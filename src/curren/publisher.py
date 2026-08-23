from __future__ import annotations

import argparse
import asyncio
import json
import os
from pathlib import Path

import httpx

from curren.client import CurrenError
from curren.models import IngestResult, PublicationBatch

DEFAULT_API_URL = "https://api.curren.tech"


class PublicationClient:
    """Push sanitized projections to the Curren public read model.

    This client is intended for private runtime integrations. It accepts only
    the public PublicationBatch contract and has no access to trading/execution
    APIs because those APIs do not exist on the public service.
    """

    def __init__(
        self,
        *,
        base_url: str | None = None,
        ingest_token: str | None = None,
        timeout_seconds: float = 10.0,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        resolved_url = (base_url or os.getenv("CURREN_API_URL") or DEFAULT_API_URL).rstrip("/")
        resolved_token = ingest_token if ingest_token is not None else os.getenv("CURREN_INGEST_TOKEN")
        if not resolved_token:
            raise ValueError("CURREN_INGEST_TOKEN is required for publication")
        self._client = httpx.AsyncClient(
            base_url=resolved_url,
            headers={
                "Accept": "application/json",
                "Content-Type": "application/json",
                "Authorization": f"Bearer {resolved_token}",
                "User-Agent": "curren-publisher/0.3.0",
            },
            timeout=timeout_seconds,
            transport=transport,
            follow_redirects=False,
        )

    async def __aenter__(self) -> PublicationClient:
        return self

    async def __aexit__(self, *_args: object) -> None:
        await self._client.aclose()

    async def publish(self, batch: PublicationBatch) -> IngestResult:
        try:
            response = await self._client.post(
                "/internal/v1/publications",
                content=batch.model_dump_json(),
            )
        except httpx.TimeoutException as exc:
            raise CurrenError("Curren publication request timed out") from exc
        except httpx.HTTPError as exc:
            raise CurrenError("Curren publication request failed") from exc
        if response.status_code >= 400:
            detail = _response_detail(response)
            retry_after = response.headers.get("Retry-After")
            retry = f"; retry after {retry_after}s" if response.status_code == 429 and retry_after else ""
            raise CurrenError(
                f"Curren publication rejected with HTTP {response.status_code}: {detail}{retry}",
                status_code=response.status_code,
            )
        try:
            return IngestResult.model_validate(response.json())
        except ValueError as exc:
            raise CurrenError("Curren publication endpoint returned invalid JSON") from exc


def main() -> None:
    parser = argparse.ArgumentParser(description="Publish a sanitized Curren PublicationBatch JSON file.")
    parser.add_argument("path", type=Path, help="Path to a PublicationBatch JSON file")
    parser.add_argument("--api-url", default=None, help="Override CURREN_API_URL")
    arguments = parser.parse_args()
    raw = json.loads(arguments.path.read_text(encoding="utf-8"))
    batch = PublicationBatch.model_validate(raw)
    result = asyncio.run(_publish_once(batch, api_url=arguments.api_url))
    print(result.model_dump_json(indent=2))


async def _publish_once(batch: PublicationBatch, *, api_url: str | None) -> IngestResult:
    async with PublicationClient(base_url=api_url) as client:
        return await client.publish(batch)


def _response_detail(response: httpx.Response) -> str:
    try:
        payload = response.json()
    except ValueError:
        return response.text[:200] or "no detail"
    if isinstance(payload, dict) and payload.get("detail"):
        return str(payload["detail"])
    return str(payload)[:200]


if __name__ == "__main__":
    main()
