#!/usr/bin/env python3
"""
Train Pattern Learner on Phase 2 Master Refunds

This script trains the invoice pattern learning model on the comprehensive
Phase 2 Master Refunds dataset which contains 13,468 historical refund decisions.

Key Terminology:
- MPU = Multiple Points of Use (NOT Multi-Property Use)
  Software/cloud services used across multiple states require tax allocation
  based on where the service is actually used/consumed.

Usage:
    python scripts/train_pattern_learner.py
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from collections import Counter, defaultdict

import pandas as pd


class Phase2MasterProcessor:
    """Process Phase 2 Master Refunds file"""

    def load_file(self, filepath: str) -> pd.DataFrame:
        """Load the Refund Summary sheet"""
        print(f"Loading Phase 2 Master Refunds: {filepath}")
        df = pd.read_excel(filepath, sheet_name="Refund Summary")
        print(f"[OK] Loaded {len(df)} refund records with {len(df.columns)} columns")
        return df

    def get_summary_stats(self, df: pd.DataFrame):
        """Get summary statistics"""
        stats = {
            "total_records": len(df),
            "unique_vendors": (
                df["Vendor Name"].nunique() if "Vendor Name" in df.columns else 0
            ),
            "status_breakdown": (
                df["Status"].value_counts().to_dict() if "Status" in df.columns else {}
            ),
        }

        # Refund analysis
        if "Refund Amount" in df.columns:
            stats["total_refund_amount"] = df["Refund Amount"].sum()
            stats["avg_refund_amount"] = df["Refund Amount"].mean()

        if "Tax Category" in df.columns:
            stats["tax_categories"] = df["Tax Category"].value_counts().to_dict()

        if "Refund Basis" in df.columns:
            stats["refund_bases"] = df["Refund Basis"].value_counts().to_dict()

        if "Type" in df.columns:
            stats["product_types"] = df["Type"].value_counts().to_dict()

        return stats


class Phase2PatternLearner:
    """Learn refund patterns from Phase 2 Master data"""

    def __init__(self):
        """Initialize the pattern learner"""
        self.patterns = {
            "refund_keywords": defaultdict(int),
            "pass_keywords": defaultdict(int),
            "vendor_patterns": {},
            "product_type_patterns": {},
            "tax_category_patterns": {},
            "refund_basis_patterns": {},
            "methodology_patterns": {},
            "decision_reasons": [],
        }
        self.training_count = 0
        self.decision_distribution = Counter()

    def train(self, df: pd.DataFrame):
        """Train on Phase 2 Master data"""
        print(f"\nTraining on {len(df)} records...")

        for idx, row in df.iterrows():
            # Determine if this is a refund or pass
            notes = str(row.get("Notes", "")).lower()
            status = str(row.get("Status", "")).upper()
            refund_amt = row.get("Refund Amount", 0)

            # Classification
            is_refund = False
            is_pass = False

            # Handle NaN values in refund amount
            try:
                if refund_amt and pd.notna(refund_amt) and float(refund_amt) > 0:
                    is_refund = True
                    decision = "REFUND"
            except (ValueError, TypeError):
                pass

            if not is_refund and "pass" in notes:
                is_pass = True
                decision = "PASS"
            elif status and status != "NAN":
                decision = status
                if "Y" in status or "R" in status:
                    is_refund = True
            else:
                decision = "UNKNOWN"

            self.training_count += 1
            self.decision_distribution[decision] += 1

            # Extract features
            vendor = row.get("Vendor Name", "")
            product_type = row.get("Type", "")
            tax_category = row.get("Tax Category", "")
            refund_basis = row.get("Refund Basis", "")
            methodology = row.get("Methodology", "")
            description = str(row.get("Description", ""))

            # Learn vendor patterns
            if vendor:
                if vendor not in self.patterns["vendor_patterns"]:
                    self.patterns["vendor_patterns"][vendor] = Counter()
                self.patterns["vendor_patterns"][vendor][decision] += 1

            # Learn product type patterns
            if product_type:
                if product_type not in self.patterns["product_type_patterns"]:
                    self.patterns["product_type_patterns"][product_type] = Counter()
                self.patterns["product_type_patterns"][product_type][decision] += 1

            # Learn tax category patterns
            if tax_category:
                if tax_category not in self.patterns["tax_category_patterns"]:
                    self.patterns["tax_category_patterns"][tax_category] = Counter()
                self.patterns["tax_category_patterns"][tax_category][decision] += 1

            # Learn refund basis patterns
            if refund_basis:
                if refund_basis not in self.patterns["refund_basis_patterns"]:
                    self.patterns["refund_basis_patterns"][refund_basis] = Counter()
                self.patterns["refund_basis_patterns"][refund_basis][decision] += 1

            # Learn methodology patterns
            if methodology:
                if methodology not in self.patterns["methodology_patterns"]:
                    self.patterns["methodology_patterns"][methodology] = Counter()
                self.patterns["methodology_patterns"][methodology][decision] += 1

            # Extract keywords from notes and description
            if notes:
                keywords = self._extract_keywords(notes)
                if is_refund:
                    for kw in keywords:
                        self.patterns["refund_keywords"][kw] += 1
                elif is_pass:
                    for kw in keywords:
                        self.patterns["pass_keywords"][kw] += 1

                self.patterns["decision_reasons"].append((decision, notes, keywords))

            if description:
                desc_keywords = self._extract_keywords(description)
                if is_refund:
                    for kw in desc_keywords:
                        self.patterns["refund_keywords"][kw] += 1
                elif is_pass:
                    for kw in desc_keywords:
                        self.patterns["pass_keywords"][kw] += 1

        print(f"\n[OK] Training complete: {self.training_count} records processed")
        print(f"\nDecision distribution:")
        for decision, count in self.decision_distribution.most_common(10):
            print(f"  {decision}: {count:,}")

    def _extract_keywords(self, text: str):
        """Extract meaningful keywords"""
        import re

        if not text or text == "nan":
            return []

        # Remove common words
        stop_words = {
            "the",
            "a",
            "an",
            "and",
            "or",
            "but",
            "in",
            "on",
            "at",
            "to",
            "for",
            "of",
            "with",
            "by",
            "from",
            "as",
            "is",
            "was",
            "are",
            "were",
            "been",
            "be",
            "have",
            "has",
            "had",
            "do",
            "does",
            "did",
            "will",
            "would",
            "could",
            "should",
            "may",
            "might",
            "must",
            "can",
            "this",
            "that",
            "these",
            "those",
        }

        words = re.findall(r"\b[a-z]{3,}\b", text.lower())
        keywords = [w for w in words if w not in stop_words]
        return keywords

    def get_top_indicators(self, top_n=20):
        """Get top refund indicators"""
        print("\n" + "=" * 80)
        print(" TOP REFUND INDICATORS")
        print("=" * 80)

        # Top keywords
        print(f"\nTop {top_n} Refund Keywords:")
        for i, (kw, count) in enumerate(
            sorted(
                self.patterns["refund_keywords"].items(),
                key=lambda x: x[1],
                reverse=True,
            )[:top_n],
            1,
        ):
            print(f"  {i:2}. '{kw}': {count} occurrences")

        print(f"\nTop {top_n} Pass Keywords:")
        for i, (kw, count) in enumerate(
            sorted(
                self.patterns["pass_keywords"].items(), key=lambda x: x[1], reverse=True
            )[:top_n],
            1,
        ):
            print(f"  {i:2}. '{kw}': {count} occurrences")

        # Best product types for refunds
        print(f"\nBest Product Types for Refunds:")
        product_refund_rates = []
        for product_type, distribution in self.patterns[
            "product_type_patterns"
        ].items():
            total = sum(distribution.values())
            if total >= 10:  # Minimum sample size
                refund_count = sum(
                    count
                    for decision, count in distribution.items()
                    if decision in ["REFUND", "Y", "Y,R28", "Y,R32"]
                )
                refund_rate = refund_count / total
                if refund_rate > 0.3:
                    product_refund_rates.append((product_type, refund_rate, total))

        for i, (ptype, rate, count) in enumerate(
            sorted(product_refund_rates, key=lambda x: (x[1], x[2]), reverse=True)[
                :top_n
            ],
            1,
        ):
            print(f"  {i:2}. '{ptype}': {rate:.1%} refund rate ({count} samples)")

        # Best tax categories for refunds
        print(f"\nBest Tax Categories for Refunds:")
        tax_refund_rates = []
        for tax_cat, distribution in self.patterns["tax_category_patterns"].items():
            total = sum(distribution.values())
            if total >= 10:
                refund_count = sum(
                    count
                    for decision, count in distribution.items()
                    if decision in ["REFUND", "Y", "Y,R28", "Y,R32"]
                )
                refund_rate = refund_count / total
                if refund_rate > 0.3:
                    tax_refund_rates.append((tax_cat, refund_rate, total))

        for i, (tax_cat, rate, count) in enumerate(
            sorted(tax_refund_rates, key=lambda x: (x[1], x[2]), reverse=True)[:top_n],
            1,
        ):
            print(f"  {i:2}. '{tax_cat}': {rate:.1%} refund rate ({count} samples)")

        # Most common refund bases
        print(f"\nMost Common Refund Bases:")
        refund_basis_counts = []
        for basis, distribution in self.patterns["refund_basis_patterns"].items():
            if basis and str(basis) != "nan":
                total = sum(distribution.values())
                refund_basis_counts.append((basis, total))

        for i, (basis, count) in enumerate(
            sorted(refund_basis_counts, key=lambda x: x[1], reverse=True)[:top_n], 1
        ):
            print(f"  {i:2}. '{basis}': {count} occurrences")

        # Top methodologies
        print(f"\nTop Methodologies:")
        methodology_counts = []
        for methodology, distribution in self.patterns["methodology_patterns"].items():
            if methodology and str(methodology) != "nan":
                total = sum(distribution.values())
                methodology_counts.append((methodology, total))

        for i, (method, count) in enumerate(
            sorted(methodology_counts, key=lambda x: x[1], reverse=True)[:top_n], 1
        ):
            print(f"  {i:2}. '{method}': {count} occurrences")


def main():
    print("=" * 80)
    print(" PHASE 2 MASTER REFUNDS - PATTERN LEARNING")
    print("=" * 80)

    # Load data
    processor = Phase2MasterProcessor()
    df = processor.load_file("Test Data/Phase 2 Master Refunds_6-15-25.xlsx")

    # Get summary stats
    print("\n" + "=" * 80)
    print(" DATASET SUMMARY")
    print("=" * 80)
    stats = processor.get_summary_stats(df)

    print(f"\nTotal records: {stats['total_records']:,}")
    print(f"Unique vendors: {stats['unique_vendors']:,}")

    if "total_refund_amount" in stats:
        print(f"\nTotal refund amount: ${stats['total_refund_amount']:,.2f}")
        print(f"Average refund amount: ${stats['avg_refund_amount']:,.2f}")

    if "status_breakdown" in stats and stats["status_breakdown"]:
        print(f"\nStatus breakdown (top 10):")
        for status, count in sorted(
            stats["status_breakdown"].items(), key=lambda x: x[1], reverse=True
        )[:10]:
            print(f"  {status}: {count:,}")

    if "product_types" in stats and stats["product_types"]:
        print(f"\nProduct types (top 10):")
        for ptype, count in sorted(
            stats["product_types"].items(), key=lambda x: x[1], reverse=True
        )[:10]:
            print(f"  {ptype}: {count:,}")

    # Train pattern learner
    learner = Phase2PatternLearner()
    learner.train(df)

    # Get top indicators
    learner.get_top_indicators(top_n=15)

    print("\n" + "=" * 80)
    print(" TRAINING COMPLETE")
    print("=" * 80)
    print(
        f"\nThe pattern learner has been trained on {learner.training_count:,} historical refund decisions."
    )
    print(
        "You can now use these learned patterns to classify new invoices automatically."
    )


if __name__ == "__main__":
    main()
