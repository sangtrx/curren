# Offline public rebaseline operator tool

`scripts/public_rebaseline.py` prepares private operator artifacts for the one-time public
correction. It opens no database connection, reads no environment credentials, sends no HTTP
requests, and executes no publication or SQL. Normal ingestion remains immutable. Generated SQL
contains no DDL, TRUNCATE, privilege changes, SECURITY DEFINER or persistent RPC.

The accepted private correction source is WoodsBot main
`5f09a4be9fa9c8a2170026bddc12e53bababa911` (PR43). That source merge does **not** prove a production
apply. A real reviewed manifest and a matching `verify-applied` receipt are runtime preconditions.
Never use an old snapshot, a terminal-status query or the historical 41-candidate universe to
choose IDs. Only the exact sorted `affected_signal_ids` from the private apply receipt can be deleted.

All manifests, captures, receipts, ID lists and generated SQL stay in a private operator evidence
directory outside this public repository. The checked-in tests use synthetic IDs only.

## Evidence and order

1. The private operator proves accepted source, stopped workers/trading, disabled persistent
   publication, fresh backup/restore/off-host proof, reviewed frozen private plan, rehearsal,
   private apply and `verify-applied`. Preserve the original receipt. Do not copy the private
   database or raw messages into this repository. Avoid concurrent maintenance/compaction.
2. Capture the public baseline and catalog with the read-only query below. Review column types,
   FK actions, privileges/RLS/security-invoker views, and the deployed Edge Function blob
   `b5f02d7489c72a097462649c8f81fa9ab5833443`. The ingest body must match the checked-in migration.
   The tool requires the three known referencing child tables with CASCADE, no custom triggers,
   empty legacy children, no baseline lifecycle rows, and NULL baseline targets. Any difference
   requires investigation and a new reviewed contract; do not relax checks during execution.
3. On the **private host**, archive the checkpoint and its adjacent quarantine ledger without
   editing their contents. Record file SHA-256 hashes and prove both original paths absent.
   A nonexistent old quarantine ledger is recorded explicitly as `null`, never fabricated.
   The checkpoint is a row-ID high-water mark; PR43 updates some rows in place, so resetting it
   is mandatory. This tool encodes the reset plan but does not perform host file operations.
4. Restore the private operator's reviewed `trading-held` runtime state before the existing
   `publication-once` action. Keep persistent `CURREN_PUBLICATION_ENABLED=false`, trading held,
   and publisher daemons absent. Stop/restore ordering is private-host operator work: do not
   start trading or invent service commands here.
5. Run fresh-checkpoint publication **#1 before deletion**. Retain its complete JSON and ledger.
   Unaffected records are accepted/enriched; corrected frozen records quarantine. A successful
   exit alone is insufficient. Any global publication failure stops this sequence.
6. Capture the complete post-run-1 public state. Freeze the sanitized cumulative `PublicationBatch`
   containing **all** projected IDs at the same reviewed state, including refused legacy IDs and
   any legitimate new records. Include the original explicit `public_available_at` on every row.
   It must be at least `published_at + 1800 seconds`. No ID discovery occurs in this tool.
7. Assemble and review the typed manifest, binding baseline, post-run-1 snapshot, catalog,
   projection, quarantine, archived-file hashes and private receipt/plan hash. Quarantine must
   equal applied IDs exactly, with `PublicationTerminalConflict` entries. Every affected row must
   remain terminal and byte-identical to baseline, without child rows. Unaffected rows must match
   run #1's projection and preserve frozen baseline fields. Refused IDs must equal residual
   `tp3`/`expired` projected rows. No hard-coded population count is used.
8. Generate artifacts and rehearse on disposable PostgreSQL built from the parity baseline plus
   migration (including the legacy child tables from the reviewed live catalog). Review the full
   SQL and output plan. Production execution remains a separately authorized operator action.
9. Execute `delete.sql` once with `psql -X -v ON_ERROR_STOP=1`. It locks the four tables NOWAIT,
   checks every row, count and catalog entry, deletes only exact IDs, and proves the remaining
   state before commit. Concurrent publication fails the lock/state checks. Any assertion failure
   aborts the transaction; a disconnected session rolls back. Retain the success receipt printed
   **after commit**. Lost acknowledgement means recapture and compare with `remaining_sha256`;
   never blindly rerun or assume failure.
10. Run publication **#2 without resetting either new checkpoint or quarantine ledger**.
    The existing private worker retries quarantined IDs individually. `republish.json` also
    contains the exact sanitized affected-only `PublicationBatch` for review/rehearsal; it is
    not an automatic sender. Keep its original reviewed clocks. If new private activity changes
    the projection, stop for fresh evidence. A partial run leaves the ledger as retry authority;
    rerun publication after diagnosis, never rerun deletion.
11. Capture post-publication state, the full publisher JSON and ledger, and complete anonymous
    landing-view results after the 90-second freshness window. Run offline verification below.
    Retain before/after status/reason counts, receipts, ledger hashes and API parity evidence in
    the private workflow record. Partial corrections leave refused rows explicitly residual.

## Commands and manifest contract

Install the repository's normal development dependencies. From an exact reviewed checkout:

```bash
python scripts/public_rebaseline.py manifest-schema > /private/evidence/manifest-schema.json
python scripts/public_rebaseline.py capture-sql --out /private/evidence/capture.sql
```

The generated read-only transaction emits one JSON object. A separately authorized operator uses
`psql -X -qAt -v ON_ERROR_STOP=1` to capture it as `baseline.json`, `before.json` or `after.json`.
Use the same database owner role, database and UTC timezone for capture and apply: catalog evidence
includes role-visible columns/grants. Live catalog evidence remains required; the test baseline is
not a declaration that the unversioned production schema is identical.

The manifest schema has no permissive extras or default affected IDs. Use `manifest-schema` for
the complete field list. Hashes of JSON use sorted keys, compact separators, ASCII escapes and
SHA-256 (not the file's whitespace). Raw archived checkpoint/quarantine **file** hashes use
`sha256sum`; private `receipt_sha256` uses the accepted WoodsBot canonical JSON algorithm.

```bash
python scripts/public_rebaseline.py hash /private/evidence/baseline.json
python scripts/public_rebaseline.py hash /private/evidence/before.json
python scripts/public_rebaseline.py hash /private/evidence/catalog.json
python scripts/public_rebaseline.py hash --publication /private/evidence/projection.json
python scripts/public_rebaseline.py hash /private/evidence/quarantine-run1.json
python scripts/public_rebaseline.py hash /private/evidence/manifest.json
```

`catalog.json` is the unmodified `catalog` object in the capture. `--publication` first validates
and normalizes through Curren's strict `PublicationBatch` model, including defaults and timestamps.
The reviewed manifest's SHA must be supplied independently; calculating a hash is not review.
The tool verifies the receipt's own hash, `verified=true`, `mode=verify-applied`, zero mutations,
accepted private revision, exact IDs and `plan_sha256`. It does not invent an apply receipt.

```bash
python scripts/public_rebaseline.py prepare \
  --manifest /private/evidence/manifest.json --expect-manifest-sha256 REVIEWED_SHA256 \
  --private-receipt /private/evidence/verify-applied.json \
  --baseline /private/evidence/baseline.json --before /private/evidence/before.json \
  --projection /private/evidence/projection.json --quarantine /private/evidence/quarantine-run1.json \
  --out /private/evidence/rebaseline
```

Outputs are mode 0600 in a new mode 0700 directory; existing output directories/files are refused.
`plan.json` includes full before-row fingerprints, exact counts, remaining-state hash and reset/retry
instructions. `rehearse.sql` runs the same delete/assertions followed by ROLLBACK. `restore.sql`
reinserts **all original columns**, including source, source clock, availability and precise numeric
values, only if the entire database still equals the exact post-delete snapshot. It refuses after
any successful republish or other intervening write. Partial-publication recovery must use the
ledger, not overwrite newly inserted records with legacy backups. The delete itself refuses both
an immediate rerun and a rerun after corrected rows have been reinserted.

For the verifier, `public.json` is an offline observation with `observed_at` (UTC ISO timestamp),
`feed_status` (`stale` or `idle`), `live_signals` (empty after freshness expiry), and `recent_results`
(complete anonymous result rows, not a paginated sample). Result IDs/counts and all supplied safe
columns must equal the replica; at minimum include id, status, realized_r, closed_at and exit_reason.
Entry/stop/targets/source/lifecycle in this public capture are refused. The operator must also
confirm that the actual landing page displays the same count/status and that anonymous reads of
restricted columns/children and execution of the ingest RPC remain denied. Security Advisor and
the deployed function identity are external observations, not claims inferred from a local file.

```bash
python scripts/public_rebaseline.py verify \
  --manifest /private/evidence/manifest.json --expect-manifest-sha256 REVIEWED_SHA256 \
  --before /private/evidence/before.json --after /private/evidence/after.json \
  --projection /private/evidence/projection.json --quarantine /private/evidence/quarantine-run2.json \
  --run /private/evidence/publication-run2.json --public /private/evidence/public.json \
  --out /private/evidence/verified.json
```

Verification requires empty active quarantine, candidates = projected = published, zero stale
ignores, exact ID sets, every projection field, lifecycle identity/value parity, residual legacy IDs,
catalog parity and anonymous result parity. It also ingests the frozen sanitized batch into a
temporary local canonical `ReadStore` and compares API projections. This is **local API parity**;
it does not claim `api.curren.tech` has a store or that continuous publication is active.

## Source validation

```bash
CURREN_REBASELINE_POSTGRES=1 pytest -q tests/test_public_rebaseline.py
CURREN_SUPABASE_BRIDGE_PARITY=1 pytest -q tests/test_supabase_bridge_parity.py
MYPYPATH=src mypy scripts/public_rebaseline.py --follow-imports=silent
ruff check .
```

The first test creates only an isolated, network-disabled, temporary PostgreSQL container. Tests
exercise the real migration/RPC, deletion, restoration, post-write rollback, drift and rerun refusal.
The bridge parity suite independently checks immutable ingestion and anonymous access against the
FastAPI reference. No production target, private database or credential is needed.
