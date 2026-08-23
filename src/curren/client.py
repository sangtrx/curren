from __future__ import annotations

import os
from collections.abc import Mapping
from typing import Any

import httpx

from curren.models import LifecycleEvent, PublicSummary, Signal, SignalList, TrackRecord, VerificationRecord

DEFAULT_API_URL = "https://api.curren.tech"
DEFAULT_TIMEOUT_SECONDS = 10.0


class CurrenError(RuntimeError):
    def __init__(self, message: str, *, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code


class CurrenClient:
    """Async, read-only client for the external Curren API."""

    def __init__(
        self,
        *,
        base_url: str | None = None,
        api_key: str | None = None,
        timeout_seconds: float | None = None,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        resolved_url = (base_url or os.getenv("CURREN_API_URL") or DEFAULT_API_URL).rstrip("/")
        resolved_key = api_key if api_key is not None else os.getenv("CURREN_API_KEY")
        if timeout_seconds is None:
            raw_timeout = os.getenv("CURREN_TIMEOUT_SECONDS")
            timeout_seconds = float(raw_timeout) if raw_timeout else DEFAULT_TIMEOUT_SECONDS

        headers = {
            "Accept": "application/json",
            "User-Agent": "curren-python/0.2.0",
        }
        if resolved_key:
            headers["Authorization"] = f"Bearer {resolved_key}"

        self._client = httpx.AsyncClient(
            base_url=resolved_url,
            headers=headers,
            timeout=timeout_seconds,
            transport=transport,
            follow_redirects=False,
        )

    async def __aenter__(self) -> CurrenClient:
        return self

    async def __aexit__(self, *_args: object) -> None:
        await self.aclose()

    async def aclose(self) -> None:
        await self._client.aclose()

    async def list_active_signals(self, *, symbol: str | None = None, limit: int = 20) -> SignalList:
        params: dict[str, str | int] = {"status": "active", "limit": _bounded_limit(limit)}
        if symbol:
            params["symbol"] = symbol.upper()
        payload = await self._get_json("/v1/signals", params=params)
        return SignalList.model_validate(payload)

    async def get_signal(self, signal_id: str) -> Signal:
        payload = await self._get_json(f"/v1/signals/{_safe_id(signal_id)}")
        return Signal.model_validate(payload)

    async def get_signal_lifecycle(self, signal_id: str) -> list[LifecycleEvent]:
        payload = await self._get_json(f"/v1/signals/{_safe_id(signal_id)}/lifecycle")
        items = payload.get("items", []) if isinstance(payload, Mapping) else []
        return [LifecycleEvent.model_validate(item) for item in items]

    async def get_recent_results(self, *, limit: int = 20) -> SignalList:
        payload = await self._get_json(
            "/v1/results",
            params={"limit": _bounded_limit(limit)},
        )
        return SignalList.model_validate(payload)

    async def get_track_record(self) -> TrackRecord:
        payload = await self._get_json("/v1/track-record")
        return TrackRecord.model_validate(payload)

    async def verify_signal(self, signal_id: str) -> VerificationRecord:
        payload = await self._get_json(f"/v1/signals/{_safe_id(signal_id)}/verification")
        return VerificationRecord.model_validate(payload)

    async def get_public_summary(self) -> PublicSummary:
        payload = await self._get_json("/v1/public/summary")
        return PublicSummary.model_validate(payload)

    async def _get_json(self, path: str, *, params: Mapping[str, str | int] | None = None) -> Any:
        try:
            response = await self._client.get(path, params=params)
        except httpx.TimeoutException as exc:
            raise CurrenError("Curren API request timed out") from exc
        except httpx.HTTPError as exc:
            raise CurrenError("Curren API request failed") from exc

        if response.status_code in {401, 403}:
            raise CurrenError("Curren API entitlement does not allow this request", status_code=response.status_code)
        if response.status_code == 404:
            raise CurrenError("Curren resource was not found", status_code=404)
        if response.status_code >= 400:
            raise CurrenError(f"Curren API returned HTTP {response.status_code}", status_code=response.status_code)

        try:
            return response.json()
        except ValueError as exc:
            raise CurrenError("Curren API returned an invalid JSON response", status_code=response.status_code) from exc


def _bounded_limit(limit: int) -> int:
    if not 1 <= limit <= 100:
        raise ValueError("limit must be between 1 and 100")
    return limit


def _safe_id(value: str) -> str:
    value = value.strip()
    if not value or "/" in value or ".." in value:
        raise ValueError("invalid signal id")
    return value
