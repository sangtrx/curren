from __future__ import annotations

import hashlib
import json
import sqlite3
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from curren.models import (
    IngestResult,
    LifecycleEvent,
    PublicationBatch,
    PublicationSignal,
    Signal,
    SignalList,
    Target,
    TrackRecord,
    VerificationRecord,
)

RECORD_VERSION = "signal-publication.v1"
TERMINAL_STATUSES = frozenset({"closed", "expired"})


class PublicationConflict(RuntimeError):
    pass


class SignalNotFound(LookupError):
    pass


@dataclass(frozen=True)
class AccessPolicy:
    tier: str = "public"

    @property
    def realtime(self) -> bool:
        return self.tier in {"premium", "agent"}


class ReadStore:
    """SQLite-backed, read-optimized Curren publication store.

    The private signal runtime remains the source of truth. This store accepts
    only sanitized projections, locks the original trade-plan fields on first
    publication, and keeps lifecycle events append-only.
    """

    def __init__(self, path: str | Path, *, public_delay_seconds: int = 1800) -> None:
        self.path = str(path)
        self.public_delay_seconds = max(0, int(public_delay_seconds))

    def initialize(self) -> None:
        path = Path(self.path)
        if path.parent != Path(""):
            path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as connection:
            connection.execute("PRAGMA journal_mode=WAL")
            connection.execute("PRAGMA synchronous=NORMAL")
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS signals (
                    id TEXT PRIMARY KEY,
                    symbol TEXT NOT NULL,
                    side TEXT NOT NULL,
                    status TEXT NOT NULL,
                    published_at TEXT NOT NULL,
                    public_available_at TEXT NOT NULL,
                    entry REAL,
                    stop REAL,
                    targets_json TEXT NOT NULL,
                    mark REAL,
                    current_r REAL,
                    peak_r REAL,
                    realized_r REAL,
                    closed_at TEXT,
                    exit_reason TEXT,
                    updated_at TEXT NOT NULL
                );

                CREATE INDEX IF NOT EXISTS ix_signals_status_published
                    ON signals(status, published_at DESC);
                CREATE INDEX IF NOT EXISTS ix_signals_symbol_published
                    ON signals(symbol, published_at DESC);
                CREATE INDEX IF NOT EXISTS ix_signals_closed
                    ON signals(closed_at DESC);

                CREATE TABLE IF NOT EXISTS publication_records (
                    signal_id TEXT PRIMARY KEY,
                    published_at TEXT NOT NULL,
                    content_hash TEXT NOT NULL,
                    snapshot_json TEXT NOT NULL,
                    record_version TEXT NOT NULL,
                    recorded_at TEXT NOT NULL,
                    FOREIGN KEY(signal_id) REFERENCES signals(id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS lifecycle_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    signal_id TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    event_at TEXT NOT NULL,
                    price REAL,
                    r_multiple REAL,
                    recorded_at TEXT NOT NULL,
                    UNIQUE(signal_id, event_type, event_at),
                    FOREIGN KEY(signal_id) REFERENCES signals(id) ON DELETE CASCADE
                );

                CREATE INDEX IF NOT EXISTS ix_lifecycle_signal_time
                    ON lifecycle_events(signal_id, event_at, id);
                """
            )

    def signal_count(self) -> int:
        with self._connect() as connection:
            row = connection.execute("SELECT COUNT(*) AS count FROM signals").fetchone()
        return int(row["count"] if row else 0)

    def ingest(self, batch: PublicationBatch) -> IngestResult:
        accepted = len(batch.signals)
        inserted = 0
        updated = 0
        lifecycle_inserted = 0
        now = datetime.now(UTC)

        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            try:
                for signal in batch.signals:
                    was_inserted, added_events = self._upsert_signal(connection, signal, now=now)
                    if was_inserted:
                        inserted += 1
                    else:
                        updated += 1
                    lifecycle_inserted += added_events
                connection.commit()
            except Exception:
                connection.rollback()
                raise

        return IngestResult(
            accepted=accepted,
            inserted=inserted,
            updated=updated,
            lifecycle_events_inserted=lifecycle_inserted,
        )

    def list_signals(
        self,
        *,
        status: str = "active",
        symbol: str | None = None,
        limit: int = 20,
        policy: AccessPolicy | None = None,
        now: datetime | None = None,
    ) -> SignalList:
        policy = policy or AccessPolicy()
        now = _utc(now or datetime.now(UTC))
        clauses: list[str] = []
        parameters: list[Any] = []

        normalized_status = status.strip().lower()
        if normalized_status == "active":
            clauses.append("closed_at IS NULL")
            clauses.append("LOWER(status) NOT IN ('closed', 'expired')")
        elif normalized_status in TERMINAL_STATUSES:
            clauses.append("(closed_at IS NOT NULL OR LOWER(status) = ?)")
            parameters.append(normalized_status)
        else:
            clauses.append("LOWER(status) = ?")
            parameters.append(normalized_status)

        if symbol:
            clauses.append("symbol = ?")
            parameters.append(symbol.upper())

        if not policy.realtime and normalized_status == "active":
            clauses.append("public_available_at <= ?")
            parameters.append(_iso(now))

        query = "SELECT * FROM signals"
        if clauses:
            query += " WHERE " + " AND ".join(clauses)
        query += " ORDER BY published_at DESC, id DESC LIMIT ?"
        parameters.append(limit)

        with self._connect() as connection:
            rows = connection.execute(query, parameters).fetchall()
        return SignalList(items=[self._signal_from_row(row, policy=policy) for row in rows], next_cursor=None)

    def recent_results(self, *, limit: int = 20, policy: AccessPolicy | None = None) -> SignalList:
        policy = policy or AccessPolicy()
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT * FROM signals
                WHERE closed_at IS NOT NULL OR LOWER(status) IN ('closed', 'expired')
                ORDER BY COALESCE(closed_at, published_at) DESC, id DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return SignalList(items=[self._signal_from_row(row, policy=policy) for row in rows], next_cursor=None)

    def get_signal(
        self,
        signal_id: str,
        *,
        policy: AccessPolicy | None = None,
        now: datetime | None = None,
    ) -> Signal:
        policy = policy or AccessPolicy()
        now = _utc(now or datetime.now(UTC))
        with self._connect() as connection:
            row = connection.execute("SELECT * FROM signals WHERE id = ?", (signal_id,)).fetchone()
        if row is None or not self._row_visible(row, policy=policy, now=now):
            raise SignalNotFound(signal_id)
        return self._signal_from_row(row, policy=policy)

    def lifecycle(
        self,
        signal_id: str,
        *,
        policy: AccessPolicy | None = None,
        now: datetime | None = None,
    ) -> list[LifecycleEvent]:
        policy = policy or AccessPolicy()
        now = _utc(now or datetime.now(UTC))
        signal = self.get_signal(signal_id, policy=policy, now=now)

        parameters: list[Any] = [signal_id]
        query = "SELECT * FROM lifecycle_events WHERE signal_id = ?"
        if not policy.realtime and signal.closed_at is None:
            visible_before = now - timedelta(seconds=self.public_delay_seconds)
            query += " AND event_at <= ?"
            parameters.append(_iso(visible_before))
        query += " ORDER BY event_at ASC, id ASC"

        with self._connect() as connection:
            rows = connection.execute(query, parameters).fetchall()

        reveal_prices = policy.realtime or signal.closed_at is not None
        return [
            LifecycleEvent(
                event_type=row["event_type"],
                event_at=_parse_time(row["event_at"]),
                price=row["price"] if reveal_prices else None,
                r_multiple=row["r_multiple"],
            )
            for row in rows
        ]

    def track_record(self) -> TrackRecord:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT realized_r
                FROM signals
                WHERE realized_r IS NOT NULL
                  AND (closed_at IS NOT NULL OR LOWER(status) IN ('closed', 'expired'))
                """
            ).fetchall()
        values = [float(row["realized_r"]) for row in rows]
        wins = sum(1 for value in values if value > 0)
        losses = sum(1 for value in values if value < 0)
        breakeven = sum(1 for value in values if value == 0)
        sample = len(values)
        net_r = sum(values) if values else 0.0
        return TrackRecord(
            sample_size=sample,
            wins=wins,
            losses=losses,
            breakeven=breakeven,
            win_rate=(wins / sample) if sample else None,
            net_r=net_r,
            average_r=(net_r / sample) if sample else None,
            as_of=datetime.now(UTC),
            methodology="Closed server-published signals with a recorded realized R multiple.",
        )

    def verification(
        self,
        signal_id: str,
        *,
        policy: AccessPolicy | None = None,
        now: datetime | None = None,
    ) -> VerificationRecord:
        self.get_signal(signal_id, policy=policy, now=now)
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM publication_records WHERE signal_id = ?",
                (signal_id,),
            ).fetchone()
        if row is None:
            raise SignalNotFound(signal_id)
        calculated = hashlib.sha256(row["snapshot_json"].encode("utf-8")).hexdigest()
        return VerificationRecord(
            signal_id=signal_id,
            published_at=_parse_time(row["published_at"]),
            content_hash=f"sha256:{row['content_hash']}",
            verified=calculated == row["content_hash"],
            immutable=True,
            record_version=row["record_version"],
            recorded_at=_parse_time(row["recorded_at"]),
        )

    def public_summary(self) -> dict[str, Any]:
        active = self.list_signals(status="active", limit=3, policy=AccessPolicy("public"))
        results = self.recent_results(limit=5, policy=AccessPolicy("public"))
        return {
            "active_count": self._public_active_count(),
            "delayed_signals": active.items,
            "recent_results": results.items,
            "as_of": datetime.now(UTC),
        }

    def _public_active_count(self) -> int:
        now = _iso(datetime.now(UTC))
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT COUNT(*) AS count
                FROM signals
                WHERE closed_at IS NULL
                  AND LOWER(status) NOT IN ('closed', 'expired')
                  AND public_available_at <= ?
                """,
                (now,),
            ).fetchone()
        return int(row["count"] if row else 0)

    def _upsert_signal(
        self,
        connection: sqlite3.Connection,
        signal: PublicationSignal,
        *,
        now: datetime,
    ) -> tuple[bool, int]:
        published_at = _utc(signal.published_at)
        public_available_at = _utc(
            signal.public_available_at or published_at + timedelta(seconds=self.public_delay_seconds)
        )
        immutable_json = _canonical_snapshot(signal)
        content_hash = hashlib.sha256(immutable_json.encode("utf-8")).hexdigest()
        existing_record = connection.execute(
            "SELECT content_hash FROM publication_records WHERE signal_id = ?",
            (signal.id,),
        ).fetchone()
        if existing_record is not None and existing_record["content_hash"] != content_hash:
            raise PublicationConflict(f"immutable publication fields changed for {signal.id}")

        existing_signal = connection.execute("SELECT id FROM signals WHERE id = ?", (signal.id,)).fetchone()
        targets_json = json.dumps(
            [target.model_dump(mode="json") for target in signal.targets],
            sort_keys=True,
            separators=(",", ":"),
        )
        values = (
            signal.id,
            signal.symbol.upper(),
            str(signal.side),
            signal.status,
            _iso(published_at),
            _iso(public_available_at),
            signal.entry,
            signal.stop,
            targets_json,
            signal.mark,
            signal.current_r,
            signal.peak_r,
            signal.realized_r,
            _iso(_utc(signal.closed_at)) if signal.closed_at else None,
            signal.exit_reason,
            _iso(now),
        )
        connection.execute(
            """
            INSERT INTO signals (
                id, symbol, side, status, published_at, public_available_at,
                entry, stop, targets_json, mark, current_r, peak_r, realized_r,
                closed_at, exit_reason, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                status = excluded.status,
                public_available_at = excluded.public_available_at,
                targets_json = excluded.targets_json,
                mark = excluded.mark,
                current_r = excluded.current_r,
                peak_r = excluded.peak_r,
                realized_r = excluded.realized_r,
                closed_at = excluded.closed_at,
                exit_reason = excluded.exit_reason,
                updated_at = excluded.updated_at
            """,
            values,
        )

        if existing_record is None:
            connection.execute(
                """
                INSERT INTO publication_records (
                    signal_id, published_at, content_hash, snapshot_json, record_version, recorded_at
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (signal.id, _iso(published_at), content_hash, immutable_json, RECORD_VERSION, _iso(now)),
            )

        added_events = 0
        for event in signal.lifecycle:
            cursor = connection.execute(
                """
                INSERT OR IGNORE INTO lifecycle_events (
                    signal_id, event_type, event_at, price, r_multiple, recorded_at
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    signal.id,
                    event.event_type,
                    _iso(_utc(event.event_at)),
                    event.price,
                    event.r_multiple,
                    _iso(now),
                ),
            )
            if cursor.rowcount == 1:
                added_events += 1
        return existing_signal is None, added_events

    def _signal_from_row(self, row: sqlite3.Row, *, policy: AccessPolicy) -> Signal:
        closed_at = _parse_time(row["closed_at"]) if row["closed_at"] else None
        reveal_levels = policy.realtime or closed_at is not None or row["status"].lower() in TERMINAL_STATUSES
        raw_targets = json.loads(row["targets_json"] or "[]")
        targets = [Target.model_validate(item) for item in raw_targets] if reveal_levels else []
        return Signal(
            id=row["id"],
            symbol=row["symbol"],
            side=row["side"],
            status=row["status"],
            published_at=_parse_time(row["published_at"]),
            available_at=(
                _parse_time(row["published_at"]) if policy.realtime else _parse_time(row["public_available_at"])
            ),
            entry=row["entry"] if reveal_levels else None,
            stop=row["stop"] if reveal_levels else None,
            targets=targets,
            mark=row["mark"],
            current_r=row["current_r"],
            peak_r=row["peak_r"],
            realized_r=row["realized_r"],
            closed_at=closed_at,
            exit_reason=row["exit_reason"],
            access=policy.tier,
        )

    def _row_visible(self, row: sqlite3.Row, *, policy: AccessPolicy, now: datetime) -> bool:
        if policy.realtime:
            return True
        if row["closed_at"] or row["status"].lower() in TERMINAL_STATUSES:
            return True
        return _parse_time(row["public_available_at"]) <= now

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path, timeout=5.0)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys=ON")
        connection.execute("PRAGMA busy_timeout=5000")
        return connection


def _canonical_snapshot(signal: PublicationSignal) -> str:
    payload = {
        "id": signal.id,
        "symbol": signal.symbol.upper(),
        "side": str(signal.side),
        "published_at": _iso(_utc(signal.published_at)),
        "entry": signal.entry,
        "stop": signal.stop,
        "targets": [target.price for target in signal.targets],
        "record_version": RECORD_VERSION,
    }
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        raise ValueError("timestamps must include a timezone")
    return value.astimezone(UTC)


def _iso(value: datetime) -> str:
    return _utc(value).isoformat(timespec="microseconds").replace("+00:00", "Z")


def _parse_time(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(UTC)
