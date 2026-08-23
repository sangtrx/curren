from __future__ import annotations

from datetime import UTC, datetime

import httpx
import pytest

from curren.server import create_app


@pytest.fixture
def app(tmp_path):
    return create_app(
        database_path=str(tmp_path / "curren.db"),
        ingest_token="ingest-secret",
        api_keys={"premium-key-123": "premium", "agent-key-12345": "agent"},
        public_delay_seconds=0,
    )


@pytest.fixture
def active_payload() -> dict:
    return {
        "source": "test-runtime",
        "generated_at": "2026-08-23T12:00:05Z",
        "signals": [
            {
                "id": "crn_sig_1",
                "symbol": "HYPEUSDT",
                "side": "long",
                "status": "active",
                "published_at": "2026-08-23T12:00:00Z",
                "entry": 42.18,
                "stop": 40.90,
                "targets": [
                    {"price": 43.45, "status": "hit", "hit_at": "2026-08-23T12:10:00Z"},
                    {"price": 44.72, "status": "pending"},
                ],
                "mark": 43.60,
                "current_r": 1.10,
                "peak_r": 1.25,
                "lifecycle": [
                    {
                        "event_type": "entry_hit",
                        "event_at": "2026-08-23T12:01:00Z",
                        "price": 42.18,
                        "r_multiple": 0.0,
                    },
                    {
                        "event_type": "tp1_hit",
                        "event_at": "2026-08-23T12:10:00Z",
                        "price": 43.45,
                        "r_multiple": 1.0,
                    },
                ],
            }
        ],
    }


async def _client(app) -> httpx.AsyncClient:
    return httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test")


@pytest.mark.asyncio
async def test_health_starts_empty(app) -> None:
    async with await _client(app) as client:
        response = await client.get("/healthz")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "signals": 0, "ingestion_enabled": True}


@pytest.mark.asyncio
async def test_ingestion_requires_token(app, active_payload) -> None:
    async with await _client(app) as client:
        response = await client.post("/internal/v1/publications", json=active_payload)
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_public_active_hides_levels_but_premium_reveals_them(app, active_payload) -> None:
    async with await _client(app) as client:
        ingested = await client.post(
            "/internal/v1/publications",
            json=active_payload,
            headers={"Authorization": "Bearer ingest-secret"},
        )
        assert ingested.status_code == 200

        public = await client.get("/v1/signals", params={"status": "active"})
        premium = await client.get(
            "/v1/signals",
            params={"status": "active"},
            headers={"Authorization": "Bearer premium-key-123"},
        )

    public_signal = public.json()["items"][0]
    premium_signal = premium.json()["items"][0]
    assert public_signal["entry"] is None
    assert public_signal["stop"] is None
    assert public_signal["targets"] == []
    assert public_signal["current_r"] == 1.1
    assert premium_signal["entry"] == 42.18
    assert premium_signal["stop"] == 40.9
    assert [item["price"] for item in premium_signal["targets"]] == [43.45, 44.72]


@pytest.mark.asyncio
async def test_public_active_lifecycle_hides_prices(app, active_payload) -> None:
    async with await _client(app) as client:
        await client.post(
            "/internal/v1/publications",
            json=active_payload,
            headers={"Authorization": "Bearer ingest-secret"},
        )
        public = await client.get("/v1/signals/crn_sig_1/lifecycle")
        premium = await client.get(
            "/v1/signals/crn_sig_1/lifecycle",
            headers={"Authorization": "Bearer premium-key-123"},
        )

    assert [item["event_type"] for item in public.json()["items"]] == ["entry_hit", "tp1_hit"]
    assert all(item["price"] is None for item in public.json()["items"])
    assert premium.json()["items"][0]["price"] == 42.18


@pytest.mark.asyncio
async def test_closed_result_becomes_full_public_proof(app, active_payload) -> None:
    closed = active_payload.copy()
    closed["signals"] = [dict(active_payload["signals"][0])]
    closed_signal = closed["signals"][0]
    closed_signal.update(
        {
            "status": "closed",
            "mark": 44.72,
            "realized_r": 2.0,
            "closed_at": "2026-08-23T12:20:00Z",
            "exit_reason": "tp2",
        }
    )

    async with await _client(app) as client:
        first = await client.post(
            "/internal/v1/publications",
            json=active_payload,
            headers={"Authorization": "Bearer ingest-secret"},
        )
        second = await client.post(
            "/internal/v1/publications",
            json=closed,
            headers={"Authorization": "Bearer ingest-secret"},
        )
        results = await client.get("/v1/results")
        track = await client.get("/v1/track-record")

    assert first.json()["inserted"] == 1
    assert second.json()["updated"] == 1
    item = results.json()["items"][0]
    assert item["entry"] == 42.18
    assert item["realized_r"] == 2.0
    assert track.json()["sample_size"] == 1
    assert track.json()["wins"] == 1
    assert track.json()["net_r"] == 2.0


@pytest.mark.asyncio
async def test_immutable_trade_plan_mutation_is_rejected(app, active_payload) -> None:
    changed = active_payload.copy()
    changed["signals"] = [dict(active_payload["signals"][0])]
    changed["signals"][0]["entry"] = 99.0

    async with await _client(app) as client:
        first = await client.post(
            "/internal/v1/publications",
            json=active_payload,
            headers={"Authorization": "Bearer ingest-secret"},
        )
        conflict = await client.post(
            "/internal/v1/publications",
            json=changed,
            headers={"Authorization": "Bearer ingest-secret"},
        )

    assert first.status_code == 200
    assert conflict.status_code == 409
    assert "immutable publication fields changed" in conflict.json()["detail"]


@pytest.mark.asyncio
async def test_verification_hash_checks_recorded_snapshot(app, active_payload) -> None:
    async with await _client(app) as client:
        await client.post(
            "/internal/v1/publications",
            json=active_payload,
            headers={"Authorization": "Bearer ingest-secret"},
        )
        response = await client.get("/v1/signals/crn_sig_1/verification")

    payload = response.json()
    assert payload["verified"] is True
    assert payload["immutable"] is True
    assert payload["content_hash"].startswith("sha256:")
    assert payload["record_version"] == "signal-publication.v1"
    assert datetime.fromisoformat(payload["recorded_at"].replace("Z", "+00:00")).tzinfo == UTC


@pytest.mark.asyncio
async def test_unknown_api_key_fails_closed(app) -> None:
    async with await _client(app) as client:
        response = await client.get(
            "/v1/signals",
            headers={"Authorization": "Bearer unknown-key"},
        )
    assert response.status_code == 401
