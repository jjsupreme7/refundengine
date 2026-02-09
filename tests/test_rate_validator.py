from __future__ import annotations

import refund_engine.rate_validator as rv_module
from refund_engine.rate_validator import validate_rate


def _reset_cache():
    rv_module._CACHE = None


def test_wa_rate_match():
    _reset_cache()
    result = validate_rate(0.1035, "WA", 10000.0, 1035.0)
    assert result.is_wa is True
    assert result.rate_ok is True
    assert result.closest_wa_rate is not None
    assert abs(result.closest_wa_rate - 0.1035) < 0.003
    assert "matches" in result.message.lower() or "Rate matches" in result.message
    _reset_cache()


def test_wa_rate_mismatch():
    # Use a sparse mock table so we can create a genuine mismatch
    rv_module._CACHE = [(0.1020, "Bellevue"), (0.1035, "Seattle")]
    result = validate_rate(0.0850, "WA", 10000.0, 850.0)
    assert result.is_wa is True
    assert result.rate_ok is False
    assert result.rate_variance is not None
    assert "MISMATCH" in result.message
    _reset_cache()


def test_non_wa_skipped():
    _reset_cache()
    result = validate_rate(0.0625, "CA", 10000.0, 625.0)
    assert result.is_wa is False
    assert result.rate_ok is True
    assert "Non-WA" in result.message
    _reset_cache()


def test_anomalous_rate():
    _reset_cache()
    result = validate_rate(0.02, "WA", 10000.0, 200.0)
    assert result.is_wa is True
    assert result.rate_ok is False
    assert "ANOMALY" in result.message
    _reset_cache()


def test_none_inputs():
    _reset_cache()
    result = validate_rate(None, None, None, None)
    assert result.is_wa is False
    assert result.rate_ok is True
    assert "No rate data" in result.message
    _reset_cache()


def test_tax_calc_check():
    _reset_cache()
    # tax_base * rate = 10000 * 0.1035 = 1035, but tax_amount is 800 (big discrepancy)
    result = validate_rate(0.1035, "WA", 10000.0, 800.0)
    assert result.is_wa is True
    assert result.tax_calc_ok is False
    assert "tax_base" in result.message.lower() or "calculation" in result.message.lower()
    _reset_cache()
