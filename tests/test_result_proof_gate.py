from __future__ import annotations

import sqlite3

import httpx
import pytest

from curren.server import create_app


@pytest.mark.asyncio
async def test_legacy_terminal_row_without_outcome_record_is_not_exposed_as_proof(tmp_path) -> None:
    database = tmp_path / "curren.db"
    app = create_app(database_path=str(database), public_rate_limit=100)

    # Simulate a terminal row from a pre-outcome-record read model. v0.4 must not
    # present this row through terminal read surfaces as proof-backed data.
    with sqlite3.connect(database) as connection:
        connection.execute(
            """
            INSERT INTO signals (
                id, symbol, side, status, published_at, public_available_at,
                entry, stop, targets_json, mark, current_r, peak_r, realized_r,
                closed_at, exit_reason, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "crn_legacy_terminal",
                "BTCUSDT",
                "long",
                "closed",
                "2026-08-23T10:00:00.000000Z",
                "2026-08-23T10:00:00.000000Z",
                100000.0,
                99000.0,
                "[]",
                102000.0,
                2.0,
                2.0,
                2.0,
                "2026-08-23T11:00:00.000000Z",
                "tp2",
                "2026-08-23T11:00:01.000000Z",
            ),
        )
        connection.commit()

    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        results = await client.get("/v1/results")
        terminal_list = await client.get("/v1/signals", params={"status": "closed"})
        direct = await client.get("/v1/signals/crn_legacy_terminal")
        lifecycle = await client.get("/v1/signals/crn_legacy_terminal/lifecycle")
        summary = await client.get("/v1/public/summary")
        track = await client.get("/v1/track-record")

    assert results.status_code == 200
    assert results.json()["items"] == []
    assert terminal_list.json()["items"] == []
    assert direct.status_code == 404
    assert lifecycle.status_code == 404
    assert summary.json()["recent_results"] == []
    assert track.json()["sample_size"] == 0
