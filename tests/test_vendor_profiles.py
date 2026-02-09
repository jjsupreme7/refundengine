from __future__ import annotations

import json

import refund_engine.vendor_profiles as vp_module


def _reset_cache():
    vp_module._CACHE = None
    vp_module._VENDOR_NAMES = []


def _make_profile_json(vendors: dict) -> str:
    return json.dumps({"vendors": vendors})


SAMPLE_VENDOR = {
    "ACME CORP": {
        "total_rows": 50,
        "claimed_count": 40,
        "pass_count": 5,
        "dominant_tax_category": {"value": "License", "count": 30},
        "dominant_product_type": {"value": "DAS", "count": 25},
        "dominant_refund_basis": {"value": "MPU", "count": 35},
        "dominant_methodology": {"value": "User location", "count": 28},
        "sample_descriptions": ["Cloud software license", "SaaS platform"],
    }
}


def test_load_vendor_profile_returns_none_for_unknown(tmp_path, monkeypatch):
    _reset_cache()
    monkeypatch.setattr(vp_module, "_PROFILES_PATH", tmp_path / "profiles.json")
    (tmp_path / "profiles.json").write_text(_make_profile_json(SAMPLE_VENDOR))
    result = vp_module.load_vendor_profile("TOTALLY UNKNOWN VENDOR XYZ")
    assert result is None
    _reset_cache()


def test_load_vendor_profile_exact_match(tmp_path, monkeypatch):
    _reset_cache()
    monkeypatch.setattr(vp_module, "_PROFILES_PATH", tmp_path / "profiles.json")
    (tmp_path / "profiles.json").write_text(_make_profile_json(SAMPLE_VENDOR))
    result = vp_module.load_vendor_profile("ACME CORP")
    assert result is not None
    assert "ACME CORP" in result
    assert "License (30 rows)" in result
    assert "MPU (35 rows)" in result
    assert "User location (28 rows)" in result
    assert "Cloud software license" in result
    assert "NOTE:" in result
    _reset_cache()


def test_load_vendor_profile_fuzzy_match(tmp_path, monkeypatch):
    _reset_cache()
    monkeypatch.setattr(vp_module, "_PROFILES_PATH", tmp_path / "profiles.json")
    (tmp_path / "profiles.json").write_text(_make_profile_json(SAMPLE_VENDOR))
    result = vp_module.load_vendor_profile("ACME CORP INC")
    assert result is not None
    assert "ACME CORP" in result
    _reset_cache()


def test_load_vendor_profile_missing_file(tmp_path, monkeypatch):
    _reset_cache()
    monkeypatch.setattr(vp_module, "_PROFILES_PATH", tmp_path / "nonexistent.json")
    result = vp_module.load_vendor_profile("ACME CORP")
    assert result is None
    _reset_cache()


SAMPLE_VENDOR_WITH_EXAMPLES = {
    "ACME CORP": {
        **SAMPLE_VENDOR["ACME CORP"],
        "few_shot_examples": [
            {
                "description": "Cloud SaaS license",
                "tax_category": "License",
                "refund_basis": "MPU",
                "methodology": "User location",
                "product_type": "License",
                "notes": "SaaS used by employees nationwide, applied MPU headcount allocation",
            },
            {
                "description": "Network equipment maintenance",
                "tax_category": "Hardware maintenance",
                "refund_basis": "Partial OOS services",
                "methodology": "Equipment location",
                "product_type": "HW maintenance",
                "notes": "",
            },
        ],
    }
}


def test_load_vendor_profile_includes_few_shot_examples(tmp_path, monkeypatch):
    _reset_cache()
    monkeypatch.setattr(vp_module, "_PROFILES_PATH", tmp_path / "profiles.json")
    (tmp_path / "profiles.json").write_text(_make_profile_json(SAMPLE_VENDOR_WITH_EXAMPLES))
    result = vp_module.load_vendor_profile("ACME CORP")
    assert result is not None
    assert "Analyst decision examples" in result
    assert 'Ex1: "Cloud SaaS license"' in result
    assert "tax_category=License" in result
    assert "refund_basis=MPU" in result
    assert "Analyst:" in result  # notes appear for Ex1
    assert 'Ex2: "Network equipment maintenance"' in result
    _reset_cache()
