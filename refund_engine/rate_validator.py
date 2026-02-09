from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from refund_engine.constants import PROJECT_ROOT

_RATE_TABLE_PATH = PROJECT_ROOT / "data" / "wa_rates" / "Q424_Excel_LSU-rates.xlsx"

# (combined_rate, location_name) tuples, loaded once
_CACHE: list[tuple[float, str]] | None = None

# Plausible WA combined rate range (state 6.5% + local 1%–4.1%)
_MIN_WA_RATE = 0.070
_MAX_WA_RATE = 0.110
_MATCH_TOLERANCE = 0.002  # 0.2 percentage points
_TAX_CALC_TOLERANCE = 0.05  # 5% relative tolerance


@dataclass(frozen=True)
class RateValidation:
    jurisdiction: str | None
    actual_rate: float | None
    is_wa: bool
    closest_wa_rate: float | None
    closest_location: str | None
    rate_variance: float | None
    rate_ok: bool
    tax_calc_ok: bool
    message: str


def _load_rate_table() -> list[tuple[float, str]]:
    global _CACHE
    if _CACHE is not None:
        return _CACHE

    if not _RATE_TABLE_PATH.exists():
        _CACHE = []
        return _CACHE

    import pandas as pd

    df = pd.read_excel(_RATE_TABLE_PATH, skiprows=2)
    df.columns = ["Location", "County", "Location_Code", "Local_Rate", "State_Rate", "Combined_Rate"]
    df = df.dropna(subset=["Combined_Rate"])

    # Deduplicate by rate, keeping one representative location per unique rate
    seen: dict[float, str] = {}
    for _, row in df.iterrows():
        rate = float(row["Combined_Rate"])
        rate_rounded = round(rate, 4)
        if rate_rounded not in seen:
            seen[rate_rounded] = str(row["Location"]).strip()

    _CACHE = sorted(seen.items())
    return _CACHE


def _find_closest(actual_rate: float) -> tuple[float, str, float]:
    """Return (closest_rate, location, variance)."""
    table = _load_rate_table()
    if not table:
        return (0.0, "", actual_rate)

    best_rate, best_loc = table[0]
    best_diff = abs(actual_rate - best_rate)
    for rate, loc in table[1:]:
        diff = abs(actual_rate - rate)
        if diff < best_diff:
            best_rate, best_loc, best_diff = rate, loc, diff

    return (best_rate, best_loc, actual_rate - best_rate)


def validate_rate(
    rate: float | None,
    jurisdiction: str | None,
    tax_base: float | None,
    tax_amount: float | None,
) -> RateValidation:
    """Validate a row's tax rate against the WA DOR rate table."""
    if rate is None:
        return RateValidation(
            jurisdiction=jurisdiction, actual_rate=None, is_wa=False,
            closest_wa_rate=None, closest_location=None,
            rate_variance=None, rate_ok=True, tax_calc_ok=True,
            message="No rate data available.",
        )

    is_wa = (jurisdiction or "").strip().upper() == "WA"

    if not is_wa:
        return RateValidation(
            jurisdiction=jurisdiction, actual_rate=rate, is_wa=False,
            closest_wa_rate=None, closest_location=None,
            rate_variance=None, rate_ok=True, tax_calc_ok=True,
            message=f"Non-WA jurisdiction ({jurisdiction}), rate validation skipped.",
        )

    # Check tax calculation consistency
    tax_calc_ok = True
    if tax_base and tax_base > 0 and tax_amount is not None:
        expected_tax = tax_base * rate
        if expected_tax > 0:
            relative_diff = abs(tax_amount - expected_tax) / expected_tax
            tax_calc_ok = relative_diff <= _TAX_CALC_TOLERANCE

    # Rate outside plausible WA range
    if rate < _MIN_WA_RATE or rate > _MAX_WA_RATE:
        return RateValidation(
            jurisdiction=jurisdiction, actual_rate=rate, is_wa=True,
            closest_wa_rate=None, closest_location=None,
            rate_variance=None, rate_ok=False, tax_calc_ok=tax_calc_ok,
            message=f"RATE ANOMALY: {rate:.4%} is outside WA range ({_MIN_WA_RATE:.1%}-{_MAX_WA_RATE:.1%}).",
        )

    closest_rate, closest_loc, variance = _find_closest(rate)
    rate_ok = abs(variance) <= _MATCH_TOLERANCE

    parts = [f"Charged rate: {rate:.4%}"]
    parts.append(f"Closest WA rate: {closest_rate:.4%} ({closest_loc})")
    if rate_ok:
        parts.append("Status: Rate matches known WA rate.")
    else:
        parts.append(f"Status: RATE MISMATCH - variance of {variance:+.4%} from nearest WA rate.")
    if not tax_calc_ok:
        parts.append(f"Tax calculation: tax_base * rate does not match tax_amount (>5% difference).")

    return RateValidation(
        jurisdiction=jurisdiction, actual_rate=rate, is_wa=True,
        closest_wa_rate=closest_rate, closest_location=closest_loc,
        rate_variance=variance, rate_ok=rate_ok, tax_calc_ok=tax_calc_ok,
        message=" | ".join(parts),
    )
