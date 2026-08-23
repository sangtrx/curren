from __future__ import annotations

from curren.models import Signal, TrackRecord, VerificationRecord


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
        }
    )

    assert signal.entry == 4800.0
    assert signal.targets[0].price == 4740.0


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


def test_verification_record_requires_hash_and_timestamp() -> None:
    record = VerificationRecord.model_validate(
        {
            "signal_id": "crn_sig_42",
            "published_at": "2026-08-23T10:00:00Z",
            "content_hash": "sha256:abc123",
            "verified": True,
            "immutable": True,
            "record_version": "signal-public.v1",
        }
    )

    assert record.verified is True
    assert record.content_hash.startswith("sha256:")
