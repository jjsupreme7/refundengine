from __future__ import annotations

from refund_engine.refund_calculator import _CACHE, calculate_refund
import refund_engine.refund_calculator as rc_module


def _reset_cache():
    rc_module._CACHE = None


def test_deterministic_nontaxable(tmp_path, monkeypatch):
    _reset_cache()
    monkeypatch.setattr(rc_module, "_CONFIG_PATH", tmp_path / "alloc.json")
    (tmp_path / "alloc.json").write_text(
        '{"Non-taxable": {"allocation_pct": 1.0}}'
    )
    amount, source = calculate_refund(5000.0, "Non-taxable", 3000.0)
    assert amount == 5000.0
    assert source == "calculated"
    _reset_cache()


def test_variable_falls_back(tmp_path, monkeypatch):
    _reset_cache()
    monkeypatch.setattr(rc_module, "_CONFIG_PATH", tmp_path / "alloc.json")
    (tmp_path / "alloc.json").write_text(
        '{"User location": {"allocation_pct": null}}'
    )
    amount, source = calculate_refund(5000.0, "User location", 3500.0)
    assert amount == 3500.0
    assert source == "estimated"
    _reset_cache()


def test_unknown_methodology(tmp_path, monkeypatch):
    _reset_cache()
    monkeypatch.setattr(rc_module, "_CONFIG_PATH", tmp_path / "alloc.json")
    (tmp_path / "alloc.json").write_text("{}")
    amount, source = calculate_refund(5000.0, "Unknown Method", 2000.0)
    assert amount == 2000.0
    assert source == "estimated"
    _reset_cache()


def test_negative_llm_estimate_clamped(tmp_path, monkeypatch):
    _reset_cache()
    monkeypatch.setattr(rc_module, "_CONFIG_PATH", tmp_path / "alloc.json")
    (tmp_path / "alloc.json").write_text("{}")
    amount, source = calculate_refund(5000.0, "Whatever", -100.0)
    assert amount == 0.0
    assert source == "estimated"
    _reset_cache()


def test_ship_to_location(tmp_path, monkeypatch):
    _reset_cache()
    monkeypatch.setattr(rc_module, "_CONFIG_PATH", tmp_path / "alloc.json")
    (tmp_path / "alloc.json").write_text(
        '{"Ship-to location": {"allocation_pct": 1.0}}'
    )
    amount, source = calculate_refund(12345.67, "Ship-to location", 0.0)
    assert amount == 12345.67
    assert source == "calculated"
    _reset_cache()


def test_mpu_calculation(tmp_path, monkeypatch):
    _reset_cache()
    monkeypatch.setattr(rc_module, "_CONFIG_PATH", tmp_path / "alloc.json")
    (tmp_path / "alloc.json").write_text(
        '{"MPU": {"allocation_pct": 0.6742}}'
    )
    amount, source = calculate_refund(10000.0, "MPU", 5000.0)
    assert amount == 6742.0
    assert source == "calculated"
    _reset_cache()


def test_normalization_in_calculator(tmp_path, monkeypatch):
    """'equipment location' (lowercase) should normalize to 'Equipment Location' for lookup."""
    _reset_cache()
    monkeypatch.setattr(rc_module, "_CONFIG_PATH", tmp_path / "alloc.json")
    (tmp_path / "alloc.json").write_text(
        '{"Equipment Location": {"allocation_pct": 0.7056}}'
    )
    amount, source = calculate_refund(10000.0, "equipment location", 5000.0)
    assert amount == 7056.0
    assert source == "calculated"
    _reset_cache()
