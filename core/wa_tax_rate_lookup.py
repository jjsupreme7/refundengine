"""
Washington State Tax Rate Lookup
================================

Uses the WA DOR GIS API to look up official tax rates by city/ZIP.

API Documentation:
https://dor.wa.gov/taxes-rates/retail-sales-tax/destination-based-sales-tax-and-streamlined-sales-tax/wa-sales-tax-rate-lookup-url-interface

Usage:
    from core.wa_tax_rate_lookup import lookup_tax_rate, compare_rate

    # Look up current rate
    result = lookup_tax_rate(city="Tacoma", zip_code="98401")
    print(result)  # {'rate': 0.103, 'location_code': '2717', 'result_code': 5}

    # Compare charged rate vs official
    comparison = compare_rate(city="Tacoma", zip_code="98401", charged_rate=8.5)
    print(comparison)  # {'correct_rate': 10.3, 'charged_rate': 8.5, 'difference': -1.8, 'is_overcharge': False}
"""

import requests
import urllib.parse
import re
from typing import Optional
from functools import lru_cache


# Cache results to avoid repeated API calls
@lru_cache(maxsize=500)
def lookup_tax_rate(
    city: str = "",
    zip_code: str = "",
    address: str = ""
) -> dict:
    """
    Look up the official WA tax rate for a location.

    Args:
        city: City name (e.g., "Tacoma")
        zip_code: ZIP code (e.g., "98401" or "98401-1234")
        address: Street address (optional, improves accuracy)

    Returns:
        Dict with:
            - rate: Tax rate as decimal (e.g., 0.103 = 10.3%)
            - rate_percent: Tax rate as percentage (e.g., 10.3)
            - location_code: WA DOR location code
            - result_code: API result code (0-9)
            - error: Error message if lookup failed

    Example:
        >>> lookup_tax_rate(city="Tacoma", zip_code="98401")
        {'rate': 0.103, 'rate_percent': 10.3, 'location_code': '2717', 'result_code': 5}
    """
    if not city and not zip_code:
        return {"error": "Must provide city or zip_code"}

    # Build URL
    base_url = "https://webgis.dor.wa.gov/webapi/AddressRates.aspx"
    params = {
        "output": "text",
        "addr": address or "",
        "city": city or "",
        "zip": zip_code or "",
    }

    url = f"{base_url}?{'&'.join(f'{k}={urllib.parse.quote(str(v))}' for k, v in params.items())}"

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()

        # Parse response: "LocationCode=2717 Rate=.103 ResultCode=5"
        text = response.text.strip()

        # Extract values using regex
        location_match = re.search(r'LocationCode=(\d+)', text)
        rate_match = re.search(r'Rate=([.\d]+)', text)
        result_match = re.search(r'ResultCode=(\d+)', text)

        if rate_match:
            rate = float(rate_match.group(1))
            return {
                "rate": rate,
                "rate_percent": round(rate * 100, 2),
                "location_code": location_match.group(1) if location_match else None,
                "result_code": int(result_match.group(1)) if result_match else None,
            }
        else:
            return {"error": f"Could not parse response: {text}"}

    except requests.RequestException as e:
        return {"error": f"API request failed: {e}"}


def compare_rate(
    city: str = "",
    zip_code: str = "",
    charged_rate: float = 0,
    address: str = ""
) -> dict:
    """
    Compare a charged tax rate against the official WA rate.

    Args:
        city: City name
        zip_code: ZIP code
        charged_rate: The rate that was charged (as percentage, e.g., 10.1)
        address: Street address (optional)

    Returns:
        Dict with:
            - correct_rate: Official WA rate (percentage)
            - charged_rate: Rate that was charged (percentage)
            - difference: charged - correct (positive = overcharge)
            - is_overcharge: True if vendor charged too much
            - is_undercharge: True if vendor charged too little
            - refund_potential: True if difference > 0.1%
            - error: Error message if lookup failed

    Example:
        >>> compare_rate(city="Tacoma", zip_code="98401", charged_rate=10.5)
        {'correct_rate': 10.3, 'charged_rate': 10.5, 'difference': 0.2, 'is_overcharge': True}
    """
    lookup = lookup_tax_rate(city=city, zip_code=zip_code, address=address)

    if "error" in lookup:
        return {"error": lookup["error"], "charged_rate": charged_rate}

    correct_rate = lookup["rate_percent"]
    difference = round(charged_rate - correct_rate, 2)

    return {
        "correct_rate": correct_rate,
        "charged_rate": charged_rate,
        "difference": difference,
        "is_overcharge": difference > 0.1,  # Allow 0.1% tolerance for rounding
        "is_undercharge": difference < -0.1,
        "refund_potential": difference > 0.1,  # Only overcharges can be refunded
        "location_code": lookup.get("location_code"),
    }


def batch_lookup(locations: list) -> dict:
    """
    Look up rates for multiple locations.

    Args:
        locations: List of dicts with 'city' and/or 'zip_code' keys

    Returns:
        Dict mapping (city, zip) to rate info

    Example:
        >>> batch_lookup([
        ...     {'city': 'Tacoma', 'zip_code': '98401'},
        ...     {'city': 'Seattle', 'zip_code': '98101'},
        ... ])
    """
    results = {}
    for loc in locations:
        city = loc.get("city", "")
        zip_code = loc.get("zip_code", loc.get("zip", ""))
        key = (city, zip_code)
        results[key] = lookup_tax_rate(city=city, zip_code=zip_code)
    return results


# Convenience function for the analyzer
def get_correct_rate(city: str, zip_code: str) -> Optional[float]:
    """
    Simple function to get the correct tax rate percentage.

    Returns None if lookup fails.

    Example:
        >>> get_correct_rate("Tacoma", "98401")
        10.3
    """
    result = lookup_tax_rate(city=city, zip_code=zip_code)
    return result.get("rate_percent")


if __name__ == "__main__":
    # Test the API
    print("=== WA Tax Rate Lookup Test ===\n")

    test_locations = [
        ("Tacoma", "98401"),
        ("Kent", "98032"),
        ("Seattle", "98101"),
        ("Wenatchee", "98801"),
        ("Spokane", "99201"),
    ]

    for city, zip_code in test_locations:
        result = lookup_tax_rate(city=city, zip_code=zip_code)
        print(f"{city} ({zip_code}): {result.get('rate_percent', 'ERROR')}%")

    print("\n=== Rate Comparison Test ===\n")

    # Test comparing charged vs correct
    comparison = compare_rate(city="Tacoma", zip_code="98401", charged_rate=10.5)
    print(f"Tacoma charged 10.5%: {comparison}")

    comparison = compare_rate(city="Tacoma", zip_code="98401", charged_rate=8.5)
    print(f"Tacoma charged 8.5%: {comparison}")
