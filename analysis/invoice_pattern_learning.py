#!/usr/bin/env python3
"""
Invoice Pattern Learning Module

Analyzes thousands of invoices to learn refund decision patterns and
automatically classify new invoices.

This module:
1. Extracts patterns from historical "Final Decision" data
2. Learns from "Recon Analysis" and "KOM Analysis & Notes" columns
3. Builds a classification model based on:
   - Vertex categories
   - Product descriptions
   - Vendor patterns
   - Tax codes
   - Material groups
4. Automatically scores new invoices for refund likelihood

Usage:
    from analysis.invoice_pattern_learning import InvoicePatternLearner

    # Train on historical data
    learner = InvoicePatternLearner()
    learner.train_from_excel("Test Data/2023 Records in Denodo not in Master_2-2-24.xlsx")

    # Classify new invoice
    prediction = learner.classify_invoice(new_invoice_data)
    # Returns: {'refund_decision': 'REFUND', 'confidence': 0.85, 'reasons': [...]}
"""

import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Dict, List, Tuple

import pandas as pd


class InvoicePatternLearner:
    """Learn refund patterns from historical invoice decisions"""

    def __init__(self):
        """Initialize the pattern learner"""
        self.patterns = {
            "refund_keywords": defaultdict(int),  # Keywords -> refund count
            "no_opp_keywords": defaultdict(int),  # Keywords -> no opportunity count
            "vertex_categories": {},  # Category -> decision distribution
            "material_groups": {},  # Material group -> decision distribution
            "tax_codes": {},  # Tax code -> decision distribution
            "vendor_patterns": {},  # Vendor -> decision distribution
            "decision_reasons": [],  # List of (decision, reason, keywords)
        }
        self.training_count = 0
        self.decision_distribution = Counter()

    def train_from_excel(self, excel_path: str, file_type: str = "auto"):
        """
        Train the model from historical Excel data

        Args:
            excel_path: Path to Denodo or Use Tax Excel file
            file_type: 'denodo', 'use_tax', or 'auto' to detect
        """
        from analysis.excel_processors import (
            DenodoSalesTaxProcessor,
            UseTaxProcessor,
            auto_detect_file_type,
        )

        # Auto-detect file type
        if file_type == "auto":
            file_type = auto_detect_file_type(excel_path)

        # Load data
        if file_type == "denodo_sales_tax":
            processor = DenodoSalesTaxProcessor()
            df = processor.load_file(excel_path)
            self._train_from_denodo(df)
        elif file_type == "use_tax":
            processor = UseTaxProcessor()
            df = processor.load_file(excel_path)
            self._train_from_use_tax(df)
        else:
            raise ValueError(f"Unknown file type: {file_type}")

        print(f"Training complete: {self.training_count} records processed")
        print(f"Decision distribution: {dict(self.decision_distribution)}")

    def _train_from_denodo(self, df: pd.DataFrame):
        """Train from Denodo sales tax data"""
        print(f"Training from Denodo file with {len(df)} rows...")

        for idx, row in df.iterrows():
            final_decision = str(row.get("Final Decision", "")).strip().upper()
            if not final_decision or final_decision == "NAN":
                continue

            self.training_count += 1
            self.decision_distribution[final_decision] += 1

            # Extract features
            recon_analysis = str(row.get("Recon Analysis", "")).lower()
            description = str(row.get("txz01_po_description", "")).lower()
            material_group = row.get("matk1_po_material_group_desc", "")
            tax_code = row.get("mwskz_tax_code", "")
            vendor = row.get("vendor", "")
            account_desc = str(row.get("txt50_account_description", "")).lower()

            # Learn from decision
            is_refund = (
                "REFUND" in final_decision
                or "OPP" in final_decision
                and "NO" not in final_decision
            )
            is_no_opp = "NO OPP" in final_decision or "PASS" in final_decision

            # Extract keywords from analysis
            if recon_analysis:
                keywords = self._extract_keywords(recon_analysis)

                if is_refund:
                    for kw in keywords:
                        self.patterns["refund_keywords"][kw] += 1
                elif is_no_opp:
                    for kw in keywords:
                        self.patterns["no_opp_keywords"][kw] += 1

                # Store reasons
                self.patterns["decision_reasons"].append(
                    (final_decision, recon_analysis, keywords)
                )

            # Learn material group patterns
            if material_group:
                if material_group not in self.patterns["material_groups"]:
                    self.patterns["material_groups"][material_group] = Counter()
                self.patterns["material_groups"][material_group][final_decision] += 1

            # Learn tax code patterns
            if tax_code:
                if tax_code not in self.patterns["tax_codes"]:
                    self.patterns["tax_codes"][tax_code] = Counter()
                self.patterns["tax_codes"][tax_code][final_decision] += 1

            # Learn vendor patterns
            if vendor:
                if vendor not in self.patterns["vendor_patterns"]:
                    self.patterns["vendor_patterns"][vendor] = Counter()
                self.patterns["vendor_patterns"][vendor][final_decision] += 1

    def _train_from_use_tax(self, df: pd.DataFrame):
        """Train from Use Tax data"""
        print(f"Training from Use Tax file with {len(df)} rows...")

        for idx, row in df.iterrows():
            final_decision = str(row.get("Final Decision", "")).strip().upper()
            if not final_decision or final_decision == "NAN":
                continue

            self.training_count += 1
            self.decision_distribution[final_decision] += 1

            # Extract features
            kom_analysis = str(row.get("KOM Analysis & Notes", "")).lower()
            description = str(row.get("Description", "")).lower()
            vertex_category = row.get("Vertex Category", "")
            vendor = row.get("Vendor Name", "")
            tax_category = row.get("Tax Category", "")

            # Learn from decision
            is_refund = "REFUND" in final_decision
            is_no_opp = "NO OPP" in final_decision

            # Extract keywords from analysis
            if kom_analysis:
                keywords = self._extract_keywords(kom_analysis)

                if is_refund:
                    for kw in keywords:
                        self.patterns["refund_keywords"][kw] += 1
                elif is_no_opp:
                    for kw in keywords:
                        self.patterns["no_opp_keywords"][kw] += 1

                self.patterns["decision_reasons"].append(
                    (final_decision, kom_analysis, keywords)
                )

            # Learn Vertex category patterns
            if vertex_category:
                if vertex_category not in self.patterns["vertex_categories"]:
                    self.patterns["vertex_categories"][vertex_category] = Counter()
                self.patterns["vertex_categories"][vertex_category][final_decision] += 1

            # Learn vendor patterns
            if vendor:
                if vendor not in self.patterns["vendor_patterns"]:
                    self.patterns["vendor_patterns"][vendor] = Counter()
                self.patterns["vendor_patterns"][vendor][final_decision] += 1

    def _extract_keywords(self, text: str) -> List[str]:
        """Extract meaningful keywords from analysis text"""
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
            "o",
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

        # Extract words
        words = re.findall(r"\b[a-z]{3,}\b", text.lower())
        keywords = [w for w in words if w not in stop_words]

        return keywords

    def classify_invoice(self, invoice_data: Dict) -> Dict:
        """
        Classify an invoice for refund eligibility

        Args:
            invoice_data: Dict with invoice fields (from Excel row)

        Returns:
            {
                'refund_decision': 'LIKELY_REFUND' | 'LIKELY_NO_OPP' | 'UNCERTAIN',
                'confidence': 0.0-1.0,
                'score': float (positive = refund, negative = no opp),
                'reasons': [list of reasoning],
                'matched_patterns': {pattern_type: matched_value}
            }
        """
        score = 0.0
        reasons = []
        matched_patterns = {}

        # Check Vertex category (strongest signal)
        vertex_cat = invoice_data.get("Vertex Category") or invoice_data.get(
            "vertex_category"
        )
        if vertex_cat and vertex_cat in self.patterns["vertex_categories"]:
            distribution = self.patterns["vertex_categories"][vertex_cat]
            total = sum(distribution.values())

            refund_count = sum(
                count
                for decision, count in distribution.items()
                if "REFUND" in decision
            )
            no_opp_count = sum(
                count
                for decision, count in distribution.items()
                if "NO OPP" in decision
            )

            if total > 0:
                refund_pct = refund_count / total
                no_opp_pct = no_opp_count / total

                if refund_pct > 0.7:
                    score += 3.0
                    reasons.append(
                        f"Vertex category '{vertex_cat}' shows {
                            refund_pct:.0%} refund rate"
                    )
                    matched_patterns["vertex_category"] = (vertex_cat, refund_pct)
                elif no_opp_pct > 0.7:
                    score -= 2.0
                    reasons.append(
                        f"Vertex category '{vertex_cat}' shows {
                            no_opp_pct:.0%} no-opp rate"
                    )

        # Check material group
        material_group = invoice_data.get(
            "matk1_po_material_group_desc"
        ) or invoice_data.get("Material Group")
        if material_group and material_group in self.patterns["material_groups"]:
            distribution = self.patterns["material_groups"][material_group]
            total = sum(distribution.values())

            refund_count = sum(
                count
                for decision, count in distribution.items()
                if "REFUND" in decision
            )

            if total > 5:  # Only trust if we have enough samples
                refund_pct = refund_count / total
                if refund_pct > 0.6:
                    score += 1.5
                    reasons.append(
                        f"Material group '{material_group}' shows {
                            refund_pct:.0%} refund rate"
                    )
                    matched_patterns["material_group"] = (material_group, refund_pct)
                elif refund_pct < 0.2:
                    score -= 1.0
                    reasons.append(
                        f"Material group '{
                            material_group}' rarely refunds ({refund_pct:.0%})"
                    )

        # Check vendor history
        vendor = (
            invoice_data.get("Vendor Name")
            or invoice_data.get("vendor")
            or invoice_data.get("name1_po_vendor_name")
        )
        if vendor and vendor in self.patterns["vendor_patterns"]:
            distribution = self.patterns["vendor_patterns"][vendor]
            total = sum(distribution.values())

            if total > 3:
                refund_count = sum(
                    count
                    for decision, count in distribution.items()
                    if "REFUND" in decision
                )
                refund_pct = refund_count / total

                if refund_pct > 0.5:
                    score += 1.0
                    reasons.append(
                        f"Vendor '{vendor}' has {
                            refund_pct:.0%} refund rate ({total} samples)"
                    )
                    matched_patterns["vendor"] = (vendor, refund_pct)

        # Analyze description for keywords
        description = str(
            invoice_data.get("Description")
            or invoice_data.get("txz01_po_description")
            or ""
        )
        if description:
            desc_keywords = self._extract_keywords(description.lower())

            refund_keyword_score = sum(
                self.patterns["refund_keywords"].get(kw, 0) for kw in desc_keywords
            )
            no_opp_keyword_score = sum(
                self.patterns["no_opp_keywords"].get(kw, 0) for kw in desc_keywords
            )

            if refund_keyword_score > no_opp_keyword_score and refund_keyword_score > 5:
                score += 0.5
                top_kws = [
                    kw
                    for kw in desc_keywords
                    if self.patterns["refund_keywords"].get(kw, 0) > 2
                ]
                if top_kws:
                    reasons.append(
                        f"Description contains refund keywords: {
                            ', '.join(top_kws[:3])}"
                    )
            elif (
                no_opp_keyword_score > refund_keyword_score and no_opp_keyword_score > 5
            ):
                score -= 0.5
                reasons.append("Description contains no-opp keywords")

        # Determine final decision
        if score >= 2.0:
            decision = "LIKELY_REFUND"
            confidence = min(0.95, 0.5 + (score / 10))
        elif score <= -1.5:
            decision = "LIKELY_NO_OPP"
            confidence = min(0.90, 0.5 + (abs(score) / 10))
        else:
            decision = "UNCERTAIN"
            confidence = max(0.0, 0.5 - abs(score) / 5)

        return {
            "refund_decision": decision,
            "confidence": confidence,
            "score": score,
            "reasons": reasons if reasons else ["No strong patterns matched"],
            "matched_patterns": matched_patterns,
        }

    def get_top_refund_indicators(self, top_n: int = 20) -> Dict:
        """
        Get the top indicators of refund opportunities

        Returns:
            {
                'top_refund_keywords': [(keyword, count), ...],
                'top_no_opp_keywords': [(keyword, count), ...],
                'best_vertex_categories': [(category, refund_rate), ...],
                'best_material_groups': [(group, refund_rate), ...]
            }
        """
        # Top refund keywords
        top_refund_kw = sorted(
            self.patterns["refund_keywords"].items(), key=lambda x: x[1], reverse=True
        )[:top_n]

        # Top no-opp keywords
        top_no_opp_kw = sorted(
            self.patterns["no_opp_keywords"].items(), key=lambda x: x[1], reverse=True
        )[:top_n]

        # Best Vertex categories for refunds
        best_vertex = []
        for category, distribution in self.patterns["vertex_categories"].items():
            total = sum(distribution.values())
            if total >= 5:  # Minimum sample size
                refund_count = sum(
                    count
                    for decision, count in distribution.items()
                    if "REFUND" in decision
                )
                refund_rate = refund_count / total
                if refund_rate > 0.5:
                    best_vertex.append((category, refund_rate, total))

        best_vertex.sort(key=lambda x: (x[1], x[2]), reverse=True)

        # Best material groups for refunds
        best_materials = []
        for group, distribution in self.patterns["material_groups"].items():
            total = sum(distribution.values())
            if total >= 5:
                refund_count = sum(
                    count
                    for decision, count in distribution.items()
                    if "REFUND" in decision
                )
                refund_rate = refund_count / total
                if refund_rate > 0.5:
                    best_materials.append((group, refund_rate, total))

        best_materials.sort(key=lambda x: (x[1], x[2]), reverse=True)

        return {
            "top_refund_keywords": top_refund_kw,
            "top_no_opp_keywords": top_no_opp_kw,
            "best_vertex_categories": best_vertex[:top_n],
            "best_material_groups": best_materials[:top_n],
        }


if __name__ == "__main__":
    import sys

    print("Invoice Pattern Learning - Demo")
    print("=" * 70)

    # Train model
    learner = InvoicePatternLearner()

    if len(sys.argv) > 1:
        excel_file = sys.argv[1]
        learner.train_from_excel(excel_file)

        print("\n" + "=" * 70)
        print("TOP REFUND INDICATORS")
        print("=" * 70)

        indicators = learner.get_top_refund_indicators(top_n=10)

        print("\nTop 10 Refund Keywords:")
        for i, (kw, count) in enumerate(indicators["top_refund_keywords"], 1):
            print(f"  {i}. '{kw}': {count} occurrences")

        print("\nTop 10 No-Opp Keywords:")
        for i, (kw, count) in enumerate(indicators["top_no_opp_keywords"], 1):
            print(f"  {i}. '{kw}': {count} occurrences")

        print("\nBest Vertex Categories for Refunds:")
        for i, (cat, rate, count) in enumerate(indicators["best_vertex_categories"], 1):
            print(f"  {i}. '{cat}': {rate:.1%} refund rate ({count} samples)")

        print("\nBest Material Groups for Refunds:")
        for i, (group, rate, count) in enumerate(indicators["best_material_groups"], 1):
            print(f"  {i}. '{group}': {rate:.1%} refund rate ({count} samples)")

    else:
        print("\nUsage: python invoice_pattern_learning.py <excel_file>")
        print(
            "Example: python invoice_pattern_learning.py 'Test Data/Phase_3_2023_Use Tax_10-17-25.xlsx'"
        )
