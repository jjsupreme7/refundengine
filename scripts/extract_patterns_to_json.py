#!/usr/bin/env python3
"""
Extract Historical Patterns to JSON

Reads Excel file and extracts patterns to JSON files for later import.
NO database connection required - just extracts patterns to files.

Usage:
    python scripts/extract_patterns_to_json.py --file "Phase 2 Master Refunds.xlsx"

Output:
    - vendor_patterns.json
    - keyword_patterns.json
    - citation_patterns.json
    - category_patterns.json
"""

import argparse
import json
import os
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Dict, List

import pandas as pd

print("Starting pattern extraction...")


def extract_keywords_from_vendor(vendor_name: str) -> List[str]:
    """Extract keywords from vendor name for fuzzy matching."""
    if pd.isna(vendor_name) or vendor_name == "":
        return []

    stopwords = {
        "LLC",
        "INC",
        "CORP",
        "CO",
        "LTD",
        "LP",
        "CORPORATION",
        "COMPANY",
        "INCORPORATED",
        "LIMITED",
        "THE",
        "AND",
        "&",
    }

    words = str(vendor_name).upper().replace(",", " ").replace(".", " ").split()
    keywords = [w for w in words if w not in stopwords and len(w) > 1]

    return keywords


def extract_keywords_from_description(description: str) -> List[str]:
    """Extract meaningful keywords from product description."""
    if pd.isna(description) or description == "":
        return []

    stopwords = {
        "the",
        "a",
        "an",
        "and",
        "or",
        "but",
        "for",
        "of",
        "to",
        "in",
        "on",
        "at",
        "by",
        "from",
        "with",
        "is",
        "was",
        "are",
        "were",
    }

    text = str(description).lower()
    text = "".join(c if c.isalnum() or c.isspace() else " " for c in text)
    words = text.split()

    keywords = [w for w in words if w not in stopwords and len(w) > 2]

    return keywords


def auto_detect_columns(columns: List[str]) -> Dict[str, str]:
    """Auto-detect column names by keyword matching."""
    column_map = {}

    col_patterns = {
        "vendor": ["vendor", "supplier", "company name"],
        "description": ["description", "product", "item", "material description"],
        "final_decision": ["final decision", "decision", "determination"],
        "refund_basis": ["refund basis", "basis", "legal basis"],
        "tax_amount": ["tax", "amount", "sales tax", "use tax"],
        "vertex_category": ["vertex", "category"],
        "tax_category": ["tax category"],
        "material_group": ["material group"],
    }

    for col in columns:
        col_lower = str(col).lower()
        for key, patterns in col_patterns.items():
            if any(pattern in col_lower for pattern in patterns):
                if key not in column_map:
                    column_map[key] = col
                    break

    return column_map


def is_refund_decision(decision: str) -> bool:
    """Check if decision indicates a refund."""
    if pd.isna(decision) or decision == "":
        return False

    decision_upper = str(decision).upper()

    if "NO OPP" in decision_upper or "NO OPPORTUNITY" in decision_upper:
        return False

    refund_keywords = ["REFUND", "ADD TO CLAIM", "CLAIM", "ELIGIBLE"]
    return any(keyword in decision_upper for keyword in refund_keywords)


def main():
    parser = argparse.ArgumentParser(description="Extract historical patterns to JSON")
    parser.add_argument("--file", required=True, help="Path to Excel file")
    parser.add_argument(
        "--output-dir", default="extracted_patterns", help="Output directory"
    )

    args = parser.parse_args()

    if not os.path.exists(args.file):
        print(f"Error: File not found: {args.file}")
        sys.exit(1)

    # Create output directory
    os.makedirs(args.output_dir, exist_ok=True)

    print(f"\n{'='*70}")
    print(f"Reading Excel file: {args.file}")
    print(f"{'='*70}\n")

    # Read Excel file
    df = pd.read_excel(args.file)
    print(f"Total rows: {len(df)}")

    # Auto-detect columns
    column_map = auto_detect_columns(df.columns.tolist())
    print(f"\nDetected columns:")
    for key, col in column_map.items():
        print(f"  {key}: {col}")

    # Filter to analyzed rows only
    if "final_decision" not in column_map:
        print("\nError: Could not detect 'Final Decision' column")
        sys.exit(1)

    decision_col = column_map["final_decision"]
    analyzed_df = df[df[decision_col].notna() & (df[decision_col] != "")]
    print(f"\nAnalyzed rows (with Final Decision): {len(analyzed_df)}")

    # Extract patterns
    vendor_patterns = defaultdict(
        lambda: {
            "refund_count": 0,
            "no_opp_count": 0,
            "product_types": Counter(),
            "refund_bases": Counter(),
            "vendor_keywords": set(),
            "description_keywords": Counter(),
        }
    )

    keyword_patterns = defaultdict(
        lambda: {
            "refund_count": 0,
            "no_opp_count": 0,
            "refund_bases": Counter(),
            "keywords": set(),
        }
    )

    citation_patterns = defaultdict(
        lambda: {
            "usage_count": 0,
            "example_cases": [],
        }
    )

    category_patterns = defaultdict(
        lambda: {
            "refund_count": 0,
            "no_opp_count": 0,
            "refund_bases": Counter(),
        }
    )

    # Extract vendor patterns
    print("\nExtracting vendor patterns...")
    vendor_col = column_map.get("vendor")
    description_col = column_map.get("description")
    refund_basis_col = column_map.get("refund_basis")

    product_col = (
        column_map.get("vertex_category")
        or column_map.get("tax_category")
        or column_map.get("material_group")
        or column_map.get("description")
    )

    for idx, row in analyzed_df.iterrows():
        if vendor_col:
            vendor = str(row.get(vendor_col, "")).strip().upper()
            if vendor:
                decision = row.get(decision_col, "")
                is_refund = is_refund_decision(decision)

                if is_refund:
                    vendor_patterns[vendor]["refund_count"] += 1
                else:
                    vendor_patterns[vendor]["no_opp_count"] += 1

                # Extract vendor keywords
                vendor_keywords = extract_keywords_from_vendor(vendor)
                vendor_patterns[vendor]["vendor_keywords"].update(vendor_keywords)

                # Extract description keywords
                if description_col and pd.notna(row.get(description_col)):
                    description = str(row.get(description_col))
                    desc_keywords = extract_keywords_from_description(description)
                    for keyword in desc_keywords:
                        vendor_patterns[vendor]["description_keywords"][keyword] += 1

                # Track product types
                if product_col and pd.notna(row.get(product_col)):
                    product_type = str(row.get(product_col)).strip()
                    vendor_patterns[vendor]["product_types"][product_type] += 1

                # Track refund bases
                if (
                    refund_basis_col
                    and pd.notna(row.get(refund_basis_col))
                    and is_refund
                ):
                    refund_basis = str(row.get(refund_basis_col)).strip()
                    vendor_patterns[vendor]["refund_bases"][refund_basis] += 1

        # Extract keyword patterns
        if description_col:
            description = row.get(description_col)
            if pd.notna(description) and description != "":
                keywords = extract_keywords_from_description(str(description))
                if len(keywords) >= 2:
                    keyword_signature = tuple(sorted(keywords[:5]))

                    decision = row.get(decision_col, "")
                    is_refund = is_refund_decision(decision)

                    if is_refund:
                        keyword_patterns[keyword_signature]["refund_count"] += 1
                    else:
                        keyword_patterns[keyword_signature]["no_opp_count"] += 1

                    keyword_patterns[keyword_signature]["keywords"].update(keywords)

                    if (
                        refund_basis_col
                        and pd.notna(row.get(refund_basis_col))
                        and is_refund
                    ):
                        refund_basis = str(row.get(refund_basis_col)).strip()
                        keyword_patterns[keyword_signature]["refund_bases"][
                            refund_basis
                        ] += 1

        # Extract citation patterns
        if refund_basis_col:
            refund_basis = row.get(refund_basis_col)
            if pd.notna(refund_basis) and refund_basis != "":
                refund_basis = str(refund_basis).strip()
                citation_patterns[refund_basis]["usage_count"] += 1

                if (
                    len(citation_patterns[refund_basis]["example_cases"]) < 3
                    and vendor_col
                ):
                    vendor = row.get(vendor_col, "Unknown")
                    citation_patterns[refund_basis]["example_cases"].append(str(vendor))

    print(f"Extracted {len(vendor_patterns)} vendor patterns")
    print(f"Extracted {len(keyword_patterns)} keyword patterns")
    print(f"Extracted {len(citation_patterns)} citation patterns")

    # Convert to JSON-serializable format
    vendor_data = []
    for vendor, data in vendor_patterns.items():
        total_count = data["refund_count"] + data["no_opp_count"]
        if total_count < 3:
            continue

        success_rate = data["refund_count"] / total_count if total_count > 0 else 0
        most_common_product = data["product_types"].most_common(1)
        product_type = most_common_product[0][0] if most_common_product else "Unknown"

        most_common_basis = data["refund_bases"].most_common(1)
        refund_basis = most_common_basis[0][0] if most_common_basis else None

        vendor_keywords = (
            list(data["vendor_keywords"]) if data["vendor_keywords"] else []
        )
        top_desc_keywords = [k for k, v in data["description_keywords"].most_common(10)]

        vendor_data.append(
            {
                "vendor_name": vendor,
                "product_type": product_type,
                "historical_sample_count": total_count,
                "historical_success_rate": round(success_rate, 4),
                "typical_refund_basis": refund_basis,
                "vendor_keywords": vendor_keywords,
                "description_keywords": top_desc_keywords,
            }
        )

    keyword_data = []
    for keyword_sig, data in keyword_patterns.items():
        total_count = data["refund_count"] + data["no_opp_count"]
        if total_count < 5:
            continue

        success_rate = data["refund_count"] / total_count if total_count > 0 else 0
        most_common_basis = data["refund_bases"].most_common(1)
        typical_basis = most_common_basis[0][0] if most_common_basis else None

        signature_str = "|".join(sorted(keyword_sig))
        keywords_list = list(data["keywords"])

        keyword_data.append(
            {
                "keyword_signature": signature_str,
                "keywords": keywords_list,
                "success_rate": round(success_rate, 4),
                "sample_count": total_count,
                "typical_basis": typical_basis,
            }
        )

    citation_data = []
    for refund_basis, data in citation_patterns.items():
        citation_data.append(
            {
                "refund_basis": refund_basis,
                "usage_count": data["usage_count"],
                "example_cases": data["example_cases"],
            }
        )

    # Save to JSON files
    vendor_file = os.path.join(args.output_dir, "vendor_patterns.json")
    keyword_file = os.path.join(args.output_dir, "keyword_patterns.json")
    citation_file = os.path.join(args.output_dir, "citation_patterns.json")

    with open(vendor_file, "w", encoding="utf-8") as f:
        json.dump(vendor_data, f, indent=2)
    print(f"\n[SUCCESS] Saved {len(vendor_data)} vendor patterns to: {vendor_file}")

    with open(keyword_file, "w", encoding="utf-8") as f:
        json.dump(keyword_data, f, indent=2)
    print(f"[SUCCESS] Saved {len(keyword_data)} keyword patterns to: {keyword_file}")

    with open(citation_file, "w", encoding="utf-8") as f:
        json.dump(citation_data, f, indent=2)
    print(f"[SUCCESS] Saved {len(citation_data)} citation patterns to: {citation_file}")

    print(f"\n{'='*70}")
    print("SUMMARY")
    print(f"{'='*70}")
    print(f"Total vendors: {len(vendor_data)}")
    print(f"Total keyword patterns: {len(keyword_data)}")
    print(f"Total citation patterns: {len(citation_data)}")
    print(f"\nTop 10 vendors by success rate:")
    for vendor in sorted(
        vendor_data,
        key=lambda x: (x["historical_success_rate"], x["historical_sample_count"]),
        reverse=True,
    )[:10]:
        print(
            f"  {vendor['vendor_name'][:50]:50} {vendor['historical_success_rate']:.0%} ({vendor['historical_sample_count']} cases)"
        )

    print(f"\n\nPattern files saved to: {args.output_dir}/")
    print("Copy this folder to your personal laptop and run:")
    print("  python scripts/import_patterns_from_json.py --dir extracted_patterns")


if __name__ == "__main__":
    main()
