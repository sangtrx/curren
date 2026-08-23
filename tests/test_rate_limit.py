from __future__ import annotations

import httpx
import pytest

from curren.server import create_app


async def _client(app, *, peer: str = "127.0.0.1") -> httpx.AsyncClient:
    transport = httpx.ASGITransport(app=app, client=(peer, 12345))
    return httpx.AsyncClient(transport=transport, base_url="http://test")


@pytest.mark.asyncio
async def test_public_and_authenticated_rate_limits_use_separate_buckets(tmp_path) -> None:
    app = create_app(
        database_path=str(tmp_path / "curren.db"),
        api_keys={"premium-key-123": "premium"},
        public_rate_limit=1,
        authenticated_rate_limit=2,
        rate_limit_window_seconds=60,
    )

    async with await _client(app) as client:
        public_ok = await client.get("/v1/public/summary")
        public_limited = await client.get("/v1/public/summary")
        premium_one = await client.get(
            "/v1/signals",
            headers={"Authorization": "Bearer premium-key-123"},
        )
        premium_two = await client.get(
            "/v1/signals",
            headers={"Authorization": "Bearer premium-key-123"},
        )
        premium_limited = await client.get(
            "/v1/signals",
            headers={"Authorization": "Bearer premium-key-123"},
        )

    assert public_ok.status_code == 200
    assert public_ok.headers["X-RateLimit-Limit"] == "1"
    assert public_limited.status_code == 429
    assert public_limited.headers["Retry-After"]
    assert premium_one.status_code == 200
    assert premium_two.status_code == 200
    assert premium_limited.status_code == 429


@pytest.mark.asyncio
async def test_rotating_invalid_tokens_cannot_bypass_public_peer_limit(tmp_path) -> None:
    app = create_app(
        database_path=str(tmp_path / "curren.db"),
        api_keys={"premium-key-123": "premium"},
        public_rate_limit=1,
        authenticated_rate_limit=100,
    )

    async with await _client(app) as client:
        first = await client.get(
            "/v1/signals",
            headers={"Authorization": "Bearer attacker-token-one"},
        )
        second = await client.get(
            "/v1/signals",
            headers={"Authorization": "Bearer attacker-token-two"},
        )

    assert first.status_code == 401
    assert second.status_code == 429


@pytest.mark.asyncio
async def test_forwarded_ip_is_ignored_from_untrusted_peer(tmp_path) -> None:
    app = create_app(
        database_path=str(tmp_path / "curren.db"),
        public_rate_limit=1,
    )

    async with await _client(app) as client:
        first = await client.get("/v1/public/summary", headers={"X-Forwarded-For": "203.0.113.10"})
        second = await client.get("/v1/public/summary", headers={"X-Forwarded-For": "203.0.113.11"})

    assert first.status_code == 200
    assert second.status_code == 429


@pytest.mark.asyncio
async def test_allowlisted_proxy_can_supply_forwarded_client_ip(tmp_path) -> None:
    app = create_app(
        database_path=str(tmp_path / "curren.db"),
        public_rate_limit=1,
        trusted_proxy_ips="127.0.0.1/32",
    )

    async with await _client(app, peer="127.0.0.1") as client:
        first_client = await client.get("/v1/public/summary", headers={"X-Forwarded-For": "203.0.113.10"})
        second_client = await client.get("/v1/public/summary", headers={"X-Forwarded-For": "203.0.113.11"})
        first_client_again = await client.get(
            "/v1/public/summary",
            headers={"X-Forwarded-For": "203.0.113.10"},
        )

    assert first_client.status_code == 200
    assert second_client.status_code == 200
    assert first_client_again.status_code == 429


@pytest.mark.asyncio
async def test_trusted_proxy_chain_uses_first_untrusted_hop_from_the_right(tmp_path) -> None:
    app = create_app(
        database_path=str(tmp_path / "curren.db"),
        public_rate_limit=1,
        trusted_proxy_ips="127.0.0.1/32,10.0.0.0/8",
    )

    async with await _client(app, peer="127.0.0.1") as client:
        # Left-most values can be attacker-supplied. 198.51.100.9 is the actual
        # untrusted client immediately before the trusted 10/8 proxy hop.
        first = await client.get(
            "/v1/public/summary",
            headers={"X-Forwarded-For": "203.0.113.66, 198.51.100.9, 10.1.2.3"},
        )
        spoof_changed = await client.get(
            "/v1/public/summary",
            headers={"X-Forwarded-For": "203.0.113.77, 198.51.100.9, 10.1.2.3"},
        )
        other_client = await client.get(
            "/v1/public/summary",
            headers={"X-Forwarded-For": "198.51.100.10, 10.1.2.3"},
        )

    assert first.status_code == 200
    assert spoof_changed.status_code == 429
    assert other_client.status_code == 200


@pytest.mark.asyncio
async def test_ingestion_has_its_own_rate_limit(tmp_path) -> None:
    app = create_app(
        database_path=str(tmp_path / "curren.db"),
        ingest_token="ingest-secret",
        ingest_rate_limit=1,
        public_rate_limit=100,
    )
    payload = {
        "source": "test-runtime",
        "generated_at": "2026-08-23T12:00:01Z",
        "signals": [
            {
                "id": "crn_sig_rl",
                "symbol": "BTCUSDT",
                "side": "long",
                "status": "active",
                "published_at": "2026-08-23T12:00:00Z",
                "entry": 100000.0,
                "stop": 99000.0,
                "targets": [{"price": 102000.0}],
            }
        ],
    }

    async with await _client(app) as client:
        first = await client.post(
            "/internal/v1/publications",
            json=payload,
            headers={"Authorization": "Bearer ingest-secret"},
        )
        second = await client.post(
            "/internal/v1/publications",
            json=payload,
            headers={"Authorization": "Bearer ingest-secret"},
        )

    assert first.status_code == 200
    assert second.status_code == 429
    assert second.headers["X-RateLimit-Remaining"] == "0"


@pytest.mark.asyncio
async def test_health_check_is_not_rate_limited(tmp_path) -> None:
    app = create_app(
        database_path=str(tmp_path / "curren.db"),
        public_rate_limit=1,
    )

    async with await _client(app) as client:
        responses = [await client.get("/healthz") for _ in range(5)]

    assert all(response.status_code == 200 for response in responses)
    assert all("X-RateLimit-Limit" not in response.headers for response in responses)
