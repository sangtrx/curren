from __future__ import annotations

import httpx
import pytest

from curren.server import create_app


async def _client(app) -> httpx.AsyncClient:
    return httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test")


def _signal() -> dict:
    return {
        "id": "crn_sig_schedule",
        "symbol": "BTCUSDT",
        "side": "long",
        "status": "active",
        "published_at": "2026-08-23T12:00:00Z",
        "public_available_at": "2026-08-23T12:00:00Z",
        "entry": 100000.0,
        "stop": 99000.0,
        "targets": [{"price": 102000.0}],
        "mark": 100100.0,
        "current_r": 0.1,
    }


@pytest.mark.asyncio
async def test_public_availability_cannot_be_moved_after_first_publication(tmp_path) -> None:
    app = create_app(
        database_path=str(tmp_path / "curren.db"),
        ingest_token="ingest-secret",
        public_delay_seconds=0,
        public_rate_limit=100,
        ingest_rate_limit=100,
    )
    first = {
        "source": "test-runtime",
        "generated_at": "2026-08-23T12:00:01Z",
        "signals": [_signal()],
    }
    later_signal = {**_signal(), "public_available_at": "2099-01-01T00:00:00Z", "mark": 100500.0}
    later = {
        "source": "test-runtime",
        "generated_at": "2026-08-23T12:01:00Z",
        "signals": [later_signal],
    }

    async with await _client(app) as client:
        initial = await client.post(
            "/internal/v1/publications",
            json=first,
            headers={"Authorization": "Bearer ingest-secret"},
        )
        before = await client.get("/v1/signals/crn_sig_schedule")
        updated = await client.post(
            "/internal/v1/publications",
            json=later,
            headers={"Authorization": "Bearer ingest-secret"},
        )
        after = await client.get("/v1/signals/crn_sig_schedule")

    assert initial.status_code == 200
    assert before.status_code == 200
    assert updated.status_code == 200
    assert after.status_code == 200
    assert after.json()["mark"] == 100500.0
    assert after.json()["available_at"] == before.json()["available_at"]


@pytest.mark.asyncio
async def test_duplicate_signal_ids_in_one_batch_are_rejected(tmp_path) -> None:
    app = create_app(
        database_path=str(tmp_path / "curren.db"),
        ingest_token="ingest-secret",
        public_rate_limit=100,
        ingest_rate_limit=100,
    )
    payload = {
        "source": "test-runtime",
        "generated_at": "2026-08-23T12:00:01Z",
        "signals": [_signal(), _signal()],
    }

    async with await _client(app) as client:
        response = await client.post(
            "/internal/v1/publications",
            json=payload,
            headers={"Authorization": "Bearer ingest-secret"},
        )

    assert response.status_code == 422
    assert "duplicate signal id" in response.text
