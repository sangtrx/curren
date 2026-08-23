from __future__ import annotations

import pytest
from pydantic import ValidationError

from curren.models import PublicationBatch, Signal, TrackRecord, VerificationRecord, normalize_signal_id


def test_signal_contract_accepts_exact_levels_when_entitled() -> None:
    signal = Signal.model_validate(
        {
            "id": "crn_sig_42",
            "symbol": "ETHUSDT",
            "side": "short",
            "status": "active",
            "published_at": "2026-08-23T10:00:00Z",
            "entry": 4800.0,
            "stop": 4860.0,
            "targets": [{"price": 4740.0, "status": "pending"}],
            "mark": 4780.0,
            "current_r": 0.33,
            "future_response_field": "ignored for forward compatibility",
        }
    )

    assert signal.entry == 4800.0
    assert signal.targets[0].price == 4740.0


def test_publication_batch_rejects_private_runtime_fields() -> None:
    with pytest.raises(ValidationError):
        PublicationBatch.model_validate(
            {
                "source": "curren-runtime",
                "generated_at": "2026-08-23T10:00:05Z",
                "signals": [
                    {
                        "id": "crn_sig_42",
                        "symbol": "ETHUSDT",
                        "side": "short",
                        "status": "active",
                        "published_at": "2026-08-23T10:00:00Z",
                        "entry": 4800.0,
                        "stop": 4860.0,
                        "targets": [{"price": 4740.0}],
                        "raw_source_message": "must be rejected",
                        "trade_intent": {"must": "not cross boundary"},
                    }
                ],
            }
        )


def test_publication_status_is_closed_set() -> None:
    with pytest.raises(ValidationError):
        PublicationBatch.model_validate(
            {
                "source": "curren-runtime",
                "generated_at": "2026-08-23T10:00:05Z",
                "signals": [
                    {
                        "id": "crn_sig_42",
                        "symbol": "ETHUSDT",
                        "side": "short",
                        "status": "closed_win",
                        "published_at": "2026-08-23T10:00:00Z",
                    }
                ],
            }
        )


def test_target_hit_state_requires_consistent_timestamp() -> None:
    base = {
        "source": "curren-runtime",
        "generated_at": "2026-08-23T10:05:00Z",
        "signals": [
            {
                "id": "crn_sig_42",
                "symbol": "ETHUSDT",
                "side": "short",
                "status": "active",
                "published_at": "2026-08-23T10:00:00Z",
                "targets": [{"price": 4740.0, "status": "hit"}],
            }
        ],
    }
    with pytest.raises(ValidationError):
        PublicationBatch.model_validate(base)

    base["signals"][0]["targets"] = [
        {"price": 4740.0, "status": "pending", "hit_at": "2026-08-23T10:04:00Z"}
    ]
    with pytest.raises(ValidationError):
        PublicationBatch.model_validate(base)


def test_closed_publication_requires_terminal_timestamp_and_result() -> None:
    with pytest.raises(ValidationError):
        PublicationBatch.model_validate(
            {
                "source": "curren-runtime",
                "generated_at": "2026-08-23T10:10:00Z",
                "signals": [
                    {
                        "id": "crn_sig_42",
                        "symbol": "ETHUSDT",
                        "side": "short",
                        "status": "closed",
                        "published_at": "2026-08-23T10:00:00Z",
                        "closed_at": "2026-08-23T10:09:00Z",
                    }
                ],
            }
        )


def test_signal_id_normalization_rejects_path_or_query_characters() -> None:
    assert normalize_signal_id(" crn_sig:42 ") == "crn_sig:42"
    for value in ("../secret", "sig/child", "sig?query", "sig#fragment", ""):
        with pytest.raises(ValueError):
            normalize_signal_id(value)


def test_track_record_does_not_require_profit_claims() -> None:
    record = TrackRecord.model_validate(
        {
            "sample_size": 0,
            "as_of": "2026-08-23T10:00:00Z",
            "methodology": "No closed public records yet",
        }
    )

    assert record.win_rate is None
    assert record.net_r is None


def test_verification_record_accepts_optional_terminal_outcome_proof() -> None:
    record = VerificationRecord.model_validate(
        {
            "signal_id": "crn_sig_42",
            "published_at": "2026-08-23T10:00:00Z",
            "recorded_at": "2026-08-23T10:00:01Z",
            "content_hash": "sha256:abc123",
            "verified": True,
            "immutable": True,
            "record_version": "signal-publication.v1",
            "outcome_content_hash": "sha256:def456",
            "outcome_verified": True,
            "outcome_record_version": "signal-outcome.v1",
            "outcome_recorded_at": "2026-08-23T10:10:01Z",
        }
    )

    assert record.verified is True
    assert record.outcome_verified is True
    assert record.content_hash.startswith("sha256:")
