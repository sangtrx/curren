from __future__ import annotations

import json

import httpx
import pytest

from curren.client import CurrenClient, CurrenError


@pytest.mark.asyncio
async def test_active_signals_accept_entitlement_omitted_levels() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/v1/signals"
        assert request.url.params["status"] == "active"
        return httpx.Response(
            200,
            json={
                "items": [
                    {
                        "id": "crn_sig_1",
                        "symbol": "HYPEUSDT",
                        "side": "long",
                        "status": "active",
                        "published_at": "2026-08-23T11:30:00Z",
                        "current_r": 1.2,
                        "access": "delayed",
                    }
                ],
                "next_cursor": None,
            },
        )

    transport = httpx.MockTransport(handler)
    async with CurrenClient(base_url="https://example.test", transport=transport) as client:
        result = await client.list_active_signals(limit=5)

    assert result.items[0].symbol == "HYPEUSDT"
    assert result.items[0].entry is None
    assert result.items[0].stop is None
    assert result.items[0].targets == []


@pytest.mark.asyncio
async def test_client_sends_bearer_token_without_putting_it_in_url() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["Authorization"] == "Bearer crn_secret"
        assert "crn_secret" not in str(request.url)
        return httpx.Response(200, json={"items": [], "next_cursor": None})

    async with CurrenClient(
        base_url="https://example.test",
        api_key="crn_secret",
        transport=httpx.MockTransport(handler),
    ) as client:
        await client.list_active_signals()


@pytest.mark.asyncio
async def test_entitlement_failure_is_explicit() -> None:
    transport = httpx.MockTransport(lambda _request: httpx.Response(403, json={"detail": "forbidden"}))
    async with CurrenClient(base_url="https://example.test", transport=transport) as client:
        with pytest.raises(CurrenError, match="entitlement") as exc_info:
            await client.list_active_signals()

    assert exc_info.value.status_code == 403


@pytest.mark.asyncio
async def test_invalid_json_fails_closed() -> None:
    transport = httpx.MockTransport(
        lambda _request: httpx.Response(200, content=b"not-json", headers={"content-type": "application/json"})
    )
    async with CurrenClient(base_url="https://example.test", transport=transport) as client:
        with pytest.raises(CurrenError, match="invalid JSON"):
            await client.get_track_record()


def test_mock_payload_is_machine_serializable() -> None:
    payload = {
        "id": "crn_sig_1",
        "symbol": "BTCUSDT",
        "side": "short",
        "status": "closed",
        "published_at": "2026-08-23T11:30:00Z",
        "realized_r": 2.0,
    }
    assert json.loads(json.dumps(payload))["realized_r"] == 2.0
