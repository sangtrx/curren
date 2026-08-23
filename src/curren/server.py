from __future__ import annotations

import hmac
import json
import os
import re
from dataclasses import dataclass
from typing import Any

from fastapi import Depends, FastAPI, Header, HTTPException, Query, Request, Response, status

from curren.models import (
    HealthStatus,
    IngestResult,
    PublicationBatch,
    PublicSummary,
    Signal,
    SignalList,
    TrackRecord,
    VerificationRecord,
)
from curren.store import AccessPolicy, PublicationConflict, ReadStore, SignalNotFound

_SYMBOL_RE = re.compile(r"^[A-Z0-9._-]{2,32}$")
_ALLOWED_TIERS = frozenset({"premium", "agent"})


@dataclass(frozen=True)
class ServerConfig:
    database_path: str
    ingest_token: str | None
    api_keys: dict[str, str]
    public_delay_seconds: int

    @classmethod
    def from_env(cls) -> ServerConfig:
        return cls(
            database_path=os.getenv("CURREN_DB_PATH", "./.local/curren.db"),
            ingest_token=_clean_secret(os.getenv("CURREN_INGEST_TOKEN")),
            api_keys=_parse_api_keys(os.getenv("CURREN_API_KEYS_JSON", "{}")),
            public_delay_seconds=max(0, int(os.getenv("CURREN_PUBLIC_DELAY_SECONDS", "1800"))),
        )


def create_app(
    *,
    database_path: str | None = None,
    ingest_token: str | None = None,
    api_keys: dict[str, str] | None = None,
    public_delay_seconds: int | None = None,
) -> FastAPI:
    environment = ServerConfig.from_env()
    config = ServerConfig(
        database_path=database_path or environment.database_path,
        ingest_token=_clean_secret(ingest_token) if ingest_token is not None else environment.ingest_token,
        api_keys=dict(api_keys) if api_keys is not None else environment.api_keys,
        public_delay_seconds=(
            max(0, int(public_delay_seconds))
            if public_delay_seconds is not None
            else environment.public_delay_seconds
        ),
    )
    store = ReadStore(config.database_path, public_delay_seconds=config.public_delay_seconds)
    store.initialize()

    app = FastAPI(
        title="Curren API",
        version="0.2.0",
        description=(
            "Read-only trading-intelligence API backed by sanitized publications from the private Curren runtime. "
            "Public clients cannot execute trades or access private runtime state."
        ),
    )
    app.state.store = store
    app.state.config = config

    @app.middleware("http")
    async def security_headers(request: Request, call_next: Any) -> Response:
        response = await call_next(request)
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("Referrer-Policy", "no-referrer")
        response.headers.setdefault("X-Frame-Options", "DENY")
        if request.headers.get("Authorization"):
            response.headers.setdefault("Cache-Control", "private, no-store")
        return response

    def entitlement(authorization: str | None = Header(default=None)) -> AccessPolicy:
        if authorization is None:
            return AccessPolicy("public")
        token = _bearer_token(authorization)
        for configured_key, tier in config.api_keys.items():
            if hmac.compare_digest(token, configured_key):
                return AccessPolicy(tier)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid API key")

    def require_ingest(authorization: str | None = Header(default=None)) -> None:
        if not config.ingest_token:
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="ingestion is disabled")
        if authorization is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="ingestion token required")
        token = _bearer_token(authorization)
        if not hmac.compare_digest(token, config.ingest_token):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid ingestion token")

    @app.get("/healthz", response_model=HealthStatus, tags=["system"])
    def healthz() -> HealthStatus:
        return HealthStatus(
            status="ok",
            signals=store.signal_count(),
            ingestion_enabled=bool(config.ingest_token),
        )

    @app.get("/v1/public/summary", response_model=PublicSummary, tags=["public"])
    def public_summary(response: Response) -> PublicSummary:
        response.headers["Cache-Control"] = "public, max-age=30"
        return PublicSummary.model_validate(store.public_summary())

    @app.get("/v1/signals", response_model=SignalList, tags=["signals"])
    def signals(
        status_filter: str = Query("active", alias="status", min_length=1, max_length=32),
        symbol: str | None = Query(default=None, min_length=2, max_length=32),
        limit: int = Query(20, ge=1, le=100),
        policy: AccessPolicy = Depends(entitlement),
    ) -> SignalList:
        normalized_symbol = _symbol(symbol) if symbol else None
        return store.list_signals(status=status_filter, symbol=normalized_symbol, limit=limit, policy=policy)

    @app.get("/v1/signals/{signal_id}", response_model=Signal, tags=["signals"])
    def signal(signal_id: str, policy: AccessPolicy = Depends(entitlement)) -> Signal:
        try:
            return store.get_signal(_signal_id(signal_id), policy=policy)
        except SignalNotFound as exc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="signal not found") from exc

    @app.get("/v1/signals/{signal_id}/lifecycle", tags=["signals"])
    def lifecycle(signal_id: str, policy: AccessPolicy = Depends(entitlement)) -> dict[str, Any]:
        try:
            items = store.lifecycle(_signal_id(signal_id), policy=policy)
        except SignalNotFound as exc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="signal not found") from exc
        return {"items": [item.model_dump(mode="json") for item in items]}

    @app.get("/v1/results", response_model=SignalList, tags=["results"])
    def results(
        limit: int = Query(20, ge=1, le=100),
        policy: AccessPolicy = Depends(entitlement),
    ) -> SignalList:
        return store.recent_results(limit=limit, policy=policy)

    @app.get("/v1/track-record", response_model=TrackRecord, tags=["results"])
    def track_record() -> TrackRecord:
        return store.track_record()

    @app.get(
        "/v1/signals/{signal_id}/verification",
        response_model=VerificationRecord,
        tags=["verification"],
    )
    def verification(signal_id: str, policy: AccessPolicy = Depends(entitlement)) -> VerificationRecord:
        try:
            return store.verification(_signal_id(signal_id), policy=policy)
        except SignalNotFound as exc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="signal not found") from exc

    @app.post(
        "/internal/v1/publications",
        response_model=IngestResult,
        dependencies=[Depends(require_ingest)],
        tags=["internal"],
    )
    def ingest(batch: PublicationBatch) -> IngestResult:
        try:
            return store.ingest(batch)
        except PublicationConflict as exc:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc

    return app


def main() -> None:
    try:
        import uvicorn
    except ImportError as exc:  # pragma: no cover
        raise SystemExit("API server dependencies are not installed") from exc

    host = os.getenv("CURREN_API_HOST", "127.0.0.1")
    port = int(os.getenv("CURREN_API_PORT", "8000"))
    uvicorn.run(create_app(), host=host, port=port, log_level=os.getenv("CURREN_LOG_LEVEL", "info"))


def _parse_api_keys(raw: str) -> dict[str, str]:
    try:
        payload = json.loads(raw or "{}")
    except json.JSONDecodeError as exc:
        raise ValueError("CURREN_API_KEYS_JSON must be valid JSON") from exc
    if not isinstance(payload, dict):
        raise ValueError("CURREN_API_KEYS_JSON must be a JSON object")
    parsed: dict[str, str] = {}
    for key, value in payload.items():
        if not isinstance(key, str) or len(key) < 8:
            raise ValueError("API keys must be strings with at least 8 characters")
        tier = value.get("tier") if isinstance(value, dict) else value
        if tier not in _ALLOWED_TIERS:
            raise ValueError("API key tiers must be 'premium' or 'agent'")
        parsed[key] = str(tier)
    return parsed


def _bearer_token(header: str) -> str:
    scheme, separator, token = header.partition(" ")
    if separator != " " or scheme.lower() != "bearer" or not token.strip():
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Bearer token required")
    return token.strip()


def _clean_secret(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = value.strip()
    return cleaned or None


def _symbol(value: str) -> str:
    normalized = value.strip().upper()
    if not _SYMBOL_RE.fullmatch(normalized):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="invalid symbol")
    return normalized


def _signal_id(value: str) -> str:
    normalized = value.strip()
    if not normalized or len(normalized) > 128 or "/" in normalized or ".." in normalized:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="invalid signal id")
    return normalized


app = create_app()


if __name__ == "__main__":
    main()
