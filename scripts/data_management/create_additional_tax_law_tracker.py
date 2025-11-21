#!/usr/bin/env python3
"""
Create Excel Tracker for Additional Tax Law Documents

This script:
1. Analyzes "new WA tax law" folder (ESSB 5814 guidance)
2. Analyzes "Additional Tax Law" folder (ETAs + other guidance)
3. Creates comprehensive Excel tracker with categorization
"""

import os
import re
from datetime import datetime
from pathlib import Path

import pandas as pd

# Paths
new_wa_tax_law_path = "/Users/jacoballen/Desktop/new WA tax law"
additional_tax_law_path = "/Users/jacoballen/Desktop/Additional Tax Law"
essb_kb_path = "/Users/jacoballen/Desktop/refund-engine/knowledge_base/states/washington/essb_5814_oct_2025"

output_excel = "/Users/jacoballen/Desktop/refund-engine/knowledge_base/states/washington/Additional_Tax_Law_Tracker.xlsx"


def classify_document(filename: str) -> dict:
    """Classify document and extract metadata"""

    # Default classification
    classification = {
        "filename": filename,
        "document_type": "Other Guidance",
        "citation": None,
        "category": "General",
        "law_category": "guidance",
        "effective_date": "2024-01-01",  # Default to old law
        "topic_tags": [],
        "notes": "",
    }

    filename_lower = filename.lower()

    # ETA Detection (4-digit numbers)
    if re.match(r"^\d{4}\.pdf$", filename):
        eta_num = filename.replace(".pd", "")
        classification.update(
            {
                "document_type": "ETA",
                "citation": f"ETA {eta_num}",
                "category": "Excise Tax Advisory",
                "law_category": "advisory",
                "notes": "Excise Tax Advisory - interpretive statement",
            }
        )

    # ESSB 5814 Detection
    elif "essb" in filename_lower or "5814" in filename_lower:
        classification.update(
            {
                "document_type": "ESSB 5814 Guidance",
                "citation": "ESSB 5814 Guidance",
                "category": "New Law (Oct 2025)",
                "law_category": "new_law",
                "effective_date": "2025-10-01",
                "notes": "ESSB 5814 - Services newly taxable Oct 1, 2025",
            }
        )

        # Extract specific service type
        if "advertising" in filename_lower:
            classification["topic_tags"] = ["advertising", "essb_5814"]
        elif (
            "it services" in filename_lower
            or "information technology" in filename_lower
        ):
            classification["topic_tags"] = ["it_services", "essb_5814"]
        elif "custom software" in filename_lower or "software" in filename_lower:
            classification["topic_tags"] = ["custom_software", "essb_5814"]
        elif "website" in filename_lower:
            classification["topic_tags"] = ["website_development", "essb_5814"]
        elif "security" in filename_lower:
            classification["topic_tags"] = ["security_services", "essb_5814"]
        elif "staffing" in filename_lower or "temporary" in filename_lower:
            classification["topic_tags"] = ["temporary_staffing", "essb_5814"]
        elif "live presentations" in filename_lower or "presentation" in filename_lower:
            classification["topic_tags"] = ["live_presentations", "essb_5814"]
        elif "das" in filename_lower or "digital automated" in filename_lower:
            classification["topic_tags"] = ["digital_automated_services", "essb_5814"]

    # Tax Type Guides (numbered guides)
    elif re.match(r"^\d{2}_.*\.pdf$", filename):
        guide_name = filename.replace(".pd", "").split("_", 1)[1].replace("_", " ")
        classification.update(
            {
                "document_type": "Tax Type Guide",
                "citation": f"Tax Guide - {guide_name}",
                "category": "Tax Type Reference",
                "law_category": "guide",
                "notes": f"Comprehensive guide on {guide_name}",
            }
        )

        # Extract tax type
        if "sales" in filename_lower or "retail" in filename_lower:
            classification["topic_tags"] = ["sales_tax", "use_tax"]
        elif "property" in filename_lower:
            classification["topic_tags"] = ["property_tax"]
        elif "estate" in filename_lower:
            classification["topic_tags"] = ["estate_tax"]
        elif "fuel" in filename_lower:
            classification["topic_tags"] = ["fuel_tax"]

    # Industry Guides
    elif "_tax_guide" in filename_lower or "tax_guide" in filename_lower:
        industry = (
            filename.replace("_tax_guide.pd", "").replace(".pd", "").replace("_", " ")
        )
        classification.update(
            {
                "document_type": "Industry Guide",
                "citation": f"{industry.title()} Tax Guide",
                "category": "Industry Guidance",
                "law_category": "industry_guide",
                "topic_tags": [industry.lower().replace(" ", "_")],
            }
        )

    # External Documents
    elif filename.startswith("_External_"):
        classification.update(
            {
                "document_type": "External Content",
                "category": "News/Updates",
                "law_category": "external",
                "notes": "External news or update",
            }
        )

    # Capital Gains related
    elif "capital gains" in filename_lower or "capitalgains" in filename_lower:
        classification.update(
            {
                "document_type": "Capital Gains Guide",
                "category": "Capital Gains Tax",
                "law_category": "capital_gains",
                "topic_tags": ["capital_gains", "income_tax"],
            }
        )

    # General topic-based classification
    else:
        # Try to extract topic from filename
        topics = []
        if "software" in filename_lower:
            topics.append("software")
        if "saas" in filename_lower:
            topics.append("saas")
        if "service" in filename_lower:
            topics.append("services")
        if "tax" in filename_lower:
            topics.append("taxation")

        if topics:
            classification["topic_tags"] = topics

        classification["notes"] = "General tax guidance document"

    return classification


def main():
    """Create comprehensive Excel tracker"""

    print("=" * 80)
    print("Creating Additional Tax Law Document Tracker")
    print("=" * 80)
    print()

    all_documents = []

    # 1. Process ESSB 5814 documents (already in knowledge base + new ones)
    print("Step 1: Processing ESSB 5814 documents...")
    if os.path.exists(essb_kb_path):
        essb_files = [f for f in os.listdir(essb_kb_path) if f.endswith(".pd")]
        print(f"  Found {len(essb_files)} ESSB 5814 PDFs")

        for filename in sorted(essb_files):
            doc = classify_document(filename)
            doc["source_folder"] = "ESSB 5814 (Knowledge Base)"
            doc["file_path"] = (
                f"knowledge_base/states/washington/essb_5814_oct_2025/{filename}"
            )
            doc["status"] = (
                "Ready to Ingest"
                if not filename.startswith("0")
                else "Already Ingested"
            )
            all_documents.append(doc)

    # 2. Process Additional Tax Law folder
    print("\nStep 2: Processing Additional Tax Law folder...")
    if os.path.exists(additional_tax_law_path):
        additional_files = [
            f for f in os.listdir(additional_tax_law_path) if f.endswith(".pd")
        ]
        print(f"  Found {len(additional_files)} documents")

        # Categorize
        etas = [f for f in additional_files if re.match(r"^\d{4}\.pdf$", f)]
        tax_guides = [f for f in additional_files if re.match(r"^\d{2}_.*\.pdf$", f)]
        other = [f for f in additional_files if f not in etas and f not in tax_guides]

        print(f"    - ETAs: {len(etas)}")
        print(f"    - Tax Type Guides: {len(tax_guides)}")
        print(f"    - Other Guidance: {len(other)}")

        for filename in sorted(additional_files):
            doc = classify_document(filename)
            doc["source_folder"] = "Additional Tax Law (Desktop)"

            # Determine destination
            if doc["document_type"] == "ETA":
                doc["file_path"] = f"knowledge_base/states/washington/ETAs/{filename}"
            else:
                doc["file_path"] = (
                    f"knowledge_base/states/washington/other_guidance/{filename}"
                )

            doc["status"] = "Not Yet Ingested"
            all_documents.append(doc)

    # 3. Create DataFrame
    print("\nStep 3: Creating Excel tracker...")
    df = pd.DataFrame(all_documents)

    # Reorder columns
    column_order = [
        "status",
        "filename",
        "document_type",
        "citation",
        "category",
        "law_category",
        "effective_date",
        "topic_tags",
        "source_folder",
        "file_path",
        "notes",
    ]

    df = df[column_order]

    # Create Excel with multiple sheets
    with pd.ExcelWriter(output_excel, engine="openpyxl") as writer:
        # Sheet 1: All Documents
        df.to_excel(writer, sheet_name="All Documents", index=False)

        # Sheet 2: ESSB 5814 Only
        essb_df = df[df["document_type"].str.contains("ESSB", case=False, na=False)]
        essb_df.to_excel(writer, sheet_name="ESSB 5814 Documents", index=False)

        # Sheet 3: ETAs Only
        eta_df = df[df["document_type"] == "ETA"]
        eta_df.to_excel(writer, sheet_name="ETAs", index=False)

        # Sheet 4: Tax Guides
        guides_df = df[df["document_type"].isin(["Tax Type Guide", "Industry Guide"])]
        guides_df.to_excel(writer, sheet_name="Tax Guides", index=False)

        # Sheet 5: Other Guidance
        other_df = df[
            ~df["document_type"].isin(["ETA", "Tax Type Guide", "Industry Guide"])
            & ~df["document_type"].str.contains("ESSB", case=False, na=False)
        ]
        other_df.to_excel(writer, sheet_name="Other Guidance", index=False)

        # Sheet 6: Summary
        summary_data = {
            "Category": [
                "ESSB 5814 Documents",
                "ETAs",
                "Tax Type Guides",
                "Industry Guides",
                "Other Guidance",
                "External Content",
                "Total Documents",
            ],
            "Count": [
                len(essb_df),
                len(eta_df),
                len(df[df["document_type"] == "Tax Type Guide"]),
                len(df[df["document_type"] == "Industry Guide"]),
                len(other_df),
                len(df[df["document_type"] == "External Content"]),
                len(df),
            ],
            "Status": [
                f"{len(essb_df[essb_df['status'].str.contains(
                    'Ingested', na=False)])} ingested",
                f"{len(eta_df[eta_df['status'].str.contains(
                    'Ingested', na=False)])} ingested",
                "Not ingested",
                "Not ingested",
                "Not ingested",
                "Not ingested",
                f"{len(df[df['status'].str.contains('Ingested', na=False)])} ingested",
            ],
        }
        summary_df = pd.DataFrame(summary_data)
        summary_df.to_excel(writer, sheet_name="Summary", index=False)

    print(f"\n✅ Excel tracker created: {output_excel}")
    print()
    print("=" * 80)
    print("Summary:")
    print("=" * 80)
    print(f"Total Documents: {len(df)}")
    print(f"  - ESSB 5814: {len(essb_df)}")
    print(f"  - ETAs: {len(eta_df)}")
    print(f"  - Tax Guides: {len(guides_df)}")
    print(f"  - Other: {len(other_df)}")
    print()
    print("Sheets created:")
    print("  1. All Documents")
    print("  2. ESSB 5814 Documents")
    print("  3. ETAs")
    print("  4. Tax Guides")
    print("  5. Other Guidance")
    print("  6. Summary")
    print()


if __name__ == "__main__":
    main()
