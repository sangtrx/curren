"""Supabase publication bridge parity with the FastAPI reference read model.

Opt-in because it needs Docker and network access for the Edge Function's npm import:

    CURREN_SUPABASE_BRIDGE_PARITY=1 pytest -q tests/test_supabase_bridge_parity.py

The same publication batches go through the FastAPI read model and through the real Edge Function
(supabase/functions/curren-api) backed by Postgres + PostgREST with the repository migration applied.
Every step must produce the same status code, the same counts and the same conflict detail.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import shutil
import subprocess
import time
import uuid
from collections.abc import Iterator
from datetime import UTC, datetime, timedelta
from pathlib import Path

import httpx
import pytest

from curren.server import create_app

pytestmark = pytest.mark.skipif(
    os.environ.get("CURREN_SUPABASE_BRIDGE_PARITY") != "1" or shutil.which("docker") is None,
    reason="set CURREN_SUPABASE_BRIDGE_PARITY=1 with Docker available",
)

REPO = Path(__file__).resolve().parents[1]
MIGRATION = REPO / "supabase" / "migrations" / "20260927090000_publication_ingest_parity.sql"
BASELINE = REPO / "tests" / "supabase_bridge" / "baseline.sql"
POSTGRES_IMAGE = "postgres:17-alpine"
POSTGREST_IMAGE = "postgrest/postgrest:v12.2.3"
DENO_IMAGE = "denoland/deno:2.1.4"
JWT_SECRET = "curren-parity-test-jwt-secret-0123456789"
INGEST_TOKEN = "ingest-secret"
BASE = (datetime.now(UTC) - timedelta(hours=3)).replace(microsecond=0)


def _t(minutes: float) -> str:
    return (BASE + timedelta(minutes=minutes)).isoformat().replace("+00:00", "Z")


def _jwt(role: str) -> str:
    def encode(value: dict) -> str:
        raw = json.dumps(value, separators=(",", ":")).encode()
        return base64.urlsafe_b64encode(raw).rstrip(b"=").decode()

    signing_input = f"{encode({'alg': 'HS256', 'typ': 'JWT'})}.{encode({'role': role})}"
    signature = hmac.new(JWT_SECRET.encode(), signing_input.encode(), hashlib.sha256).digest()
    return f"{signing_input}.{base64.urlsafe_b64encode(signature).rstrip(b'=').decode()}"


def _docker(*args: str, stdin: bytes | None = None, check: bool = True) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(["docker", *args], input=stdin, capture_output=True, check=check, timeout=300)


class Replica:
    def __init__(self, postgres: str, url: str) -> None:
        self.postgres = postgres
        self.url = url

    def sql(self, statement: str, *, database: str = "postgres", check: bool = True) -> str:
        result = _docker(
            "exec", "-i", self.postgres,
            "psql", "-h", "127.0.0.1", "-U", "postgres", "-d", database, "-v", "ON_ERROR_STOP=1", "-tAq",
            stdin=statement.encode(),
            check=check,
        )
        return (result.stdout + result.stderr).decode().strip()


@pytest.fixture(scope="module")
def replica() -> Iterator[Replica]:
    suffix = uuid.uuid4().hex[:8]
    network = f"crn-parity-{suffix}"
    postgres = f"crn-parity-pg-{suffix}"
    postgrest = f"crn-parity-rest-{suffix}"
    function = f"crn-parity-fn-{suffix}"
    _docker("network", "create", network)
    try:
        _docker(
            "run", "-d", "--name", postgres, "--network", network, "--tmpfs", "/var/lib/postgresql/data",
            "-e", "POSTGRES_PASSWORD=postgres", POSTGRES_IMAGE, "-c", "fsync=off",
        )
        _wait(lambda: _docker("exec", postgres, "psql", "-h", "127.0.0.1", "-U", "postgres", "-tAc", "select 1", check=False).returncode == 0)
        db = Replica(postgres, "")
        db.sql(BASELINE.read_text() + MIGRATION.read_text())
        _docker(
            "run", "-d", "--name", postgrest, "--network", network,
            "-e", f"PGRST_DB_URI=postgres://authenticator:authenticator@{postgres}:5432/postgres",
            "-e", "PGRST_DB_SCHEMAS=public",
            "-e", "PGRST_DB_ANON_ROLE=anon",
            "-e", f"PGRST_JWT_SECRET={JWT_SECRET}",
            POSTGREST_IMAGE,
        )
        _docker(
            "run", "-d", "--name", function, "--network", network, "-p", "127.0.0.1::8000",
            "-v", f"{REPO}:/repo:ro",
            "-e", "SUPABASE_URL=http://127.0.0.1:3001",
            "-e", f"POSTGREST_URL=http://{postgrest}:3000",
            "-e", f"SUPABASE_SERVICE_ROLE_KEY={_jwt('service_role')}",
            DENO_IMAGE, "run", "-A", "/repo/tests/supabase_bridge/serve.ts",
        )
        port = _docker("port", function, "8000").stdout.decode().split(":")[-1].strip()
        url = f"http://127.0.0.1:{port}/functions/v1/curren-api"
        _wait(lambda: _healthy(url))
        yield Replica(postgres, url)
    finally:
        for container in (function, postgrest, postgres):
            _docker("rm", "-f", container, check=False)
        _docker("network", "rm", network, check=False)


def _wait(ready, timeout: float = 240.0) -> None:
    deadline = time.monotonic() + timeout
    while not ready():
        if time.monotonic() > deadline:
            raise TimeoutError("parity environment did not become ready")
        time.sleep(1)


def _healthy(url: str) -> bool:
    try:
        return httpx.get(f"{url}/healthz", timeout=2).status_code == 200
    except httpx.HTTPError:
        return False


def _signal(signal_id: str = "crn_sig_parity", **overrides) -> dict:
    signal = {
        "id": signal_id,
        "symbol": "ETHUSDT",
        "side": "long",
        "status": "active",
        "published_at": _t(0),
        "entry": 2500.0,
        "stop": 2450.0,
        "targets": [{"price": 2550.0}, {"price": 2600.0}],
        "mark": 2510.0,
        "current_r": 0.2,
        "peak_r": 0.3,
        "lifecycle": [{"event_type": "entry_hit", "event_at": _t(1), "price": 2500.0, "r_multiple": 0.0}],
    }
    signal.update(overrides)
    return signal


def _closed(**overrides) -> dict:
    closed = {
        "status": "closed",
        "targets": [{"price": 2550.0, "status": "hit", "hit_at": _t(20)}, {"price": 2600.0}],
        "mark": 2500.0,
        "current_r": 0.0,
        "peak_r": 1.2,
        "realized_r": 0.5,
        "closed_at": _t(60),
        "exit_reason": "stop_after_tp",
        "lifecycle": [
            {"event_type": "entry_hit", "event_at": _t(1), "price": 2500.0, "r_multiple": 0.0},
            {"event_type": "tp1_hit", "event_at": _t(20), "price": 2550.0, "r_multiple": 1.0},
            {"event_type": "sl_hit", "event_at": _t(60), "price": 2500.0, "r_multiple": 0.0},
        ],
    }
    closed.update(overrides)
    return _signal(**closed)


def _batch(generated_minutes: float, *signals: dict, source: str = "synthetic-runtime") -> dict:
    return {"source": source, "generated_at": _t(generated_minutes), "signals": list(signals)}


STEPS: list[tuple[str, dict, int]] = [
    ("insert active signal", _batch(2, _signal()), 200),
    ("replayed generated_at is stale", _batch(2, _signal(mark=2520.0)), 200),
    (
        "live update with a target hit and a new lifecycle event",
        _batch(
            21,
            _signal(
                targets=[{"price": 2550.0, "status": "hit", "hit_at": _t(20)}, {"price": 2600.0}],
                mark=2551.0,
                current_r=1.02,
                peak_r=1.05,
                lifecycle=[
                    {"event_type": "entry_hit", "event_at": _t(1), "price": 2500.0, "r_multiple": 0.0},
                    {"event_type": "tp1_hit", "event_at": _t(20), "price": 2550.0, "r_multiple": 1.0},
                ],
            ),
        ),
        200,
    ),
    ("entry cannot change", _batch(22, _signal(entry=2501.0)), 409),
    ("target prices cannot change", _batch(23, _signal(targets=[{"price": 2560.0}, {"price": 2600.0}])), 409),
    (
        "lifecycle identity cannot be rewritten",
        _batch(24, _signal(lifecycle=[{"event_type": "entry_hit", "event_at": _t(1), "price": 2499.0, "r_multiple": 0.0}])),
        409,
    ),
    ("source ownership is fixed", _batch(25, _signal(), source="other-runtime"), 409),
    ("a conflict rejects the whole batch", _batch(26, _signal("crn_sig_other"), _signal(entry=2501.0)), 409),
    ("the rejected batch wrote nothing", _batch(27, _signal("crn_sig_other")), 200),
    ("close records the outcome", _batch(61, _closed()), 200),
    (
        "identical terminal replay may add an unseen earlier lifecycle event",
        _batch(
            62,
            _closed(
                lifecycle=[
                    {"event_type": "entry_hit", "event_at": _t(1), "price": 2500.0, "r_multiple": 0.0},
                    {"event_type": "tp1_hit", "event_at": _t(20), "price": 2550.0, "r_multiple": 1.0},
                    {"event_type": "breakeven_moved", "event_at": _t(21), "price": 2500.0, "r_multiple": 0.0},
                    {"event_type": "sl_hit", "event_at": _t(60), "price": 2500.0, "r_multiple": 0.0},
                ]
            ),
        ),
        200,
    ),
    ("terminal current_r is live-only and not frozen", _batch(62.5, _closed(current_r=None)), 200),
    ("realized R cannot be rewritten", _batch(63, _closed(realized_r=0.0)), 409),
    ("closed cannot become expired", _batch(64, _closed(status="expired", realized_r=None)), 409),
    ("exit reason cannot be rewritten", _batch(65, _closed(exit_reason="stop_loss")), 409),
    ("frozen peak R cannot be rewritten", _batch(66, _closed(peak_r=1.5)), 409),
    ("frozen terminal mark cannot be rewritten", _batch(67, _closed(mark=2600.0)), 409),
    (
        "frozen target state cannot be rewritten",
        _batch(68, _closed(targets=[{"price": 2550.0, "status": "hit", "hit_at": _t(20)}, {"price": 2600.0, "status": "hit", "hit_at": _t(50)}])),
        409,
    ),
    ("terminal cannot return to active", _batch(69, _signal()), 409),
    (
        "expired needs no realized R",
        _batch(70, _signal("crn_sig_expired", status="expired", closed_at=_t(30), exit_reason="expired", lifecycle=[])),
        200,
    ),
    ("duplicate ids are rejected", _batch(71, _signal("crn_sig_dup"), _signal("crn_sig_dup")), 422),
    ("zone-less timestamps are rejected", _batch(72, _signal("crn_sig_naive", published_at=_t(0).rstrip("Z"))), 422),
    ("generated_at cannot predate the state", _batch(0.5, _signal("crn_sig_early")), 422),
    ("generated_at cannot run ahead of the server clock", _batch(60 * 24, _signal("crn_sig_future")), 422),
    ("hit targets need hit_at", _batch(73, _signal("crn_sig_x", targets=[{"price": 2550.0, "status": "hit"}])), 422),
    ("pending targets cannot carry hit_at", _batch(74, _signal("crn_sig_x", targets=[{"price": 2550.0, "hit_at": _t(5)}])), 422),
    ("targets are strict", _batch(75, _signal("crn_sig_x", targets=[{"price": 2550.0, "size": 1}])), 422),
    (
        "lifecycle events are strict",
        _batch(76, _signal("crn_sig_x", lifecycle=[{"event_type": "entry_hit", "event_at": _t(1), "note": "x"}])),
        422,
    ),
    (
        "lifecycle cannot follow the close",
        _batch(77, _signal("crn_sig_x", status="expired", closed_at=_t(5), lifecycle=[{"event_type": "late", "event_at": _t(6)}])),
        422,
    ),
    ("target hits cannot predate publication", _batch(78, _signal("crn_sig_x", published_at=_t(10), targets=[{"price": 2550.0, "status": "hit", "hit_at": _t(5)}])), 422),
    ("live rows cannot carry an exit reason", _batch(79, _signal("crn_sig_x", exit_reason="stop_loss")), 422),
    ("closed rows need realized R", _batch(80, _signal("crn_sig_x", status="closed", closed_at=_t(5))), 422),
    ("prices must be positive", _batch(81, _signal("crn_sig_x", mark=0.0)), 422),
    ("side is an exact enum", _batch(82, _signal("crn_sig_x", side="LONG")), 422),
    ("at most 16 targets", _batch(83, _signal("crn_sig_x", targets=[{"price": 2550.0 + i} for i in range(17)])), 422),
    ("impossible calendar dates are rejected", _batch(84, _signal("crn_sig_x", published_at="2026-02-30T00:00:00Z")), 422),
    ("year zero is rejected", _batch(85, _signal("crn_sig_x", published_at="0000-01-01T00:00:00Z")), 422),
    ("a batch without signals is empty", {"source": "synthetic-runtime", "generated_at": _t(86)}, 200),
]


@pytest.mark.asyncio
async def test_bridge_matches_fastapi_reference(replica: Replica, tmp_path) -> None:
    app = create_app(
        database_path=str(tmp_path / "curren.db"),
        ingest_token=INGEST_TOKEN,
        public_rate_limit=10_000,
        ingest_rate_limit=10_000,
    )
    reference = httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://reference")
    bridge = httpx.AsyncClient(base_url=replica.url, timeout=30)
    async with reference, bridge:
        for name, batch, expected in STEPS:
            expected_response = await reference.post(
                "/internal/v1/publications", json=batch, headers={"Authorization": f"Bearer {INGEST_TOKEN}"}
            )
            bridge_response = await bridge.post(
                "/internal/v1/publications", json=batch, headers={"Authorization": f"Bearer {_jwt('service_role')}"}
            )
            assert expected_response.status_code == expected, name
            assert bridge_response.status_code == expected, (name, bridge_response.text)
            if expected == 200:
                assert bridge_response.json() == expected_response.json(), name
            if expected == 409:
                assert bridge_response.json()["detail"] == expected_response.json()["detail"], name

        lifecycle = (await reference.get("/v1/signals/crn_sig_parity/lifecycle")).json()["items"]
        signal = (await reference.get("/v1/signals/crn_sig_parity")).json()

    stored_events = json.loads(
        replica.sql(
            "select coalesce(json_agg(json_build_object('event_type', event_type, 'event_at', event_at,"
            " 'price', price, 'r_multiple', r_multiple) order by event_at), '[]') from public.lifecycle_events"
            " where signal_id = 'crn_sig_parity'"
        )
    )
    assert [e["event_type"] for e in lifecycle] == ["entry_hit", "tp1_hit", "breakeven_moved", "sl_hit"]
    assert [(e["event_type"], _instant(e["event_at"]), e["price"], e["r_multiple"]) for e in stored_events] == [
        (e["event_type"], _instant(e["event_at"]), e["price"], e["r_multiple"]) for e in lifecycle
    ]
    stored = json.loads(
        replica.sql(
            "select row_to_json(s) from (select status, mark, current_r, peak_r, realized_r, closed_at, exit_reason,"
            " targets from public.signals where id = 'crn_sig_parity') s"
        )
    )
    for field in ("status", "mark", "current_r", "peak_r", "realized_r", "exit_reason"):
        assert stored[field] == signal[field], field
    assert _instant(stored["closed_at"]) == _instant(signal["closed_at"])
    assert [(t["price"], t["status"], t["hit_at"] and _instant(t["hit_at"])) for t in stored["targets"]] == [
        (t["price"], t["status"], t["hit_at"] and _instant(t["hit_at"])) for t in signal["targets"]
    ]


@pytest.mark.asyncio
async def test_rows_replicated_before_the_migration_are_locked(replica: Replica) -> None:
    # Shape the v2 bridge wrote on 2026-09-18: terminal outcome, no targets, no lifecycle rows.
    replica.sql(
        "insert into public.signals (id, source, source_generated_at, symbol, side, status, published_at,"
        " public_available_at, entry, stop, mark, current_r, peak_r, realized_r, closed_at, exit_reason)"
        f" values ('crn_sig_legacy', 'synthetic-runtime', '{_t(61)}', 'ETHUSDT', 'long', 'closed', '{_t(0)}',"
        f" '{_t(30)}', 2500.0, 2450.0, 2500.0, 0.0, 1.2, 0.5, '{_t(60)}', 'stop_after_tp')"
    )
    legacy = _closed(id="crn_sig_legacy")
    headers = {"Authorization": f"Bearer {_jwt('service_role')}"}
    async with httpx.AsyncClient(base_url=replica.url, timeout=30) as bridge:
        accepted = await bridge.post("/internal/v1/publications", json=_batch(90, legacy), headers=headers)
        corrected = await bridge.post(
            "/internal/v1/publications", json=_batch(91, {**legacy, "realized_r": 0.0}), headers=headers
        )
        reentered = await bridge.post(
            "/internal/v1/publications", json=_batch(92, {**legacy, "entry": 2490.0}), headers=headers
        )

    assert accepted.status_code == 200
    assert accepted.json()["updated"] == 1
    assert accepted.json()["outcome_records_inserted"] == 0
    assert accepted.json()["lifecycle_events_inserted"] == 3
    assert corrected.status_code == 409
    assert corrected.json()["detail"] == "immutable terminal outcome changed for crn_sig_legacy"
    assert reentered.status_code == 409
    assert reentered.json()["detail"] == "immutable publication fields changed for crn_sig_legacy"
    stored = json.loads(replica.sql("select targets from public.signals where id = 'crn_sig_legacy'"))
    assert [target["price"] for target in stored] == [2550.0, 2600.0]
    assert replica.sql("select realized_r from public.signals where id = 'crn_sig_legacy'") == "0.5"
    assert replica.sql("select current_r is null from public.signals where id = 'crn_sig_legacy'") == "t"


def test_new_objects_stay_private(replica: Replica) -> None:
    denied = (
        "select targets from public.signals",
        "select * from public.lifecycle_events",
        "select public.curren_ingest_publication('x', now(), '[]'::jsonb)",
    )
    for role in ("anon", "authenticated"):
        for statement in denied:
            output = replica.sql(f"set role {role}; {statement};", check=False)
            assert "permission denied" in output, (role, statement)
    assert replica.sql("set role anon; select count(*) >= 0 from public.signals;") == "t"
    # Append-only even for the service role; FK cascades from signals still apply.
    output = replica.sql("set role service_role; delete from public.lifecycle_events;", check=False)
    assert "permission denied" in output


def test_migration_refuses_when_anon_can_read_signal_rows(replica: Replica) -> None:
    replica.sql("create database guard_check;")
    replica.sql(
        BASELINE.read_text().replace("create role", "-- create role").replace("grant anon, authenticated", "-- grant")
        + "grant select on public.signals to anon;",
        database="guard_check",
    )
    output = replica.sql(MIGRATION.read_text(), database="guard_check", check=False)
    assert "publication ingest objects must stay private from role anon" in output
    assert replica.sql("select to_regclass('public.lifecycle_events') is null;", database="guard_check") == "t"


def _instant(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(UTC)
