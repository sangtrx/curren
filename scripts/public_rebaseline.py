"""Offline, exact-manifest public rebaseline artifacts. No network or database client.

Operator evidence stays outside Git. SQL is for a separately authorized operator;
this program only writes new local files. See docs/PUBLIC_REBASELINE.md.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from collections import Counter
from datetime import UTC, datetime, timedelta
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from curren.models import PublicationBatch, normalize_signal_id
from curren.store import AccessPolicy, ReadStore

ROOT = Path(__file__).resolve().parents[1]
CAPTURE = (ROOT / "scripts/rebaseline_capture.sql").read_text().strip().removesuffix(";")
WOODS_REVISION = "5f09a4be9fa9c8a2170026bddc12e53bababa911"
BRIDGE_BLOB = "b5f02d7489c72a097462649c8f81fa9ab5833443"
CHILDREN = {"lifecycle_events", "signal_targets", "signal_lifecycle"}
SHA = Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")]
IDENTITY = ("id", "symbol", "side", "published_at", "public_available_at", "entry", "stop")
FIELDS = (*IDENTITY, "status", "mark", "current_r", "peak_r", "realized_r", "closed_at", "exit_reason", "targets")


class Refusal(ValueError):
    """A safe diagnostic code, with no operator evidence included."""


def require(ok: object, message: str) -> None:
    if not ok:
        raise Refusal(message)


def encoded(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)


def digest(value: Any) -> str:
    return hashlib.sha256(encoded(value).encode()).hexdigest()


def read(path: Path) -> Any:
    def unique(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            require(key not in result, "duplicate JSON key")
            result[key] = value
        return result

    return json.loads(path.read_text(), object_pairs_hook=unique,
                      parse_constant=lambda _: (_ for _ in ()).throw(ValueError("nonfinite JSON")))


class Strict(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class Manifest(Strict):
    schema_version: Literal["curren.public-rebaseline.v1"]
    woodsbot_revision: Literal["5f09a4be9fa9c8a2170026bddc12e53bababa911"]
    bridge_blob: Literal["b5f02d7489c72a097462649c8f81fa9ab5833443"]
    plan_sha256: SHA
    verify_applied_receipt_sha256: SHA
    affected_signal_ids: list[str] = Field(min_length=1)
    refused_signal_ids: list[str]
    baseline_sha256: SHA
    before_sha256: SHA
    catalog_sha256: SHA
    projection_sha256: SHA
    quarantine_sha256: SHA
    checkpoint_archive_sha256: SHA
    quarantine_archive_sha256: SHA | None  # null only for proved absence before run #1

    @model_validator(mode="after")
    def exact_ids(self) -> Manifest:
        for ids in (self.affected_signal_ids, self.refused_signal_ids):
            require(ids == sorted(set(ids)), "IDs must be sorted and unique")
            require(all(normalize_signal_id(i) == i for i in ids), "invalid signal ID")
        require(not set(self.affected_signal_ids) & set(self.refused_signal_ids), "overlapping ID lists")
        return self


class Snapshot(Strict):
    catalog: dict[str, Any]
    signals: list[str]
    children: dict[str, list[str]]
    counts: dict[str, int]

    def rows(self) -> dict[str, dict[str, Any]]:
        rows = [json.loads(row) for row in self.signals]
        result = {row["id"]: row for row in rows}
        require(len(result) == len(rows), "duplicate captured ID")
        require(set(self.children) == CHILDREN, "child table contract changed")
        require(self.counts == {"signals": len(rows), **{k: len(v) for k, v in self.children.items()}},
                "capture counts changed")
        return result


def quarantine_ids(ledger: dict[str, Any]) -> list[str]:
    require(set(ledger) == {"version", "signals"} and ledger["version"] == 1, "quarantine schema changed")
    require(isinstance(ledger["signals"], dict), "invalid quarantine entries")
    active = []
    for signal_id, entry in ledger["signals"].items():
        require(normalize_signal_id(signal_id) == signal_id, "invalid quarantine ID")
        require(entry.get("state") in ("quarantined", "resolved"), "invalid quarantine state")
        if entry["state"] == "quarantined":
            # Projection failures are not proof of an immutable-record conflict.
            require(entry.get("error_type") == "PublicationTerminalConflict", "non-frozen quarantine entry")
            active.append(signal_id)
    return sorted(active)


def row_value(value: Any, key: str) -> Any:
    if value is not None and (key.endswith("_at")):
        timestamp = datetime.fromisoformat(value.replace("Z", "+00:00"))
        require(timestamp.tzinfo is not None, "timezone required in evidence")
        return timestamp.astimezone(UTC)
    if key == "targets" and value is not None:
        return [{**t, "hit_at": row_value(t.get("hit_at"), "hit_at")} for t in value]
    return value


def equal_fields(left: dict[str, Any], right: dict[str, Any], fields: Any) -> bool:
    return all(row_value(left.get(k), k) == row_value(right.get(k), k) for k in fields)


def check_catalog(snapshot: Snapshot, expected_hash: str) -> None:
    require(digest(snapshot.catalog) == expected_hash, "catalog drift")
    require(snapshot.catalog.get("triggers") == [], "unexpected non-internal trigger")
    fks = snapshot.catalog.get("foreign_keys", [])
    require({f["table"].removeprefix("public.") for f in fks} == CHILDREN
            and len(fks) == len(CHILDREN)
            and all(f["delete_action"] == "c" for f in fks), "unexpected referencing foreign key")
    migration = (ROOT / "supabase/migrations/20260927090000_publication_ingest_parity.sql").read_text()
    body = migration.split("as $$", 1)[1].split("$$;", 1)[0]
    functions = snapshot.catalog.get("functions", [])
    require(len(functions) == 1 and functions[0]["body"] == body, "ingest function source drift")
    require(not snapshot.children["signal_targets"] and not snapshot.children["signal_lifecycle"],
            "legacy child rows exist")


def validate_inputs(manifest: Manifest, receipt: dict[str, Any], baseline: Snapshot,
                    before: Snapshot, ledger: dict[str, Any], projection: PublicationBatch) -> None:
    require(digest(baseline.model_dump()) == manifest.baseline_sha256, "baseline hash mismatch")
    require(digest(before.model_dump()) == manifest.before_sha256, "before hash mismatch")
    require(digest(projection.model_dump(mode="json")) == manifest.projection_sha256, "projection hash mismatch")
    require(digest(ledger) == manifest.quarantine_sha256, "quarantine hash mismatch")
    unsigned = {k: v for k, v in receipt.items() if k != "receipt_sha256"}
    require(digest(unsigned) == receipt.get("receipt_sha256") == manifest.verify_applied_receipt_sha256,
            "private verify receipt hash mismatch")
    require(receipt.get("schema") == "issue462.private_correction.v1"
            and receipt.get("mode") == "verify-applied" and receipt.get("verified") is True
            and receipt.get("mutation_count") == 0, "private verify-applied receipt required")
    require(receipt.get("source", {}).get("revision") == manifest.woodsbot_revision
            and receipt.get("plan_sha256") == manifest.plan_sha256
            and receipt.get("affected_signal_ids") == manifest.affected_signal_ids, "private handoff mismatch")
    require(projection.generated_at >= row_value(receipt["cutoff"], "cutoff_at"), "projection predates private cutoff")
    require(quarantine_ids(ledger) == manifest.affected_signal_ids, "quarantine must equal applied IDs")
    for snapshot in (baseline, before):
        snapshot.rows()
        check_catalog(snapshot, manifest.catalog_sha256)
    old, rows = baseline.rows(), before.rows()
    projected = {s.id: s.model_dump(mode="json") for s in projection.signals}
    require(set(rows) == set(projected) and set(old) <= set(rows), "projection population mismatch")
    require(set(manifest.affected_signal_ids) <= set(old), "affected IDs absent from baseline")
    require(set(manifest.refused_signal_ids) <= set(old), "refused IDs absent from baseline")
    require(not baseline.children["lifecycle_events"], "baseline lifecycle rows exist")
    require(all(r["targets"] is None for r in old.values()), "baseline targets already populated")
    for signal_id, row in old.items():
        require(row["source"] == projection.source, "publication source mismatch")
        incoming = projected[signal_id]
        require(equal_fields(row, incoming, IDENTITY), "immutable publication identity drift")
        require(row_value(row["public_available_at"], "public_available_at") >=
                row_value(row["published_at"], "published_at") + timedelta(seconds=1800),
                "availability would change on reinsert")
        if signal_id in manifest.affected_signal_ids:
            require(next(r for r in baseline.signals if json.loads(r)["id"] == signal_id) ==
                    next(r for r in before.signals if json.loads(r)["id"] == signal_id)
                    and row["status"] in ("closed", "expired"), "affected before row drift")
            require(not equal_fields(row, incoming, ("status", "realized_r", "closed_at", "exit_reason", "mark", "peak_r")),
                    "affected row has no frozen correction")
        else:
            # Run #1 can enrich old terminal rows but cannot rewrite any frozen visible field.
            fields = set(row) - {"source_generated_at", "updated_at", "targets", "current_r"}
            if row["status"] in ("pending", "active"):
                fields = set(IDENTITY) | {"source"}
            require(equal_fields(row, rows[signal_id], fields), "unaffected frozen row drift")
    for signal_id in set(rows) - set(manifest.affected_signal_ids):
        expected = dict(projected[signal_id])
        if expected["status"] in ("closed", "expired"):
            expected["current_r"] = None
        require(equal_fields(rows[signal_id], expected, FIELDS), "run #1 projection mismatch")
        require(rows[signal_id]["source"] == projection.source, "run #1 source mismatch")
    require(not any(json.loads(e)["signal_id"] in manifest.affected_signal_ids
                    for e in before.children["lifecycle_events"]), "affected lifecycle rows exist")
    legacy = sorted(i for i, r in projected.items() if r["exit_reason"] in ("tp3", "expired"))
    require(legacy == manifest.refused_signal_ids, "residual legacy IDs differ from refused list")


def literal(value: Any) -> str:
    return "'" + encoded(value).replace("'", "''") + "'::jsonb"


def remaining(before: Snapshot, ids: list[str]) -> Snapshot:
    result = before.model_copy(deep=True)
    result.signals = [r for r in before.signals if json.loads(r)["id"] not in ids]
    result.counts["signals"] -= len(ids)
    return result


def transaction(before: Snapshot, after: Snapshot, statement: str, count: int, plan_hash: str,
                *, rollback: bool = False) -> str:
    # Compare the entire captured state under locks, including every child row and the catalog.
    # No temporary table, DDL, function installation, RPC or privilege change is needed.
    sql = f"""\\set ON_ERROR_STOP on
set standard_conforming_strings = on;
begin;
set local time zone 'UTC';
set local lock_timeout = '2s';
lock table public.signals, public.lifecycle_events, public.signal_targets,
  public.signal_lifecycle in share row exclusive mode nowait;
do $rebaseline$
declare actual jsonb; changed integer;
begin
  actual := ({CAPTURE});
  if actual is distinct from {literal(before.model_dump())} then
    raise exception 'rebaseline before state/catalog drift or rerun';
  end if;
  {statement}
  get diagnostics changed = row_count;
  if changed <> {count} then raise exception 'rebaseline row count mismatch'; end if;
  actual := ({CAPTURE});
  if actual is distinct from {literal(after.model_dump())} then
    raise exception 'rebaseline after state/catalog drift';
  end if;
end;
$rebaseline$;
{'rollback' if rollback else 'commit'};
select {literal({'plan_sha256': plan_hash, 'changed': count, 'committed': not rollback,
                'before_sha256': digest(before.model_dump()), 'after_sha256': digest(after.model_dump())})};
"""
    # Dollar-quote delimiters are SQL syntax even inside embedded JSON strings.
    # Derive a delimiter absent from the body rather than trusting row/catalog text.
    tag = "$rebaseline_" + hashlib.sha256(sql.encode()).hexdigest() + "$"
    require(tag not in sql, "SQL delimiter collision")
    return sql.replace("do $rebaseline$", "do " + tag, 1).replace("\n$rebaseline$;", "\n" + tag + ";", 1)


def artifacts(manifest: Manifest, before: Snapshot, projection: PublicationBatch) -> dict[str, str]:
    ids = manifest.affected_signal_ids
    after = remaining(before, ids)
    delete = f"delete from public.signals where id in (select jsonb_array_elements_text({literal(ids)}));"
    # Original JSON text is used, so numeric precision and all recorded columns survive rollback.
    raw_rows = "[" + ",".join(row for row in before.signals if json.loads(row)["id"] in ids) + "]"
    insert = ("insert into public.signals select * from jsonb_populate_recordset(null::public.signals, "
              + "'" + raw_rows.replace("'", "''") + "'::jsonb);")
    retry = projection.model_copy(update={"signals": [s for s in projection.signals if s.id in ids]})
    plan = {
        "manifest_sha256": digest(manifest.model_dump()), "private_plan_sha256": manifest.plan_sha256,
        "affected_signal_ids": ids, "refused_signal_ids": manifest.refused_signal_ids,
        "before_counts": before.counts, "after_delete_counts": after.counts,
        "before_status_counts": dict(Counter(r["status"] for r in before.rows().values())),
        "before_exit_reason_counts": dict(Counter(str(r["exit_reason"]) for r in before.rows().values())),
        "before_row_sha256": {json.loads(r)["id"]: hashlib.sha256(r.encode()).hexdigest() for r in before.signals},
        "remaining_sha256": digest(after.model_dump()),
        "checkpoint_reset": {"owner": "private operator", "before_run_1_only": True,
                             "archive_checkpoint_sha256": manifest.checkpoint_archive_sha256,
                             "archive_quarantine_sha256": manifest.quarantine_archive_sha256,
                             "require_both_paths_absent": True, "reset_before_run_2": False},
        "publication_once": {"run_2_retry_ids": ids, "require_trading_held": True,
                             "require_persistent_publisher_disabled": True,
                             "require_no_publisher_daemon": True},
        "rollback": "restore.sql only before any successful run #2 insertion; otherwise stop and recapture",
    }
    require(len(before.signals) - len(after.signals) == len(ids), "missing before rows")
    return {"delete.sql": transaction(before, after, delete, len(ids), manifest.plan_sha256),
            "rehearse.sql": transaction(before, after, delete, len(ids), manifest.plan_sha256, rollback=True),
            "restore.sql": transaction(after, before, insert, len(ids), manifest.plan_sha256),
            "plan.json": encoded(plan) + "\n", "republish.json": retry.model_dump_json(indent=2) + "\n"}


def verify(manifest: Manifest, before: Snapshot, after: Snapshot, projection: PublicationBatch,
           ledger: dict[str, Any], run: dict[str, Any], public: dict[str, Any]) -> dict[str, Any]:
    require(digest(before.model_dump()) == manifest.before_sha256, "before hash mismatch")
    require(digest(projection.model_dump(mode="json")) == manifest.projection_sha256, "projection hash mismatch")
    rows = after.rows()
    original_rows = before.rows()
    check_catalog(after, manifest.catalog_sha256)
    require(not quarantine_ids(ledger), "active quarantine remains")
    require(run["candidates"] == run["projected"] == run["published"] >= len(manifest.affected_signal_ids)
            and run["stale_ignored"] == 0, "incomplete publisher cycle")
    require(set(rows) == {s.id for s in projection.signals}, "post-publication ID mismatch")
    for signal in projection.signals:
        expected = signal.model_dump(mode="json")
        if signal.status in ("closed", "expired"):
            expected["current_r"] = None
        require(equal_fields(rows[signal.id], expected, FIELDS), "post-publication row mismatch")
        require(rows[signal.id]["source"] == projection.source, "post-publication source mismatch")
        require(row_value(rows[signal.id]["source_generated_at"], "source_generated_at") >= projection.generated_at,
                "post-publication stale watermark")
        if signal.id not in manifest.affected_signal_ids:
            original = original_rows[signal.id]
            require(equal_fields(original, rows[signal.id], set(original) - {"source_generated_at", "updated_at"}),
                    "post-publication unaffected row drift")
        events = [json.loads(e) for e in after.children["lifecycle_events"] if json.loads(e)["signal_id"] == signal.id]
        actual = sorted([{k: row_value(e[k], k) for k in ("event_type", "event_at", "price", "r_multiple")}
                         for e in events], key=lambda e: (e["event_at"], e["event_type"]))
        wanted = sorted([{k: row_value(v, k) for k, v in e.items()} for e in expected["lifecycle"]],
                        key=lambda e: (e["event_at"], e["event_type"]))
        require(actual == wanted, "post-publication lifecycle mismatch")
    require(all(json.loads(e)["signal_id"] in rows for e in after.children["lifecycle_events"]),
            "orphan lifecycle row")
    require(sorted(i for i, r in rows.items() if r["exit_reason"] in ("tp3", "expired")) ==
            manifest.refused_signal_ids, "legacy residual mismatch")
    # Public captures must be complete, unpaginated results, taken after the 90-second window.
    observed = row_value(public["observed_at"], "observed_at")
    require(all(observed > row_value(r["source_generated_at"], "source_generated_at") + timedelta(seconds=90)
                for r in rows.values()), "public freshness observation too early")
    delayed_active = any(r["status"] == "active" and
                         row_value(r["public_available_at"], "public_available_at") <= observed for r in rows.values())
    require(public["live_signals"] == [] and public["feed_status"] == ("stale" if delayed_active else "idle"),
            "false live-feed claim")
    results = public["recent_results"]
    require(len(results) == len({r["id"] for r in results}) and
            {r["id"] for r in results} == {i for i, r in rows.items() if r["status"] == "closed"},
            "landing result IDs mismatch")
    safe = {"id", "symbol", "side", "status", "published_at", "public_available_at", "mark", "current_r",
            "peak_r", "realized_r", "closed_at", "exit_reason", "source_generated_at", "updated_at"}
    for row in results:
        require(set(row) <= safe and {"id", "status", "realized_r", "closed_at", "exit_reason"} <= set(row),
                "public field boundary mismatch")
        require(equal_fields(row, rows[row["id"]], row), "landing result mismatch")
    # Exercise the canonical API read model locally; no API hostname or credentials are consulted.
    with TemporaryDirectory(prefix="curren-parity-") as directory:
        store = ReadStore(Path(directory) / "reference.sqlite")
        store.initialize()
        store.ingest(projection)
        for signal_id, row in rows.items():
            api = store.get_signal(signal_id, policy=AccessPolicy("agent"), now=observed).model_dump(mode="json")
            require(equal_fields(api, row, set(FIELDS) - {"public_available_at"}), "local API parity mismatch")
            if row["status"] in ("closed", "expired") or observed >= row_value(row["public_available_at"], "public_available_at"):
                public_api = store.get_signal(signal_id, now=observed).model_dump(mode="json")
                require(row_value(public_api["available_at"], "available_at") == row_value(row["public_available_at"], "public_available_at"),
                        "local API availability mismatch")
    return {"verified": True, "plan_sha256": manifest.plan_sha256,
            "snapshot_sha256": digest(after.model_dump()), "counts": after.counts,
            "status_counts": dict(Counter(r["status"] for r in rows.values())),
            "exit_reason_counts": dict(Counter(str(r["exit_reason"]) for r in rows.values())),
            "public_results": len(results), "api_parity": "local ReadStore passed; no live API asserted"}


def write_new(path: Path, value: str) -> None:
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "w") as stream:
        stream.write(value)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    capture = commands.add_parser("capture-sql")
    capture.add_argument("--out", type=Path, required=True)
    commands.add_parser("manifest-schema")
    hash_command = commands.add_parser("hash")
    hash_command.add_argument("file", type=Path)
    hash_command.add_argument("--publication", action="store_true")
    for name in ("prepare", "verify"):
        cmd = commands.add_parser(name)
        for arg in ("manifest", "before", "projection", "quarantine", "out"):
            cmd.add_argument(f"--{arg}", type=Path, required=True)
        cmd.add_argument("--expect-manifest-sha256", required=True)
        if name == "prepare":
            cmd.add_argument("--private-receipt", type=Path, required=True)
            cmd.add_argument("--baseline", type=Path, required=True)
        else:
            for arg in ("after", "run", "public"):
                cmd.add_argument(f"--{arg}", type=Path, required=True)
    args = parser.parse_args()
    try:
        if args.command == "capture-sql":
            write_new(args.out, "begin isolation level repeatable read read only;\nset local time zone 'UTC';\n" + CAPTURE + ";\ncommit;\n")
        elif args.command == "manifest-schema":
            print(json.dumps(Manifest.model_json_schema(), indent=2))
        elif args.command == "hash":
            value = read(args.file)
            if args.publication:
                value = PublicationBatch.model_validate(value).model_dump(mode="json")
            print(digest(value))
        else:
            raw = read(args.manifest)
            require(digest(raw) == args.expect_manifest_sha256, "reviewed manifest hash mismatch")
            manifest = Manifest.model_validate(raw)
            before = Snapshot.model_validate(read(args.before))
            projection = PublicationBatch.model_validate(read(args.projection))
            ledger = read(args.quarantine)
            if args.command == "prepare":
                baseline = Snapshot.model_validate(read(args.baseline))
                validate_inputs(manifest, read(args.private_receipt), baseline, before, ledger, projection)
                outputs = artifacts(manifest, before, projection)
                args.out.mkdir(mode=0o700)  # Refuse output-directory reuse/reruns.
                for name, value in outputs.items():
                    write_new(args.out / name, value)
            else:
                result = verify(manifest, before, Snapshot.model_validate(read(args.after)), projection,
                                ledger, read(args.run), read(args.public))
                write_new(args.out, encoded(result) + "\n")
    except Refusal as exc:
        print(f"rebaseline refused: {exc}", file=sys.stderr)
        return 2
    except (ValueError, OSError, KeyError, TypeError) as exc:
        print(f"rebaseline refused: {type(exc).__name__}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
