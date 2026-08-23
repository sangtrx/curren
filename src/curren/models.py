from __future__ import annotations

import math
import re
from datetime import UTC, datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

_SIGNAL_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")
_SYMBOL_RE = re.compile(r"^[A-Z0-9._-]{2,32}$")
_NAME_RE = re.compile(r"^[a-z0-9][a-z0-9._:-]{0,63}$")


class CurrenModel(BaseModel):
    """Forward-compatible model for data returned by the public API."""

    model_config = ConfigDict(extra="ignore")


class StrictCurrenModel(BaseModel):
    """Fail-closed model for private-runtime -> public publication input."""

    model_config = ConfigDict(extra="forbid")


class SignalSide(StrEnum):
    LONG = "long"
    SHORT = "short"


class SignalStatus(StrEnum):
    PENDING = "pending"
    ACTIVE = "active"
    CLOSED = "closed"
    EXPIRED = "expired"


TERMINAL_SIGNAL_STATUSES = frozenset({SignalStatus.CLOSED, SignalStatus.EXPIRED})


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
    outcome_content_hash: str | None = None
    outcome_verified: bool | None = None
    outcome_record_version: str | None = None
    outcome_recorded_at: datetime | None = None


class PublicSummary(CurrenModel):
    active_count: int = 0
    delayed_signals: list[Signal] = Field(default_factory=list)
    recent_results: list[Signal] = Field(default_factory=list)
    as_of: datetime


class PublicationTarget(StrictCurrenModel):
    price: float = Field(gt=0)
    status: str = Field(default="pending", min_length=1, max_length=32)
    hit_at: datetime | None = None

    @field_validator("price")
    @classmethod
    def finite_price(cls, value: float) -> float:
        return _finite(value, "target price")

    @field_validator("hit_at")
    @classmethod
    def aware_hit_at(cls, value: datetime | None) -> datetime | None:
        return _aware(value, "target hit_at")


class PublicationLifecycleEvent(StrictCurrenModel):
    event_type: str = Field(min_length=1, max_length=64)
    event_at: datetime
    price: float | None = Field(default=None, gt=0)
    r_multiple: float | None = None

    @field_validator("event_type")
    @classmethod
    def normalized_event_type(cls, value: str) -> str:
        normalized = value.strip().lower()
        if not _NAME_RE.fullmatch(normalized):
            raise ValueError("event_type must be a normalized lowercase identifier")
        return normalized

    @field_validator("event_at")
    @classmethod
    def aware_event_at(cls, value: datetime) -> datetime:
        return _aware(value, "lifecycle event_at")

    @field_validator("price")
    @classmethod
    def finite_event_price(cls, value: float | None) -> float | None:
        return _finite_optional(value, "lifecycle price")

    @field_validator("r_multiple")
    @classmethod
    def finite_event_r(cls, value: float | None) -> float | None:
        return _finite_optional(value, "lifecycle r_multiple")


class PublicationSignal(StrictCurrenModel):
    """Sanitized projection accepted from the private Curren runtime.

    The ingestion contract is deliberately strict: unknown fields are rejected
    rather than silently crossing the private/public boundary.
    """

    id: str = Field(min_length=1, max_length=128)
    symbol: str = Field(min_length=2, max_length=32)
    side: SignalSide
    status: SignalStatus
    published_at: datetime
    public_available_at: datetime | None = None
    entry: float | None = Field(default=None, gt=0)
    stop: float | None = Field(default=None, gt=0)
    targets: list[PublicationTarget] = Field(default_factory=list, max_length=16)
    mark: float | None = Field(default=None, gt=0)
    current_r: float | None = None
    peak_r: float | None = None
    realized_r: float | None = None
    closed_at: datetime | None = None
    exit_reason: str | None = Field(default=None, max_length=128)
    lifecycle: list[PublicationLifecycleEvent] = Field(default_factory=list, max_length=512)

    @field_validator("id")
    @classmethod
    def valid_id(cls, value: str) -> str:
        normalized = value.strip()
        if not _SIGNAL_ID_RE.fullmatch(normalized):
            raise ValueError("signal id contains unsupported characters")
        return normalized

    @field_validator("symbol")
    @classmethod
    def normalized_symbol(cls, value: str) -> str:
        normalized = value.strip().upper()
        if not _SYMBOL_RE.fullmatch(normalized):
            raise ValueError("invalid symbol")
        return normalized

    @field_validator("published_at", "public_available_at", "closed_at")
    @classmethod
    def aware_signal_times(cls, value: datetime | None, info) -> datetime | None:
        return _aware(value, info.field_name)

    @field_validator("entry", "stop", "mark")
    @classmethod
    def finite_positive_optional(cls, value: float | None, info) -> float | None:
        return _finite_optional(value, info.field_name)

    @field_validator("current_r", "peak_r", "realized_r")
    @classmethod
    def finite_r_values(cls, value: float | None, info) -> float | None:
        return _finite_optional(value, info.field_name)

    @field_validator("exit_reason")
    @classmethod
    def normalized_exit_reason(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip().lower()
        if not normalized:
            return None
        if not _NAME_RE.fullmatch(normalized):
            raise ValueError("exit_reason must be a normalized lowercase identifier")
        return normalized

    @model_validator(mode="after")
    def validate_timeline_and_terminal_state(self) -> PublicationSignal:
        terminal = self.status in TERMINAL_SIGNAL_STATUSES
        if self.public_available_at is not None and self.public_available_at < self.published_at:
            raise ValueError("public_available_at cannot be before published_at")
        if terminal and self.closed_at is None:
            raise ValueError("terminal signals require closed_at")
        if not terminal and (self.closed_at is not None or self.realized_r is not None or self.exit_reason is not None):
            raise ValueError("non-terminal signals cannot contain terminal outcome fields")
        if self.status == SignalStatus.CLOSED and self.realized_r is None:
            raise ValueError("closed signals require realized_r")
        if self.closed_at is not None and self.closed_at < self.published_at:
            raise ValueError("closed_at cannot be before published_at")

        for target in self.targets:
            if target.hit_at is not None:
                if target.hit_at < self.published_at:
                    raise ValueError("target hit_at cannot be before published_at")
                if self.closed_at is not None and target.hit_at > self.closed_at:
                    raise ValueError("target hit_at cannot be after closed_at")
        for event in self.lifecycle:
            if event.event_at < self.published_at:
                raise ValueError("lifecycle event_at cannot be before published_at")
            if self.closed_at is not None and event.event_at > self.closed_at:
                raise ValueError("lifecycle event_at cannot be after closed_at")
        return self


class PublicationBatch(StrictCurrenModel):
    source: str = Field(min_length=1, max_length=64)
    generated_at: datetime
    signals: list[PublicationSignal] = Field(default_factory=list, max_length=500)

    @field_validator("source")
    @classmethod
    def normalized_source(cls, value: str) -> str:
        normalized = value.strip().lower()
        if not _NAME_RE.fullmatch(normalized):
            raise ValueError("source must be a normalized lowercase identifier")
        return normalized

    @field_validator("generated_at")
    @classmethod
    def aware_generated_at(cls, value: datetime) -> datetime:
        return _aware(value, "generated_at")

    @model_validator(mode="after")
    def generated_after_projection(self) -> PublicationBatch:
        for signal in self.signals:
            latest = signal.closed_at or signal.published_at
            if signal.lifecycle:
                latest = max(latest, max(event.event_at for event in signal.lifecycle))
            for target in signal.targets:
                if target.hit_at is not None:
                    latest = max(latest, target.hit_at)
            if self.generated_at < latest:
                raise ValueError(f"generated_at predates projected state for {signal.id}")
        return self


class IngestResult(CurrenModel):
    accepted: int = 0
    inserted: int = 0
    updated: int = 0
    stale_ignored: int = 0
    lifecycle_events_inserted: int = 0
    outcome_records_inserted: int = 0


class HealthStatus(CurrenModel):
    status: str
    signals: int
    ingestion_enabled: bool


def _aware(value: datetime | None, field: str) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field} must include a timezone")
    return value.astimezone(UTC)


def _finite(value: float, field: str) -> float:
    number = float(value)
    if not math.isfinite(number):
        raise ValueError(f"{field} must be finite")
    return number


def _finite_optional(value: float | None, field: str) -> float | None:
    return None if value is None else _finite(value, field)
