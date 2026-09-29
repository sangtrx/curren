"""Synthetic handoff and real disposable-Postgres transaction regressions."""
from __future__ import annotations

import importlib.util
import json
import os
import shutil
import subprocess
import sys
import time
import uuid
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("public_rebaseline", REPO / "scripts/public_rebaseline.py")
assert spec and spec.loader
tool = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = tool
spec.loader.exec_module(tool)


def row(signal_id="synthetic_corrected", **changes):
    return {"id": signal_id, "source": "synthetic", "source_generated_at": "2026-09-01T03:00:00+00:00",
            "symbol": "ETHUSDT", "side": "long", "status": "closed",
            "published_at": "2026-09-01T00:00:00+00:00", "public_available_at": "2026-09-01T00:30:00+00:00",
            "entry": 100, "stop": 90, "mark": 130, "current_r": 0, "peak_r": 3, "realized_r": 1.75,
            "closed_at": "2026-09-01T02:00:00+00:00", "exit_reason": "tp3", "targets": None,
            "updated_at": "2026-09-01T03:00:00+00:00", **changes}


def catalog():
    body = (REPO / "supabase/migrations/20260927090000_publication_ingest_parity.sql").read_text().split("as $$", 1)[1].split("$$;", 1)[0]
    return {"triggers": [], "functions": [{"body": body}],
            "foreign_keys": [{"table": name, "delete_action": "c"} for name in sorted(tool.CHILDREN)]}


def snapshot(rows, cat=None, children=None):
    children = children or {name: [] for name in tool.CHILDREN}
    return tool.Snapshot(catalog=cat or catalog(), signals=[tool.encoded(r) for r in sorted(rows, key=lambda r: r["id"])],
                         children=children, counts={"signals": len(rows), **{k: len(v) for k, v in children.items()}})


def inputs(baseline=None, before=None):
    baseline = baseline or snapshot([row(), row("synthetic_unaffected", exit_reason="stop_loss", realized_r=-1)])
    signals = []
    for old in baseline.rows().values():
        signal = {k: v for k, v in old.items() if k in tool.FIELDS}
        signal["targets"] = [{"price": 110, "status": "hit", "hit_at": "2026-09-01T01:00:00Z"}]
        signal["current_r"] = None
        signal["lifecycle"] = [{"event_type": "entry_hit", "event_at": "2026-09-01T00:00:00Z", "price": 100, "r_multiple": 0}]
        if old["id"] == "synthetic_corrected":
            signal.update(status="active", realized_r=None, closed_at=None, exit_reason=None, current_r=3)
        signals.append(signal)
    projection = tool.PublicationBatch.model_validate({"source": "synthetic", "generated_at": "2026-09-01T04:00:00Z", "signals": signals})
    if before is None:
        before_rows = []
        for old in baseline.rows().values():
            incoming = next(s for s in projection.signals if s.id == old["id"])
            before_rows.append(old if old["id"] == "synthetic_corrected" else
                               {**old, "targets": [t.model_dump(mode="json") for t in incoming.targets], "current_r": None})
        before = snapshot(before_rows, baseline.catalog)
    receipt = {"schema": "issue462.private_correction.v1", "mode": "verify-applied", "verified": True,
               "mutation_count": 0, "source": {"revision": tool.WOODS_REVISION, "files_sha256": "d" * 64},
               "plan_sha256": "a" * 64, "affected_signal_ids": ["synthetic_corrected"],
               "cutoff": "2026-09-01T04:00:00+00:00", "mutations": []}
    receipt["receipt_sha256"] = tool.digest(receipt)
    ledger = {"version": 1, "signals": {"synthetic_corrected": {"state": "quarantined", "error_type": "PublicationTerminalConflict"}}}
    manifest = tool.Manifest(schema_version="curren.public-rebaseline.v1", woodsbot_revision=tool.WOODS_REVISION,
                             bridge_blob=tool.BRIDGE_BLOB, plan_sha256=receipt["plan_sha256"],
                             verify_applied_receipt_sha256=receipt["receipt_sha256"],
                             affected_signal_ids=receipt["affected_signal_ids"], refused_signal_ids=[],
                             baseline_sha256=tool.digest(baseline.model_dump()), before_sha256=tool.digest(before.model_dump()),
                             catalog_sha256=tool.digest(before.catalog), projection_sha256=tool.digest(projection.model_dump(mode="json")),
                             quarantine_sha256=tool.digest(ledger), checkpoint_archive_sha256="b" * 64,
                             quarantine_archive_sha256=None)
    return manifest, receipt, baseline, before, ledger, projection


def test_synthetic_plan_and_missing_manifest_cli(tmp_path):
    values = inputs()
    tool.validate_inputs(*values)
    outputs = tool.artifacts(values[0], values[3], values[5])
    assert set(outputs) == {"delete.sql", "rehearse.sql", "restore.sql", "republish.json", "plan.json"}
    assert [s["id"] for s in json.loads(outputs["republish.json"])["signals"]] == ["synthetic_corrected"]
    assert "truncate" not in outputs["delete.sql"].lower()
    assert "create function" not in outputs["delete.sql"].lower()
    result = subprocess.run([sys.executable, str(REPO / "scripts/public_rebaseline.py"), "prepare"], capture_output=True)
    assert result.returncode == 2 and not list(tmp_path.iterdir())


@pytest.mark.parametrize("change", ["plan", "receipt", "ids", "quarantine", "projection_error", "catalog", "immutable", "child", "count"])
def test_manifest_binding_and_drift_refused(change):
    manifest, receipt, baseline, before, ledger, projection = inputs()
    if change == "plan":
        manifest.plan_sha256 = "f" * 64
    elif change == "receipt":
        receipt["verified"] = False
    elif change == "ids":
        manifest.affected_signal_ids = ["synthetic_unaffected"]
    elif change == "quarantine":
        ledger["signals"] = {}
        manifest.quarantine_sha256 = tool.digest(ledger)
    elif change == "projection_error":
        ledger["signals"]["synthetic_corrected"]["error_type"] = "ProjectionError"
        manifest.quarantine_sha256 = tool.digest(ledger)
    elif change == "catalog":
        before.catalog["triggers"] = ["unexpected trigger"]
    elif change == "immutable":
        changed = json.loads(before.signals[0])
        changed["entry"] = 101
        before.signals[0] = tool.encoded(changed)
    elif change == "child":
        before.children["lifecycle_events"].append(tool.encoded({"signal_id": "synthetic_corrected"}))
        before.counts["lifecycle_events"] = 1
    else:
        before.counts["signals"] += 1
    manifest.before_sha256 = tool.digest(before.model_dump())
    with pytest.raises(ValueError):
        tool.validate_inputs(manifest, receipt, baseline, before, ledger, projection)


def test_strict_allowlist_and_duplicate_json(tmp_path):
    raw = inputs()[0].model_dump()
    for ids in ([], ["synthetic_corrected"] * 2, ["z", "a"], ["x'); delete from signals; --"]):
        with pytest.raises(ValueError):
            tool.Manifest.model_validate({**raw, "affected_signal_ids": ids})
    path = tmp_path / "duplicate.json"
    path.write_text('{"id": 1, "id": 2}')
    with pytest.raises(ValueError, match="duplicate"):
        tool.read(path)


class Database:
    def __init__(self, container):
        self.container = container

    def sql(self, sql, check=True):
        result = subprocess.run(["docker", "exec", "-i", self.container, "psql", "-h", "127.0.0.1", "-U", "postgres", "-X", "-qAt", "-v", "ON_ERROR_STOP=1"],
                                input=sql, text=True, capture_output=True, timeout=30)
        if check and result.returncode:
            raise AssertionError(result.stderr)
        return result

    def capture(self):
        return tool.Snapshot.model_validate_json(self.sql("set time zone 'UTC';" + tool.CAPTURE + ";").stdout)


@pytest.fixture(scope="module")
def database():
    if os.environ.get("CURREN_REBASELINE_POSTGRES") != "1" or not shutil.which("docker"):
        pytest.skip("set CURREN_REBASELINE_POSTGRES=1 for disposable PostgreSQL checks")
    name = "curren-rebaseline-test-" + uuid.uuid4().hex[:10]
    subprocess.run(["docker", "run", "-d", "--name", name, "--network", "none", "--memory", "256m", "--cpus", "1",
                    "--tmpfs", "/var/lib/postgresql/data", "-e", "POSTGRES_HOST_AUTH_METHOD=trust", "postgres:17-alpine"],
                   check=True, capture_output=True, timeout=60)
    db = Database(name)
    try:
        for _ in range(60):
            if db.sql("select 1", check=False).returncode == 0:
                break
            time.sleep(0.25)
        db.sql((REPO / "tests/supabase_bridge/baseline.sql").read_text() +
               "create table signal_targets(id bigint primary key, signal_id text references signals(id) on delete cascade);" +
               "create table signal_lifecycle(id bigint primary key, signal_id text references signals(id) on delete cascade);" +
               (REPO / "supabase/migrations/20260927090000_publication_ingest_parity.sql").read_text())
        yield db
    finally:
        subprocess.run(["docker", "rm", "-f", name], check=True, capture_output=True, timeout=300)


@pytest.fixture
def prepared(database):
    db = database
    db.sql("delete from public.signals;")
    initial = [row(), row("synthetic_unaffected", exit_reason="stop_loss", realized_r=-1)]
    db.sql("insert into signals select * from jsonb_populate_recordset(null::signals," + tool.literal(initial) + ");")
    baseline = db.capture()
    values = inputs(baseline=baseline)
    # Reproduce accepted run #1 on the unaffected row only; the corrected terminal row remains frozen.
    unaffected = [s.model_dump(mode="json") for s in values[-1].signals if s.id == "synthetic_unaffected"]
    db.sql("select curren_ingest_publication('synthetic', '2026-09-01T04:00:00Z'," + tool.literal(unaffected) + ");")
    values = inputs(baseline=baseline, before=db.capture())
    tool.validate_inputs(*values)
    return db, values, tool.artifacts(values[0], values[3], values[5])


def test_postgres_delete_rollback_restore_and_rerun(prepared):
    db, values, outputs = prepared
    before = values[3]
    db.sql(outputs["rehearse.sql"])
    assert db.capture() == before
    db.sql(outputs["delete.sql"])
    assert set(db.capture().rows()) == {"synthetic_unaffected"}
    assert db.sql(outputs["delete.sql"], check=False).returncode != 0
    db.sql(outputs["restore.sql"])
    assert db.capture() == before
    assert db.sql(outputs["restore.sql"], check=False).returncode != 0


def test_postgres_failure_after_delete_rolls_back(prepared):
    db, values, _ = prepared
    before = values[3]
    wrong_after = tool.remaining(before, values[0].affected_signal_ids)
    wrong_after.counts["signals"] += 1
    sql = tool.transaction(before, wrong_after, "delete from signals where id='synthetic_corrected';", 1, values[0].plan_sha256)
    assert db.sql(sql, check=False).returncode != 0
    assert db.capture() == before


def test_cli_review_hash_and_output_refusal(prepared, tmp_path):
    _, values, _ = prepared
    manifest, receipt, baseline, before, ledger, projection = values
    files = {"manifest": manifest.model_dump(), "private-receipt": receipt,
             "baseline": baseline.model_dump(), "before": before.model_dump(),
             "quarantine": ledger, "projection": projection.model_dump(mode="json")}
    args = [sys.executable, str(REPO / "scripts/public_rebaseline.py"), "prepare"]
    for name, value in files.items():
        path = tmp_path / (name + ".json")
        path.write_text(tool.encoded(value))
        args.extend(["--" + name, str(path)])
    out = tmp_path / "result"
    args.extend(["--out", str(out), "--expect-manifest-sha256", tool.digest(manifest.model_dump())])
    assert subprocess.run([*args[:-1], "0" * 64], capture_output=True).returncode == 2
    assert not out.exists()
    assert subprocess.run(args, capture_output=True).returncode == 0
    assert (out / "delete.sql").stat().st_mode & 0o777 == 0o600
    assert subprocess.run(args, capture_output=True).returncode == 2


def test_postgres_writer_lock_refused(prepared):
    db, values, outputs = prepared
    proc = subprocess.Popen(["docker", "exec", "-i", db.container, "psql", "-h", "127.0.0.1", "-U", "postgres", "-qAt"],
                            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    assert proc.stdin is not None
    try:
        proc.stdin.write("set application_name='synthetic-lock'; begin; lock table signals in row exclusive mode; select pg_sleep(20); rollback;\n")
        proc.stdin.flush()
        for _ in range(40):
            if db.sql("select count(*) from pg_stat_activity where application_name='synthetic-lock' and wait_event='PgSleep';").stdout.strip() == "1":
                break
            time.sleep(0.1)
        else:
            pytest.fail("test lock not acquired")
        result = db.sql(outputs["delete.sql"], check=False)
        assert result.returncode != 0 and "lock" in result.stderr
        assert db.capture() == values[3]
    finally:
        db.sql("select pg_terminate_backend(pid) from pg_stat_activity where application_name='synthetic-lock';")
        proc.communicate(timeout=10)


@pytest.mark.parametrize("drift", ["row", "remaining", "child", "legacy", "column", "fk", "trigger", "function"])
def test_postgres_drift_rolls_back(prepared, drift):
    db, _, outputs = prepared
    changes = {
        "row": "update signals set entry=101 where id='synthetic_corrected';",
        "remaining": "update signals set peak_r=4 where id='synthetic_unaffected';",
        "child": "insert into lifecycle_events(signal_id,event_type,event_at) values ('synthetic_corrected','entry_hit',now());",
        "legacy": "insert into signal_targets values (1,'synthetic_corrected');",
        "column": "alter table signals add column unexpected text;",
        "fk": "create table unexpected_fk(signal_id text references signals(id) on delete cascade);",
        "trigger": "create function unexpected_trigger() returns trigger language plpgsql as 'begin return OLD; end'; create trigger unexpected before delete on signals for each row execute function unexpected_trigger();",
        "function": "comment on function curren_ingest_publication(text,timestamptz,jsonb) is 'not source drift'; alter function curren_ingest_publication(text,timestamptz,jsonb) security definer;",
    }
    cleanup = {"column": "alter table signals drop column unexpected;",
               "fk": "drop table unexpected_fk;",
               "trigger": "drop trigger unexpected on signals; drop function unexpected_trigger();",
               "function": "alter function curren_ingest_publication(text,timestamptz,jsonb) security invoker;"}
    try:
        db.sql(changes[drift])
        drifted = db.capture()
        assert db.sql(outputs["delete.sql"], check=False).returncode != 0
        assert db.capture() == drifted
    finally:
        if drift in cleanup:
            db.sql(cleanup[drift])


def test_postgres_republish_and_public_api_parity(prepared):
    db, values, outputs = prepared
    manifest, _, _, before, _, projection = values
    db.sql(outputs["delete.sql"])
    retry = json.loads(outputs["republish.json"])
    db.sql("select curren_ingest_publication('synthetic','2026-09-01T04:00:00Z'," + tool.literal(retry["signals"]) + ");")
    after = db.capture()
    assert db.sql(outputs["delete.sql"], check=False).returncode != 0
    assert db.sql(outputs["restore.sql"], check=False).returncode != 0
    assert db.capture() == after
    run = {"candidates": 1, "projected": 1, "published": 1, "stale_ignored": 0}
    public = {"observed_at": "2026-09-01T04:02:00Z", "live_signals": [], "feed_status": "stale",
              "recent_results": [{k: v for k, v in r.items() if k in ("id", "status", "realized_r", "closed_at", "exit_reason")}
                                 for r in after.rows().values() if r["status"] == "closed"]}
    ledger = {"version": 1, "signals": {"synthetic_corrected": {"state": "resolved"}}}
    assert tool.verify(manifest, before, after, projection, ledger, run, public)["verified"]
    for bad_run in ({**run, "published": 0}, {**run, "stale_ignored": 1}):
        with pytest.raises(ValueError):
            tool.verify(manifest, before, after, projection, ledger, bad_run, public)
    public["recent_results"][0]["entry"] = 100
    with pytest.raises(ValueError, match="boundary"):
        tool.verify(manifest, before, after, projection, ledger, run, public)
