from __future__ import annotations

import hmac
import ipaddress
import json
import os
import re
from dataclasses import dataclass
from datetime import timedelta
from typing import Any

from fastapi import Depends, FastAPI, Header, HTTPException, Query, Request, Response, status
from fastapi.responses import JSONResponse

from curren.models import (
    HealthStatus,
    IngestResult,
    PublicationBatch,
    PublicSummary,
    Signal,
    SignalList,
    SignalStatus,
    TrackRecord,
    VerificationRecord,
)
from curren.rate_limit import FixedWindowRateLimiter, RateLimitDecision, token_identity
from curren.store import AccessPolicy, PublicationConflict, ReadStore, SignalNotFound

_SYMBOL_RE = re.compile(r"^[A-Z0-9._-]{2,32}$")
_ALLOWED_TIERS = frozenset({"premium", "agent"})


@dataclass(frozen=True)
class ServerConfig:
    database_path: str
    ingest_token: str | None
    api_keys: dict[str, str]
    public_delay_seconds: int
    rate_limit_window_seconds: int
    public_rate_limit: int
    authenticated_rate_limit: int
    ingest_rate_limit: int
    trusted_proxy_networks: tuple[ipaddress.IPv4Network | ipaddress.IPv6Network, ...]

    @classmethod
    def from_env(cls) -> ServerConfig:
        return cls(
            database_path=os.getenv("CURREN_DB_PATH", "./.local/curren.db"),
            ingest_token=_clean_secret(os.getenv("CURREN_INGEST_TOKEN")),
            api_keys=_parse_api_keys(os.getenv("CURREN_API_KEYS_JSON", "{}")),
            public_delay_seconds=max(0, int(os.getenv("CURREN_PUBLIC_DELAY_SECONDS", "1800"))),
            rate_limit_window_seconds=_positive_int_env("CURREN_RATE_LIMIT_WINDOW_SECONDS", 60),
            public_rate_limit=_positive_int_env("CURREN_PUBLIC_RATE_LIMIT", 60),
            authenticated_rate_limit=_positive_int_env("CURREN_AUTH_RATE_LIMIT", 300),
            ingest_rate_limit=_positive_int_env("CURREN_INGEST_RATE_LIMIT", 120),
            trusted_proxy_networks=_parse_trusted_proxy_networks(os.getenv("CURREN_TRUSTED_PROXY_IPS", "")),
        )


def create_app(
    *,
    database_path: str | None = None,
    ingest_token: str | None = None,
    api_keys: dict[str, str] | None = None,
    public_delay_seconds: int | None = None,
    rate_limit_window_seconds: int | None = None,
    public_rate_limit: int | None = None,
    authenticated_rate_limit: int | None = None,
    ingest_rate_limit: int | None = None,
    trusted_proxy_ips: str | None = None,
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
        rate_limit_window_seconds=_positive_int(rate_limit_window_seconds, environment.rate_limit_window_seconds),
        public_rate_limit=_positive_int(public_rate_limit, environment.public_rate_limit),
        authenticated_rate_limit=_positive_int(authenticated_rate_limit, environment.authenticated_rate_limit),
        ingest_rate_limit=_positive_int(ingest_rate_limit, environment.ingest_rate_limit),
        trusted_proxy_networks=(
            _parse_trusted_proxy_networks(trusted_proxy_ips)
            if trusted_proxy_ips is not None
            else environment.trusted_proxy_networks
        ),
    )
    store = ReadStore(config.database_path, public_delay_seconds=config.public_delay_seconds)
    store.initialize()
    limiter = FixedWindowRateLimiter(window_seconds=config.rate_limit_window_seconds)

    app = FastAPI(
        title="Curren API",
        version="0.3.0",
        description=(
            "Read-only trading-intelligence API backed by sanitized publications from the private Curren runtime. "
            "Public clients cannot execute trades or access private runtime state."
        ),
    )
    app.state.store = store
    app.state.config = config
    app.state.rate_limiter = limiter

    @app.middleware("http")
    async def request_policy(request: Request, call_next: Any) -> Response:
        decision = _request_rate_limit(request, config=config, limiter=limiter)
        if decision is not None and not decision.allowed:
            response: Response = JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={"detail": "rate limit exceeded"},
                headers={"Retry-After": str(decision.retry_after_seconds)},
            )
        else:
            response = await call_next(request)

        if decision is not None:
            response.headers["X-RateLimit-Limit"] = str(decision.limit)
            response.headers["X-RateLimit-Remaining"] = str(decision.remaining)
            response.headers["X-RateLimit-Reset-After"] = str(decision.retry_after_seconds)
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
        status_filter: SignalStatus = Query(SignalStatus.ACTIVE, alias="status"),
        symbol: str | None = Query(default=None, min_length=2, max_length=32),
        limit: int = Query(20, ge=1, le=100),
        policy: AccessPolicy = Depends(entitlement),
    ) -> SignalList:
        normalized_symbol = _symbol(symbol) if symbol else None
        return store.list_signals(status=status_filter.value, symbol=normalized_symbol, limit=limit, policy=policy)

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
            return store.ingest(_enforce_public_delay(batch, config.public_delay_seconds))
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


def _request_rate_limit(
    request: Request,
    *,
    config: ServerConfig,
    limiter: FixedWindowRateLimiter,
) -> RateLimitDecision | None:
    path = request.url.path
    if not (path.startswith("/v1/") or path.startswith("/internal/")):
        return None

    peer = _rate_limit_peer(request, config.trusted_proxy_networks)
    token = _optional_bearer_token(request.headers.get("Authorization"))
    if path.startswith("/internal/"):
        identity = f"peer:{peer}"
        if token and config.ingest_token and hmac.compare_digest(token, config.ingest_token):
            identity = f"token:{token_identity(token)}"
        return limiter.check(scope="ingest", identity=identity, limit=config.ingest_rate_limit)

    if token:
        for configured_key in config.api_keys:
            if hmac.compare_digest(token, configured_key):
                return limiter.check(
                    scope="authenticated",
                    identity=f"token:{token_identity(token)}",
                    limit=config.authenticated_rate_limit,
                )
    return limiter.check(scope="public", identity=f"peer:{peer}", limit=config.public_rate_limit)


def _rate_limit_peer(
    request: Request,
    trusted_proxy_networks: tuple[ipaddress.IPv4Network | ipaddress.IPv6Network, ...],
) -> str:
    direct_peer = request.client.host if request.client and request.client.host else "unknown"
    if not trusted_proxy_networks or not _address_in_networks(direct_peer, trusted_proxy_networks):
        return direct_peer

    forwarded = request.headers.get("X-Forwarded-For", "")
    if not forwarded:
        return direct_peer
    candidate = forwarded.split(",", 1)[0].strip()
    try:
        return ipaddress.ip_address(candidate).compressed
    except ValueError:
        return direct_peer


def _address_in_networks(
    address: str,
    networks: tuple[ipaddress.IPv4Network | ipaddress.IPv6Network, ...],
) -> bool:
    try:
        parsed = ipaddress.ip_address(address)
    except ValueError:
        return False
    return any(parsed.version == network.version and parsed in network for network in networks)


def _parse_trusted_proxy_networks(
    raw: str,
) -> tuple[ipaddress.IPv4Network | ipaddress.IPv6Network, ...]:
    networks: list[ipaddress.IPv4Network | ipaddress.IPv6Network] = []
    for item in raw.split(","):
        value = item.strip()
        if not value:
            continue
        try:
            networks.append(ipaddress.ip_network(value, strict=False))
        except ValueError as exc:
            raise ValueError(f"invalid trusted proxy IP/network: {value}") from exc
    return tuple(networks)


def _enforce_public_delay(batch: PublicationBatch, delay_seconds: int) -> PublicationBatch:
    delay = timedelta(seconds=max(0, int(delay_seconds)))
    signals = []
    for signal in batch.signals:
        floor = signal.published_at + delay
        requested = signal.public_available_at
        public_available_at = max(requested, floor) if requested is not None else floor
        signals.append(signal.model_copy(update={"public_available_at": public_available_at}))
    return batch.model_copy(update={"signals": signals})


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
    token = _optional_bearer_token(header)
    if token is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Bearer token required")
    return token


def _optional_bearer_token(header: str | None) -> str | None:
    if header is None:
        return None
    scheme, separator, token = header.partition(" ")
    if separator != " " or scheme.lower() != "bearer" or not token.strip():
        return None
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


def _positive_int(value: int | None, fallback: int) -> int:
    resolved = fallback if value is None else int(value)
    if resolved < 1:
        raise ValueError("rate-limit values must be positive integers")
    return resolved


def _positive_int_env(name: str, default: int) -> int:
    raw = os.getenv(name)
    return _positive_int(int(raw) if raw is not None else None, default)


app = create_app()


if __name__ == "__main__":
    main()
