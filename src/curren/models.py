from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class CurrenModel(BaseModel):
    model_config = ConfigDict(extra="ignore")


class SignalSide(StrEnum):
    LONG = "long"
    SHORT = "short"


class SignalStatus(StrEnum):
    PENDING = "pending"
    ACTIVE = "active"
    CLOSED = "closed"
    EXPIRED = "expired"


class Target(CurrenModel):
    price: float | None = None
    status: str = "pending"
    hit_at: datetime | None = None


class LifecycleEvent(CurrenModel):
    event_type: str
    event_at: datetime
    price: float | None = None
    r_multiple: float | None = None


class Signal(CurrenModel):
    """External Curren signal contract.

    Exact trade levels are optional by design. The API may omit them for a public
    or delayed entitlement. Clients must never reconstruct restricted fields.
    """

    id: str
    symbol: str
    side: SignalSide
    status: SignalStatus | str
    published_at: datetime
    available_at: datetime | None = None
    entry: float | None = None
    stop: float | None = None
    targets: list[Target] = Field(default_factory=list)
    mark: float | None = None
    current_r: float | None = None
    peak_r: float | None = None
    realized_r: float | None = None
    closed_at: datetime | None = None
    exit_reason: str | None = None
    access: str | None = None


class SignalList(CurrenModel):
    items: list[Signal] = Field(default_factory=list)
    next_cursor: str | None = None


class TrackRecord(CurrenModel):
    sample_size: int
    wins: int | None = None
    losses: int | None = None
    breakeven: int | None = None
    win_rate: float | None = None
    net_r: float | None = None
    average_r: float | None = None
    as_of: datetime
    methodology: str | None = None


class VerificationRecord(CurrenModel):
    signal_id: str
    published_at: datetime
    content_hash: str
    verified: bool
    immutable: bool | None = None
    record_version: str | None = None
    recorded_at: datetime | None = None


class PublicSummary(CurrenModel):
    active_count: int = 0
    delayed_signals: list[Signal] = Field(default_factory=list)
    recent_results: list[Signal] = Field(default_factory=list)
    as_of: datetime


class PublicationSignal(CurrenModel):
    """Full sanitized projection accepted from the private Curren runtime.

    This contract intentionally contains no raw source messages, AI features,
    execution state, account data, exchange credentials, or operator metadata.
    """

    id: str
    symbol: str
    side: SignalSide
    status: str
    published_at: datetime
    public_available_at: datetime | None = None
    entry: float | None = None
    stop: float | None = None
    targets: list[Target] = Field(default_factory=list)
    mark: float | None = None
    current_r: float | None = None
    peak_r: float | None = None
    realized_r: float | None = None
    closed_at: datetime | None = None
    exit_reason: str | None = None
    lifecycle: list[LifecycleEvent] = Field(default_factory=list)


class PublicationBatch(CurrenModel):
    source: str = Field(min_length=1, max_length=64)
    generated_at: datetime
    signals: list[PublicationSignal] = Field(default_factory=list, max_length=500)


class IngestResult(CurrenModel):
    accepted: int = 0
    inserted: int = 0
    updated: int = 0
    lifecycle_events_inserted: int = 0


class HealthStatus(CurrenModel):
    status: str
    signals: int
    ingestion_enabled: bool
