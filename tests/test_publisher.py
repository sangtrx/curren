from __future__ import annotations

import httpx
import pytest

from curren.models import PublicationBatch
from curren.publisher import PublicationClient


@pytest.mark.asyncio
async def test_publication_client_sends_bearer_token_and_contract() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/internal/v1/publications"
        assert request.headers["Authorization"] == "Bearer ingest-secret"
        payload = __import__("json").loads(request.content)
        assert payload["source"] == "test"
        assert payload["signals"][0]["id"] == "crn_sig_1"
        return httpx.Response(
            200,
            json={"accepted": 1, "inserted": 1, "updated": 0, "lifecycle_events_inserted": 0},
        )

    batch = PublicationBatch.model_validate(
        {
            "source": "test",
            "generated_at": "2026-08-23T12:00:00Z",
            "signals": [
                {
                    "id": "crn_sig_1",
                    "symbol": "BTCUSDT",
                    "side": "long",
                    "status": "active",
                    "published_at": "2026-08-23T12:00:00Z",
                }
            ],
        }
    )
    async with PublicationClient(
        base_url="https://example.test",
        ingest_token="ingest-secret",
        transport=httpx.MockTransport(handler),
    ) as client:
        result = await client.publish(batch)

    assert result.inserted == 1


def test_publication_client_requires_token(monkeypatch) -> None:
    monkeypatch.delenv("CURREN_INGEST_TOKEN", raising=False)
    with pytest.raises(ValueError, match="CURREN_INGEST_TOKEN"):
        PublicationClient(base_url="https://example.test", ingest_token=None)
