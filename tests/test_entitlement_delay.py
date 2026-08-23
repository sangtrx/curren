from __future__ import annotations

import httpx
import pytest

from curren.server import create_app


@pytest.mark.asyncio
async def test_public_delay_hides_known_signal_id_while_premium_can_read(tmp_path) -> None:
    app = create_app(
        database_path=str(tmp_path / "curren.db"),
        ingest_token="ingest-secret",
        api_keys={"premium-key-123": "premium"},
        public_delay_seconds=1800,
    )
    payload = {
        "source": "test-runtime",
        "generated_at": "2026-08-23T12:00:05Z",
        "signals": [
            {
                "id": "crn_sig_hidden",
                "symbol": "BTCUSDT",
                "side": "short",
                "status": "active",
                "published_at": "2026-08-23T12:00:00Z",
                "public_available_at": "2099-01-01T00:00:00Z",
                "entry": 100000.0,
                "stop": 101000.0,
                "targets": [{"price": 98000.0}],
            }
        ],
    }

    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        ingested = await client.post(
            "/internal/v1/publications",
            json=payload,
            headers={"Authorization": "Bearer ingest-secret"},
        )
        public_list = await client.get("/v1/signals")
        public_direct = await client.get("/v1/signals/crn_sig_hidden")
        premium_direct = await client.get(
            "/v1/signals/crn_sig_hidden",
            headers={"Authorization": "Bearer premium-key-123"},
        )

    assert ingested.status_code == 200
    assert public_list.json()["items"] == []
    assert public_direct.status_code == 404
    assert premium_direct.status_code == 200
    assert premium_direct.json()["entry"] == 100000.0


@pytest.mark.asyncio
async def test_server_policy_prevents_publisher_from_shortening_public_delay(tmp_path) -> None:
    app = create_app(
        database_path=str(tmp_path / "curren.db"),
        ingest_token="ingest-secret",
        api_keys={"premium-key-123": "premium"},
        public_delay_seconds=1800,
    )
    payload = {
        "source": "test-runtime",
        "generated_at": "2099-01-01T00:00:01Z",
        "signals": [
            {
                "id": "crn_sig_delay_floor",
                "symbol": "ETHUSDT",
                "side": "long",
                "status": "active",
                "published_at": "2099-01-01T00:00:00Z",
                "public_available_at": "2099-01-01T00:00:00Z",
                "entry": 5000.0,
                "stop": 4900.0,
                "targets": [{"price": 5100.0}],
            }
        ],
    }

    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        ingested = await client.post(
            "/internal/v1/publications",
            json=payload,
            headers={"Authorization": "Bearer ingest-secret"},
        )
        public_direct = await client.get("/v1/signals/crn_sig_delay_floor")
        premium_direct = await client.get(
            "/v1/signals/crn_sig_delay_floor",
            headers={"Authorization": "Bearer premium-key-123"},
        )

    assert ingested.status_code == 200
    assert public_direct.status_code == 404
    assert premium_direct.status_code == 200
    assert premium_direct.json()["entry"] == 5000.0
