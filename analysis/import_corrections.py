#!/usr/bin/env python3
"""
Import Human Corrections from Excel
Reads reviewed Excel file and updates database with corrections
Updates vendor learning system based on corrections
"""

import argparse
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import centralized Supabase client
try:
    from core.database import get_supabase_client

    supabase = get_supabase_client()
except ImportError:
    print("Error: supabase package not installed. Run: pip install supabase")
    sys.exit(1)


class CorrectionImporter:
    """Imports human corrections from Excel and updates learning system"""

    def __init__(self, reviewer_name: str = "human"):
        self.reviewer_name = reviewer_name
        self.stats = {
            "approved": 0,
            "corrected": 0,
            "rejected": 0,
            "skipped": 0,
            "patterns_learned": 0,
            "products_learned": 0,
        }

    def get_analysis_id(self, row_id: int) -> Optional[str]:
        """Get the analysis_id for a given row_id"""
        try:
            response = (
                supabase.table("analysis_results")
                .select("id")
                .eq("row_id", row_id)
                .order("created_at", desc=True)
                .limit(1)
                .execute()
            )

            if response.data:
                return response.data[0]["id"]
            return None
        except Exception as e:
            print(f"Error getting analysis_id for row {row_id}: {e}")
            return None

    def import_review(self, row: pd.Series) -> bool:
        """Import a single review from Excel row"""

        # Check if row has been reviewed
        review_status = row.get("Review_Status")
        if pd.isna(review_status) or review_status == "":
            self.stats["skipped"] += 1
            return False

        review_status = str(review_status).lower().strip()

        # Get analysis_id
        analysis_id = self.get_analysis_id(int(row["Row_ID"]))
        if not analysis_id:
            print(f"  ⚠ Warning: No analysis found for Row {row['Row_ID']}")
            self.stats["skipped"] += 1
            return False

        print(f"  Row {row['Row_ID']}: Status = {review_status}")

        # Determine which fields were corrected
        fields_corrected = []
        corrections = {}

        if review_status == "corrected" or review_status == "needs correction":
            # Check each correction field
            if pd.notna(row.get("Corrected_Product_Desc")):
                fields_corrected.append("product_desc")
                corrections["corrected_product_desc"] = row["Corrected_Product_Desc"]

            if pd.notna(row.get("Corrected_Product_Type")):
                fields_corrected.append("product_type")
                corrections["corrected_product_type"] = row["Corrected_Product_Type"]

            if pd.notna(row.get("Corrected_Refund_Basis")):
                fields_corrected.append("refund_basis")
                corrections["corrected_refund_basis"] = row["Corrected_Refund_Basis"]

            if pd.notna(row.get("Corrected_Citation")):
                fields_corrected.append("citation")
                corrections["corrected_citation"] = row["Corrected_Citation"]

            if pd.notna(row.get("Corrected_Estimated_Refund")):
                fields_corrected.append("estimated_refund")
                corrections["corrected_estimated_refund"] = float(
                    row["Corrected_Estimated_Refund"]
                )
                # Calculate percentage
                if row["Tax"] > 0:
                    corrections["corrected_refund_percentage"] = (
                        float(row["Corrected_Estimated_Refund"])
                        / float(row["Tax"])
                        * 100
                    )

        # Build review record
        review_data = {
            "analysis_id": analysis_id,
            "row_id": int(row["Row_ID"]),
            "review_status": (
                "approved"
                if review_status == "approved"
                else (
                    "corrected"
                    if review_status in ["corrected", "needs correction"]
                    else "rejected"
                )
            ),
            "reviewer_notes": (
                row.get("Reviewer_Notes")
                if pd.notna(row.get("Reviewer_Notes"))
                else None
            ),
            "reviewed_at": datetime.utcnow().isoformat(),
            "reviewed_by": self.reviewer_name,
            "fields_corrected": fields_corrected if fields_corrected else None,
        }

        # Add corrections
        review_data.update(corrections)

        # Insert review
        try:
            response = supabase.table("analysis_reviews").insert(review_data).execute()

            if response.data:
                review_id = response.data[0]["id"]
                print(f"    ✓ Review saved: {review_data['review_status']}")

                # Update stats
                if review_data["review_status"] == "approved":
                    self.stats["approved"] += 1
                elif review_data["review_status"] == "corrected":
                    self.stats["corrected"] += 1
                    # Learn from correction
                    self.learn_from_correction(row, review_id, corrections)
                else:
                    self.stats["rejected"] += 1

                # Update analysis status
                supabase.table("analysis_results").update(
                    {"analysis_status": review_data["review_status"]}
                ).eq("id", analysis_id).execute()

                return True
            else:
                print(f"    ✗ Failed to save review")
                return False

        except Exception as e:
            print(f"    ✗ Error saving review: {e}")
            return False

    def learn_from_correction(self, row: pd.Series, review_id: str, corrections: Dict):
        """Update vendor learning system based on correction"""

        vendor_name = row["Vendor"]

        # Learn product information
        if "corrected_product_type" in corrections:
            product_desc = corrections.get(
                "corrected_product_desc", row.get("AI_Product_Desc")
            )
            product_type = corrections["corrected_product_type"]

            # Insert/update vendor_products
            try:
                product_data = {
                    "vendor_name": vendor_name,
                    "product_description": product_desc,
                    "product_type": product_type,
                    "learning_source": "human_correction",
                    "confidence_score": 100.0,
                    "first_seen_date": datetime.utcnow().isoformat(),
                    "last_seen_date": datetime.utcnow().isoformat(),
                }

                # Check if exists
                existing = (
                    supabase.table("vendor_products")
                    .select("id")
                    .eq("vendor_name", vendor_name)
                    .eq("product_description", product_desc)
                    .execute()
                )

                if existing.data:
                    # Update existing
                    supabase.table("vendor_products").update(
                        {
                            "product_type": product_type,
                            "last_seen_date": datetime.utcnow().isoformat(),
                            "frequency": supabase.table("vendor_products")
                            .select("frequency")
                            .eq("id", existing.data[0]["id"])
                            .execute()
                            .data[0]["frequency"]
                            + 1,
                        }
                    ).eq("id", existing.data[0]["id"]).execute()
                    print(f"    ✓ Updated vendor_products")
                else:
                    # Insert new
                    supabase.table("vendor_products").insert(product_data).execute()
                    print(f"    ✓ Added to vendor_products")
                    self.stats["products_learned"] += 1

            except Exception as e:
                print(f"    ✗ Error updating vendor_products: {e}")

            # Create/update pattern
            try:
                # Extract keywords from product description (simple approach)
                keywords = product_desc.split()[:3]  # First 3 words
                product_keyword = " ".join(keywords)

                pattern_data = {
                    "vendor_name": vendor_name,
                    "product_keyword": product_keyword,
                    "product_pattern": product_desc,
                    "correct_product_type": product_type,
                    "learned_from_correction_id": review_id,
                    "confidence_score": 100.0,
                    "times_confirmed": 1,
                    "is_active": True,
                }

                # Check if pattern exists
                existing = (
                    supabase.table("vendor_product_patterns")
                    .select("id")
                    .eq("vendor_name", vendor_name)
                    .eq("product_keyword", product_keyword)
                    .execute()
                )

                if existing.data:
                    # Update times_confirmed
                    current = (
                        supabase.table("vendor_product_patterns")
                        .select("times_confirmed")
                        .eq("id", existing.data[0]["id"])
                        .execute()
                    )
                    times = current.data[0]["times_confirmed"] + 1

                    supabase.table("vendor_product_patterns").update(
                        {
                            "times_confirmed": times,
                            "confidence_score": min(100, 80 + times * 5),
                            "updated_at": datetime.utcnow().isoformat(),
                        }
                    ).eq("id", existing.data[0]["id"]).execute()
                    print(f"    ✓ Updated pattern (confirmed {times}x)")
                else:
                    # Insert new pattern
                    supabase.table("vendor_product_patterns").insert(
                        pattern_data
                    ).execute()
                    print(f"    ✓ Created new pattern")
                    self.stats["patterns_learned"] += 1

            except Exception as e:
                print(f"    ✗ Error updating patterns: {e}")

        # Log to audit trail
        self.log_correction(row, corrections)

    def log_correction(self, row: pd.Series, corrections: Dict):
        """Log correction to audit trail"""
        try:
            for field, new_value in corrections.items():
                field_name = field.replace("corrected_", "")
                old_value = row.get(f'AI_{field_name.title().replace("_", " ")}')

                audit_data = {
                    "event_type": "human_correction",
                    "entity_type": "analysis_result",
                    "field_name": field_name,
                    "old_value": str(old_value) if pd.notna(old_value) else None,
                    "new_value": str(new_value),
                    "changed_by": self.reviewer_name,
                    "change_reason": (
                        row.get("Reviewer_Notes")
                        if pd.notna(row.get("Reviewer_Notes"))
                        else None
                    ),
                    "row_id": int(row["Row_ID"]),
                    "vendor_name": row["Vendor"],
                }

                supabase.table("audit_trail").insert(audit_data).execute()

        except Exception as e:
            print(f"    ✗ Error logging to audit trail: {e}")


def main():
    parser = argparse.ArgumentParser(
        description="Import corrections from reviewed Excel"
    )
    parser.add_argument(
        "reviewed_excel", help="Path to reviewed Excel file with corrections"
    )
    parser.add_argument("--reviewer", default="human", help="Reviewer name/email")
    parser.add_argument(
        "--dry-run", action="store_true", help="Preview without saving to database"
    )

    args = parser.parse_args()

    print(f"\n{'='*80}")
    print(f"IMPORT CORRECTIONS FROM EXCEL")
    print(f"{'='*80}")
    print(f"File:     {args.reviewed_excel}")
    print(f"Reviewer: {args.reviewer}")
    print(f"Dry run:  {args.dry_run}")
    print(f"{'='*80}\n")

    # Load Excel
    df = pd.read_excel(args.reviewed_excel)
    print(f"Loaded {len(df)} rows from Excel\n")

    # Check for required columns
    required_cols = ["Row_ID", "Vendor", "Review_Status"]
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        print(f"Error: Missing required columns: {missing_cols}")
        return

    # Initialize importer
    importer = CorrectionImporter(reviewer_name=args.reviewer)

    # Import each review
    print("Importing reviews...\n")
    for idx, row in df.iterrows():
        if args.dry_run:
            review_status = row.get("Review_Status")
            if pd.notna(review_status):
                print(f"  Row {row['Row_ID']}: Would import {review_status}")
        else:
            importer.import_review(row)

    # Print summary
    print(f"\n{'='*80}")
    print(f"IMPORT SUMMARY")
    print(f"{'='*80}")
    print(f"  Approved:         {importer.stats['approved']}")
    print(f"  Corrected:        {importer.stats['corrected']}")
    print(f"  Rejected:         {importer.stats['rejected']}")
    print(f"  Skipped:          {importer.stats['skipped']}")
    print(f"  Products learned: {importer.stats['products_learned']}")
    print(f"  Patterns learned: {importer.stats['patterns_learned']}")
    print(f"{'='*80}\n")

    if args.dry_run:
        print("This was a dry run. No changes were made to the database.")
    else:
        print("✓ Import complete! Vendor learning system updated.")


if __name__ == "__main__":
    main()
