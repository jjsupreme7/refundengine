#!/usr/bin/env python3
"""
Import Historical Knowledge from Excel Files

This script extracts patterns from historical tax decision Excel files
and imports them into the database to enhance future AI analysis.

NO Excel format standardization - reads any format, extracts key patterns.

Usage:
    python scripts/import_historical_knowledge.py --file "Phase_3_2021_Use Tax.xlsx"
    python scripts/import_historical_knowledge.py --file "2023 Denodo.xlsx" --dry-run

What it imports:
1. Vendor patterns → vendor_products table
2. Category patterns → vendor_product_patterns table
3. Refund basis citations → refund_citations table
"""

import argparse
import logging
import os
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pandas as pd

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.database import get_supabase_client

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class HistoricalKnowledgeImporter:
    """
    Imports historical knowledge from Excel files into database.
    Reads any Excel format, extracts patterns, imports to existing tables.
    """

    def __init__(self, dry_run: bool = False):
        """
        Initialize the importer.

        Args:
            dry_run: If True, don't actually import to database (just show what would be imported)
        """
        self.dry_run = dry_run
        self.supabase = None if dry_run else get_supabase_client()

        # Statistics
        self.stats = {
            "total_rows": 0,
            "analyzed_rows": 0,
            "vendor_patterns_extracted": 0,
            "category_patterns_extracted": 0,
            "citations_extracted": 0,
            "keyword_patterns_extracted": 0,
            "vendor_patterns_imported": 0,
            "category_patterns_imported": 0,
            "citations_imported": 0,
            "keyword_patterns_imported": 0,
        }

        # Extracted patterns
        self.vendor_patterns = defaultdict(
            lambda: {
                "refund_count": 0,
                "no_opp_count": 0,
                "product_types": Counter(),
                "refund_bases": Counter(),
                "sample_tax_amounts": [],
                "vendor_keywords": set(),  # For fuzzy matching
                "description_keywords": Counter(),  # For keyword pattern matching
            }
        )

        self.category_patterns = defaultdict(
            lambda: {
                "refund_count": 0,
                "no_opp_count": 0,
                "refund_bases": Counter(),
                "typical_citations": Counter(),
            }
        )

        self.citation_patterns = defaultdict(
            lambda: {
                "usage_count": 0,
                "example_cases": [],
            }
        )

        self.keyword_patterns = defaultdict(
            lambda: {
                "refund_count": 0,
                "no_opp_count": 0,
                "refund_bases": Counter(),
                "keywords": set(),
            }
        )

    def import_from_excel(self, excel_path: str):
        """
        Import knowledge from an Excel file (any format).

        Args:
            excel_path: Path to Excel file
        """
        logger.info(f"Reading Excel file: {excel_path}")

        # Read Excel
        df = pd.read_excel(excel_path)
        self.stats["total_rows"] = len(df)

        logger.info(f"Found {len(df)} rows with {len(df.columns)} columns")
        logger.info(f"Columns: {list(df.columns)[:10]}...")  # Show first 10 columns

        # Auto-detect key columns
        column_map = self._auto_detect_columns(df.columns)
        logger.info(f"Detected columns: {column_map}")

        # Filter to analyzed records only
        analyzed_df = self._filter_analyzed_records(df, column_map)
        self.stats["analyzed_rows"] = len(analyzed_df)

        logger.info(
            f"Filtered to {len(analyzed_df)} analyzed records (ignoring {len(df) - len(analyzed_df)} unanalyzed)"
        )

        if len(analyzed_df) == 0:
            logger.warning("No analyzed records found - nothing to import")
            return

        # Extract patterns
        logger.info("Extracting vendor patterns...")
        self._extract_vendor_patterns(analyzed_df, column_map)

        logger.info("Extracting category patterns...")
        self._extract_category_patterns(analyzed_df, column_map)

        logger.info("Extracting citation patterns...")
        self._extract_citation_patterns(analyzed_df, column_map)

        logger.info("Extracting keyword patterns...")
        self._extract_keyword_patterns(analyzed_df, column_map)

        # Import to database
        if not self.dry_run:
            logger.info("Importing to database...")
            self._import_vendor_patterns()
            self._import_category_patterns()
            self._import_citation_patterns()
            self._import_keyword_patterns()
        else:
            logger.info("DRY RUN - Not importing to database")
            self._print_dry_run_summary()

        # Print summary
        self._print_summary()

    def _auto_detect_columns(self, columns: List[str]) -> Dict[str, str]:
        """
        Auto-detect which columns contain the key fields we need.

        Args:
            columns: List of column names from Excel

        Returns:
            Dictionary mapping field type to actual column name
        """
        column_map = {}

        columns_lower = {col: col.lower() for col in columns}

        # Detect Final Decision
        for col, col_lower in columns_lower.items():
            if "final" in col_lower and "decision" in col_lower:
                column_map["final_decision"] = col
                break

        # Detect Vendor
        for col, col_lower in columns_lower.items():
            if "vendor" in col_lower and "name" in col_lower:
                column_map["vendor"] = col
                break
            elif col_lower == "vendor":
                column_map["vendor"] = col
                break

        # Detect Tax Category
        for col, col_lower in columns_lower.items():
            if "tax" in col_lower and "category" in col_lower:
                column_map["tax_category"] = col
                break

        # Detect Vertex Category
        for col, col_lower in columns_lower.items():
            if "vertex" in col_lower and "category" in col_lower:
                column_map["vertex_category"] = col
                break

        # Detect Material Group
        for col, col_lower in columns_lower.items():
            if "material" in col_lower and "group" in col_lower:
                column_map["material_group"] = col
                break

        # Detect Refund Basis
        for col, col_lower in columns_lower.items():
            if "refund" in col_lower and "basis" in col_lower:
                column_map["refund_basis"] = col
                break
            elif col_lower == "basis":
                column_map["refund_basis"] = col
                break

        # Detect Description
        for col, col_lower in columns_lower.items():
            if "description" in col_lower and "po" in col_lower:
                column_map["description"] = col
                break
            elif col_lower == "description":
                column_map["description"] = col
                break

        # Detect Tax Amount
        for col, col_lower in columns_lower.items():
            if "total" in col_lower and "tax" in col_lower:
                column_map["tax_amount"] = col
                break
            elif "tax" in col_lower and "amount" in col_lower:
                column_map["tax_amount"] = col
                break

        return column_map

    def _filter_analyzed_records(
        self, df: pd.DataFrame, column_map: Dict
    ) -> pd.DataFrame:
        """
        Filter to only records with Final Decision (analyzed records only).

        Args:
            df: DataFrame
            column_map: Column mapping

        Returns:
            Filtered DataFrame
        """
        if "final_decision" not in column_map:
            logger.warning("No 'Final Decision' column found - using all records")
            return df

        decision_col = column_map["final_decision"]

        # Filter to non-null, non-empty Final Decision
        analyzed = df[df[decision_col].notna() & (df[decision_col] != "")].copy()

        return analyzed

    def _is_refund_decision(self, decision: str) -> bool:
        """Check if a decision indicates a refund."""
        if pd.isna(decision):
            return False

        decision_upper = str(decision).upper()

        # Check for NO OPP first (explicit rejection)
        if "NO OPP" in decision_upper or "NO OPPORTUNITY" in decision_upper:
            return False

        # Check for refund indicators
        refund_keywords = ["REFUND", "ADD TO CLAIM", "CLAIM", "ELIGIBLE"]
        return any(keyword in decision_upper for keyword in refund_keywords)

    def _extract_vendor_keywords(self, vendor_name: str) -> List[str]:
        """
        Extract keywords from vendor name for fuzzy matching.

        Example: "ATC TOWER SERVICES LLC" → ["ATC", "TOWER", "SERVICES"]
        """
        if pd.isna(vendor_name) or vendor_name == "":
            return []

        # Remove common suffixes
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

        # Split on spaces and filter
        words = str(vendor_name).upper().replace(",", " ").replace(".", " ").split()
        keywords = [w for w in words if w not in stopwords and len(w) > 1]

        return keywords

    def _extract_description_keywords(self, description: str) -> List[str]:
        """
        Extract meaningful keywords from product description.

        Example: "Tower construction services for cell site" → ["tower", "construction", "services", "cell", "site"]
        """
        if pd.isna(description) or description == "":
            return []

        # Remove common stopwords
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

        # Clean and split
        text = str(description).lower()
        # Remove special characters but keep spaces
        text = "".join(c if c.isalnum() or c.isspace() else " " for c in text)
        words = text.split()

        # Filter out stopwords and short words
        keywords = [w for w in words if w not in stopwords and len(w) > 2]

        return keywords

    def _extract_vendor_patterns(self, df: pd.DataFrame, column_map: Dict):
        """Extract vendor-level patterns with fuzzy matching keywords."""
        if "vendor" not in column_map:
            logger.warning("No vendor column found - skipping vendor patterns")
            return

        vendor_col = column_map["vendor"]
        decision_col = column_map.get("final_decision")
        refund_basis_col = column_map.get("refund_basis")
        tax_amount_col = column_map.get("tax_amount")
        description_col = column_map.get("description")

        # Get product type column (prefer vertex_category, fallback to tax_category or material_group)
        product_col = (
            column_map.get("vertex_category")
            or column_map.get("tax_category")
            or column_map.get("material_group")
            or column_map.get("description")
        )

        for idx, row in df.iterrows():
            vendor = row.get(vendor_col)
            if pd.isna(vendor) or vendor == "":
                continue

            vendor = str(vendor).strip().upper()
            decision = row.get(decision_col, "") if decision_col else ""

            is_refund = self._is_refund_decision(decision)

            if is_refund:
                self.vendor_patterns[vendor]["refund_count"] += 1
            else:
                self.vendor_patterns[vendor]["no_opp_count"] += 1

            # Extract vendor keywords for fuzzy matching
            vendor_keywords = self._extract_vendor_keywords(vendor)
            self.vendor_patterns[vendor]["vendor_keywords"].update(vendor_keywords)

            # Extract description keywords
            if description_col and pd.notna(row.get(description_col)):
                description = str(row.get(description_col))
                desc_keywords = self._extract_description_keywords(description)
                for keyword in desc_keywords:
                    self.vendor_patterns[vendor]["description_keywords"][keyword] += 1

            # Track product types
            if product_col and pd.notna(row.get(product_col)):
                product_type = str(row.get(product_col)).strip()
                self.vendor_patterns[vendor]["product_types"][product_type] += 1

            # Track refund bases
            if refund_basis_col and pd.notna(row.get(refund_basis_col)) and is_refund:
                refund_basis = str(row.get(refund_basis_col)).strip()
                self.vendor_patterns[vendor]["refund_bases"][refund_basis] += 1

            # Track sample tax amounts
            if tax_amount_col and pd.notna(row.get(tax_amount_col)):
                try:
                    tax_amount = float(row.get(tax_amount_col))
                    if len(self.vendor_patterns[vendor]["sample_tax_amounts"]) < 10:
                        self.vendor_patterns[vendor]["sample_tax_amounts"].append(
                            tax_amount
                        )
                except:
                    pass

        self.stats["vendor_patterns_extracted"] = len(self.vendor_patterns)

    def _extract_category_patterns(self, df: pd.DataFrame, column_map: Dict):
        """Extract category-level patterns (vertex, tax, material)."""
        decision_col = column_map.get("final_decision")
        refund_basis_col = column_map.get("refund_basis")

        # Check each category type
        category_columns = []
        if "vertex_category" in column_map:
            category_columns.append(("vertex_category", column_map["vertex_category"]))
        if "tax_category" in column_map:
            category_columns.append(("tax_category", column_map["tax_category"]))
        if "material_group" in column_map:
            category_columns.append(("material_group", column_map["material_group"]))

        if not category_columns:
            logger.warning("No category columns found - skipping category patterns")
            return

        for category_type, category_col in category_columns:
            for idx, row in df.iterrows():
                category = row.get(category_col)
                if pd.isna(category) or category == "":
                    continue

                category = str(category).strip()
                pattern_key = f"{category_type}::{category}"

                decision = row.get(decision_col, "") if decision_col else ""
                is_refund = self._is_refund_decision(decision)

                if is_refund:
                    self.category_patterns[pattern_key]["refund_count"] += 1
                else:
                    self.category_patterns[pattern_key]["no_opp_count"] += 1

                # Track refund bases
                if (
                    refund_basis_col
                    and pd.notna(row.get(refund_basis_col))
                    and is_refund
                ):
                    refund_basis = str(row.get(refund_basis_col)).strip()
                    self.category_patterns[pattern_key]["refund_bases"][
                        refund_basis
                    ] += 1

        self.stats["category_patterns_extracted"] = len(self.category_patterns)

    def _extract_citation_patterns(self, df: pd.DataFrame, column_map: Dict):
        """Extract refund basis → citation mappings."""
        refund_basis_col = column_map.get("refund_basis")

        if not refund_basis_col:
            logger.warning("No refund basis column found - skipping citations")
            return

        decision_col = column_map.get("final_decision")
        vendor_col = column_map.get("vendor")

        for idx, row in df.iterrows():
            refund_basis = row.get(refund_basis_col)
            if pd.isna(refund_basis) or refund_basis == "":
                continue

            refund_basis = str(refund_basis).strip()

            decision = row.get(decision_col, "") if decision_col else ""
            if not self._is_refund_decision(decision):
                continue

            self.citation_patterns[refund_basis]["usage_count"] += 1

            # Store example case
            if len(self.citation_patterns[refund_basis]["example_cases"]) < 3:
                vendor = row.get(vendor_col, "Unknown") if vendor_col else "Unknown"
                self.citation_patterns[refund_basis]["example_cases"].append(
                    str(vendor)
                )

        self.stats["citations_extracted"] = len(self.citation_patterns)

    def _extract_keyword_patterns(self, df: pd.DataFrame, column_map: Dict):
        """
        Extract keyword-based patterns from descriptions.
        This allows matching without relying on Vertex Category codes.
        """
        description_col = column_map.get("description")
        if not description_col:
            logger.warning("No description column found - skipping keyword patterns")
            return

        decision_col = column_map.get("final_decision")
        refund_basis_col = column_map.get("refund_basis")

        for idx, row in df.iterrows():
            description = row.get(description_col)
            if pd.isna(description) or description == "":
                continue

            decision = row.get(decision_col, "") if decision_col else ""
            is_refund = self._is_refund_decision(decision)

            # Extract keywords
            keywords = self._extract_description_keywords(str(description))
            if len(keywords) < 2:  # Need at least 2 keywords for meaningful pattern
                continue

            # Create keyword signature (sorted for consistency)
            keyword_signature = tuple(sorted(keywords[:5]))  # Use top 5 keywords

            if is_refund:
                self.keyword_patterns[keyword_signature]["refund_count"] += 1
            else:
                self.keyword_patterns[keyword_signature]["no_opp_count"] += 1

            # Track keywords and refund bases
            self.keyword_patterns[keyword_signature]["keywords"].update(keywords)

            if refund_basis_col and pd.notna(row.get(refund_basis_col)) and is_refund:
                refund_basis = str(row.get(refund_basis_col)).strip()
                self.keyword_patterns[keyword_signature]["refund_bases"][
                    refund_basis
                ] += 1

        self.stats["keyword_patterns_extracted"] = len(self.keyword_patterns)
        logger.info(f"Extracted {len(self.keyword_patterns)} keyword patterns")

    def _import_vendor_patterns(self):
        """Import vendor patterns to vendor_products table with fuzzy matching keywords."""
        logger.info("Importing vendor patterns to database...")

        imported = 0
        for vendor, data in self.vendor_patterns.items():
            total_count = data["refund_count"] + data["no_opp_count"]
            if total_count < 3:  # Skip vendors with very few samples
                continue

            success_rate = data["refund_count"] / total_count if total_count > 0 else 0

            # Get most common product type
            most_common_product = data["product_types"].most_common(1)
            product_type = (
                most_common_product[0][0] if most_common_product else "Unknown"
            )

            # Get most common refund basis
            most_common_basis = data["refund_bases"].most_common(1)
            refund_basis = most_common_basis[0][0] if most_common_basis else None

            # Get vendor keywords for fuzzy matching
            vendor_keywords = (
                list(data["vendor_keywords"]) if data["vendor_keywords"] else None
            )

            # Get top description keywords
            top_desc_keywords = [
                k for k, v in data["description_keywords"].most_common(10)
            ]

            try:
                # Check if vendor already exists
                existing = (
                    self.supabase.table("vendor_products")
                    .select("*")
                    .eq("vendor_name", vendor)
                    .execute()
                )

                if existing.data and len(existing.data) > 0:
                    # Update existing
                    update_data = {
                        "historical_sample_count": total_count,
                        "historical_success_rate": success_rate,
                        "typical_refund_basis": refund_basis,
                    }
                    if vendor_keywords:
                        update_data["vendor_keywords"] = vendor_keywords
                    if top_desc_keywords:
                        update_data["description_keywords"] = top_desc_keywords

                    self.supabase.table("vendor_products").update(update_data).eq(
                        "vendor_name", vendor
                    ).execute()
                else:
                    # Insert new
                    insert_data = {
                        "vendor_name": vendor,
                        "product_type": product_type,
                        "historical_sample_count": total_count,
                        "historical_success_rate": success_rate,
                        "typical_refund_basis": refund_basis,
                    }
                    if vendor_keywords:
                        insert_data["vendor_keywords"] = vendor_keywords
                    if top_desc_keywords:
                        insert_data["description_keywords"] = top_desc_keywords

                    self.supabase.table("vendor_products").insert(insert_data).execute()

                imported += 1

            except Exception as e:
                logger.error(f"Error importing vendor {vendor}: {e}")

        self.stats["vendor_patterns_imported"] = imported
        logger.info(f"Imported {imported} vendor patterns")

    def _import_category_patterns(self):
        """Import category patterns to vendor_product_patterns table."""
        logger.info("Importing category patterns to database...")

        imported = 0
        for pattern_key, data in self.category_patterns.items():
            total_count = data["refund_count"] + data["no_opp_count"]
            if total_count < 5:  # Skip patterns with very few samples
                continue

            category_type, category_value = pattern_key.split("::", 1)
            success_rate = data["refund_count"] / total_count if total_count > 0 else 0

            # Get most common refund basis
            most_common_basis = data["refund_bases"].most_common(1)
            typical_basis = most_common_basis[0][0] if most_common_basis else None

            try:
                # Check if pattern already exists
                existing = (
                    self.supabase.table("vendor_product_patterns")
                    .select("*")
                    .eq("pattern_type", category_type)
                    .eq("pattern_value", category_value)
                    .execute()
                )

                if existing.data and len(existing.data) > 0:
                    # Update existing
                    self.supabase.table("vendor_product_patterns").update(
                        {
                            "success_rate": success_rate,
                            "sample_count": total_count,
                            "typical_basis": typical_basis,
                        }
                    ).eq("pattern_type", category_type).eq(
                        "pattern_value", category_value
                    ).execute()
                else:
                    # Insert new
                    self.supabase.table("vendor_product_patterns").insert(
                        {
                            "pattern_type": category_type,
                            "pattern_value": category_value,
                            "success_rate": success_rate,
                            "sample_count": total_count,
                            "typical_basis": typical_basis,
                        }
                    ).execute()

                imported += 1

            except Exception as e:
                logger.error(f"Error importing pattern {pattern_key}: {e}")

        self.stats["category_patterns_imported"] = imported
        logger.info(f"Imported {imported} category patterns")

    def _import_citation_patterns(self):
        """Import citation patterns to refund_citations table."""
        logger.info("Importing citation patterns to database...")

        # Map common refund bases to RCW/WAC citations
        citation_map = {
            "MPU": "RCW 82.04.067",
            "MULTIPLE POINT OF USE": "RCW 82.04.067",
            "OUT-OF-STATE SERVICES": "RCW 82.04.050",
            "OOS SERVICES": "RCW 82.04.050",
            "NON-TAXABLE": "RCW 82.04.050",
            "OUT-OF-STATE SHIPMENT": "RCW 82.08.0263",
            "OOS SHIPMENT": "RCW 82.08.0263",
            "WRONG RATE": "WAC 458-20-15502",
            "SOFTWARE MAINTENANCE": "WAC 458-20-15502",
            "HARDWARE MAINTENANCE": "WAC 458-20-15502",
        }

        imported = 0
        for refund_basis, data in self.citation_patterns.items():
            # Try to find matching citation
            refund_basis_upper = refund_basis.upper()
            legal_citation = None

            for key, citation in citation_map.items():
                if key in refund_basis_upper:
                    legal_citation = citation
                    break

            try:
                # Check if citation already exists
                existing = (
                    self.supabase.table("refund_citations")
                    .select("*")
                    .eq("refund_basis", refund_basis)
                    .execute()
                )

                example_cases = ", ".join(data["example_cases"][:3])

                if existing.data and len(existing.data) > 0:
                    # Update existing
                    self.supabase.table("refund_citations").update(
                        {
                            "usage_count": data["usage_count"],
                            "example_cases": example_cases,
                        }
                    ).eq("refund_basis", refund_basis).execute()
                else:
                    # Insert new
                    self.supabase.table("refund_citations").insert(
                        {
                            "refund_basis": refund_basis,
                            "legal_citation": legal_citation,
                            "usage_count": data["usage_count"],
                            "example_cases": example_cases,
                        }
                    ).execute()

                imported += 1

            except Exception as e:
                logger.error(f"Error importing citation for {refund_basis}: {e}")

        self.stats["citations_imported"] = imported
        logger.info(f"Imported {imported} citation patterns")

    def _import_keyword_patterns(self):
        """Import keyword patterns to keyword_patterns table for description-based matching."""
        logger.info("Importing keyword patterns to database...")

        imported = 0
        for keyword_signature, data in self.keyword_patterns.items():
            total_count = data["refund_count"] + data["no_opp_count"]
            if total_count < 5:  # Skip patterns with very few samples
                continue

            success_rate = data["refund_count"] / total_count if total_count > 0 else 0

            # Get most common refund basis
            most_common_basis = data["refund_bases"].most_common(1)
            typical_basis = most_common_basis[0][0] if most_common_basis else None

            # Convert keyword signature to list for storage
            keywords_list = list(data["keywords"])

            try:
                # Create unique signature string for lookup
                signature_str = "|".join(sorted(keyword_signature))

                # Check if pattern already exists
                existing = (
                    self.supabase.table("keyword_patterns")
                    .select("*")
                    .eq("keyword_signature", signature_str)
                    .execute()
                )

                if existing.data and len(existing.data) > 0:
                    # Update existing
                    self.supabase.table("keyword_patterns").update(
                        {
                            "keywords": keywords_list,
                            "success_rate": success_rate,
                            "sample_count": total_count,
                            "typical_basis": typical_basis,
                        }
                    ).eq("keyword_signature", signature_str).execute()
                else:
                    # Insert new
                    self.supabase.table("keyword_patterns").insert(
                        {
                            "keyword_signature": signature_str,
                            "keywords": keywords_list,
                            "success_rate": success_rate,
                            "sample_count": total_count,
                            "typical_basis": typical_basis,
                        }
                    ).execute()

                imported += 1

            except Exception as e:
                logger.error(
                    f"Error importing keyword pattern {keyword_signature[:3]}: {e}"
                )

        self.stats["keyword_patterns_imported"] = imported
        logger.info(f"Imported {imported} keyword patterns")

    def _print_dry_run_summary(self):
        """Print what would be imported (dry run mode)."""
        print("\n" + "=" * 70)
        print("DRY RUN - Would Import:")
        print("=" * 70)

        print(f"\nVendor Patterns ({len(self.vendor_patterns)}):")
        for vendor, data in sorted(
            self.vendor_patterns.items(),
            key=lambda x: x[1]["refund_count"],
            reverse=True,
        )[:10]:
            total = data["refund_count"] + data["no_opp_count"]
            success_rate = data["refund_count"] / total if total > 0 else 0
            most_common_product = data["product_types"].most_common(1)
            product = most_common_product[0][0] if most_common_product else "Unknown"
            print(
                f"  {vendor[:40]:40} {success_rate:5.0%} ({data['refund_count']}/{total}) - {product}"
            )

        print(f"\nCategory Patterns ({len(self.category_patterns)}):")
        for pattern_key, data in sorted(
            self.category_patterns.items(),
            key=lambda x: x[1]["refund_count"],
            reverse=True,
        )[:10]:
            total = data["refund_count"] + data["no_opp_count"]
            success_rate = data["refund_count"] / total if total > 0 else 0
            category_type, category_value = pattern_key.split("::", 1)
            print(
                f"  {category_value[:40]:40} {success_rate:5.0%} ({data['refund_count']}/{total}) [{category_type}]"
            )

        print(f"\nCitation Patterns ({len(self.citation_patterns)}):")
        for basis, data in sorted(
            self.citation_patterns.items(),
            key=lambda x: x[1]["usage_count"],
            reverse=True,
        )[:10]:
            print(f"  {basis[:50]:50} {data['usage_count']:5} uses")

        print(f"\nKeyword Patterns ({len(self.keyword_patterns)}):")
        for keyword_sig, data in sorted(
            self.keyword_patterns.items(),
            key=lambda x: x[1]["refund_count"],
            reverse=True,
        )[:10]:
            total = data["refund_count"] + data["no_opp_count"]
            success_rate = data["refund_count"] / total if total > 0 else 0
            keywords_str = ", ".join(list(keyword_sig)[:3])  # Show first 3 keywords
            print(
                f"  [{keywords_str}] {success_rate:5.0%} ({data['refund_count']}/{total})"
            )

    def _print_summary(self):
        """Print import summary."""
        print("\n" + "=" * 70)
        print("IMPORT SUMMARY")
        print("=" * 70)
        print(f"Total rows in Excel: {self.stats['total_rows']}")
        print(f"Analyzed rows (with Final Decision): {self.stats['analyzed_rows']}")
        print(f"\nPatterns Extracted:")
        print(f"  Vendor patterns: {self.stats['vendor_patterns_extracted']}")
        print(f"  Category patterns: {self.stats['category_patterns_extracted']}")
        print(f"  Citation patterns: {self.stats['citations_extracted']}")
        print(f"  Keyword patterns: {self.stats['keyword_patterns_extracted']}")

        if not self.dry_run:
            print(f"\nPatterns Imported to Database:")
            print(f"  Vendor patterns: {self.stats['vendor_patterns_imported']}")
            print(f"  Category patterns: {self.stats['category_patterns_imported']}")
            print(f"  Citation patterns: {self.stats['citations_imported']}")
            print(f"  Keyword patterns: {self.stats['keyword_patterns_imported']}")
        else:
            print("\n(Dry run - no database import performed)")


def main():
    parser = argparse.ArgumentParser(
        description="Import historical knowledge from Excel files"
    )
    parser.add_argument("--file", required=True, help="Path to Excel file")
    parser.add_argument(
        "--dry-run", action="store_true", help="Dry run - do not import to database"
    )

    args = parser.parse_args()

    if not os.path.exists(args.file):
        print(f"Error: File not found: {args.file}")
        sys.exit(1)

    importer = HistoricalKnowledgeImporter(dry_run=args.dry_run)
    importer.import_from_excel(args.file)


if __name__ == "__main__":
    main()
