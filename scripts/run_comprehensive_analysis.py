#!/usr/bin/env python3
"""
Run analysis on comprehensive test data and populate OUTPUT columns.

This script:
1. Reads Master_Claim_Sheet_Comprehensive.xlsx
2. For each row, runs AI analysis (simulated for now with realistic outputs)
3. Populates OUTPUT columns
4. Saves analyzed Excel for dashboard preview
"""

import pandas as pd
import random
from pathlib import Path

# Controlled vocabularies
TAX_CATEGORIES = [
    "Custom Software", "DAS", "DAS/License", "Digital Goods",
    "Hardware Support", "License", "Services", "Services/Tangible Goods",
    "Software Maintenance", "Software Support", "Tangible Goods"
]

ADDITIONAL_INFO = [
    "Professional", "Hosting", "Software Development/Configuration",
    "Installation", "Construction", "Telecommunications", "Testing"
]

REFUND_BASIS = [
    "MPU", "Non-Taxable",
    "Special Category Non-Taxable (Services in Respect to Construction)",
    "Out-of-State Services", "Wrong Rate", "Resale"
]


def analyze_line_item(row: pd.Series) -> dict:
    """
    Simulate AI analysis for a single line item.

    For demo purposes, uses rule-based logic similar to what AI would do.
    """

    desc = row['Line_Item_Description']
    amount = row['Total_Amount']
    tax_amount = row['Tax_Amount']
    tax_remitted = row['Tax_Remitted']
    vendor = row['Vendor_Name']
    tax_type = row['Tax_Type']

    # Analyze based on description keywords
    desc_lower = desc.lower()

    # Determine category and refund basis
    if 'custom' in desc_lower and ('development' in desc_lower or 'integration' in desc_lower or 'configuration' in desc_lower):
        category = "Custom Software"
        additional = "Software Development/Configuration"
        basis = "Non-Taxable"
        decision = "Add to Claim - Custom Software Exemption"
        confidence = 92
        citation = "WAC 458-20-15502(3)(a)"
        notes = f"Custom software development services are exempt under WAC 458-20-15502(3)(a). {vendor} provided {desc[:50]}... which qualifies as custom programming."

    elif 'professional' in desc_lower or 'consulting' in desc_lower or 'advisory' in desc_lower:
        # Check for odd dollar amount (hidden tax indicator)
        if amount % 1 != 0 and tax_amount == 0:
            # Odd amount like $55,250 suggests $50,000 + 10.5% tax
            implied_base = round(amount / 1.105, 2)
            implied_tax = amount - implied_base
            category = "Services"
            additional = "Professional"
            basis = "Non-Taxable"
            decision = "Add to Claim - Non-Taxable Professional Services"
            confidence = 88
            citation = "WAC 458-20-144"
            notes = f"Professional services are non-taxable. ANOMALY DETECTED: Odd dollar amount ${amount:,.2f} suggests hidden tax. Implied base: ${implied_base:,.2f}, implied tax: ${implied_tax:,.2f}. Professional consulting services do not constitute retail sales under WAC 458-20-144."
        else:
            category = "Services"
            additional = "Professional"
            basis = "Non-Taxable"
            decision = "Add to Claim - Non-Taxable Professional Services"
            confidence = 94
            citation = "WAC 458-20-144"
            notes = f"Professional {desc[:30]}... services are exempt from sales tax under WAC 458-20-144."

    elif 'hosting' in desc_lower or 'cloud' in desc_lower:
        category = "Digital Goods"
        additional = "Hosting"
        basis = "Non-Taxable"
        decision = "Add to Claim - Digital Goods Exemption"
        confidence = 90
        citation = "RCW 82.04.050(6)"
        notes = f"Cloud hosting services qualify as digital goods and are exempt under RCW 82.04.050(6). {vendor}'s hosting services do not constitute taxable retail sales."

    elif 'license' in desc_lower and 'custom' not in desc_lower:
        category = "License"
        additional = None
        basis = None
        decision = "Do Not Add to Claim - Correctly Taxed"
        confidence = 95
        citation = "WAC 458-20-15502"
        notes = f"Prewritten software licenses are taxable under WAC 458-20-15502. Tax correctly applied."

    elif 'hardware' in desc_lower or 'server' in desc_lower or 'tablet' in desc_lower:
        category = "Tangible Goods"
        additional = None
        basis = None
        decision = "Do Not Add to Claim - Correctly Taxed"
        confidence = 97
        citation = "RCW 82.08.020"
        notes = f"Tangible personal property (hardware) is taxable under RCW 82.08.020. Tax correctly applied."

    elif 'installation' in desc_lower or 'setup' in desc_lower:
        if tax_amount > 0:
            category = "Services"
            additional = "Installation"
            basis = "Non-Taxable"
            decision = "Add to Claim - Installation Services Exempt"
            confidence = 85
            citation = "WAC 458-20-111"
            notes = f"Installation services when separately stated may be exempt under WAC 458-20-111. Requires review of invoice to confirm separate billing."
        else:
            category = "Services"
            additional = "Installation"
            basis = None
            decision = "Do Not Add to Claim - Correctly Exempt"
            confidence = 93
            citation = "WAC 458-20-111"
            notes = f"Installation services correctly exempted."

    elif 'maintenance' in desc_lower or 'support' in desc_lower:
        category = "Software Maintenance"
        additional = None
        basis = "Non-Taxable"
        decision = "Add to Claim - Software Maintenance Exemption"
        confidence = 91
        citation = "WAC 458-20-15502(3)(c)"
        notes = f"Software maintenance and support agreements are exempt under WAC 458-20-15502(3)(c)."

    elif 'construction' in desc_lower or 'progress payment' in desc_lower or 'retainage' in desc_lower:
        # Check for retainage issue
        if 'retainage' in desc_lower and tax_amount == 0:
            category = "Services"
            additional = "Construction"
            basis = "Special Category Non-Taxable (Services in Respect to Construction)"
            decision = "Add to Claim - Construction Retainage Tax Overpayment"
            confidence = 78
            citation = "WAC 458-20-170"
            notes = f"CONSTRUCTION RETAINAGE ISSUE: Retainage amount should not have been taxed upfront. Tax was charged on full PO amount including retainage. Refund due on retainage portion per WAC 458-20-170."
        else:
            category = "Services"
            additional = "Construction"
            basis = None
            decision = "Needs Review - Construction Tax Rules Complex"
            confidence = 72
            citation = "WAC 458-20-170"
            notes = f"Construction contracts have complex tax rules under WAC 458-20-170. Requires manual review of contract terms and payment structure."

    elif 'training' in desc_lower or 'workshop' in desc_lower:
        category = "Services"
        additional = "Professional"
        basis = "Non-Taxable"
        decision = "Add to Claim - Training Services Exempt"
        confidence = 89
        citation = "WAC 458-20-244"
        notes = f"Training and educational services are exempt under WAC 458-20-244."

    elif 'testing' in desc_lower or 'quality assurance' in desc_lower:
        category = "Services"
        additional = "Testing"
        basis = "Non-Taxable"
        decision = "Add to Claim - Testing Services Exempt"
        confidence = 87
        citation = "WAC 458-20-244"
        notes = f"Testing and QA services as professional services are exempt."

    elif tax_type == "Use Tax" and tax_amount > 0:
        # Use tax scenario - check if services should be exempt
        if 'services' in desc_lower or 'implementation' in desc_lower:
            category = "Services"
            additional = "Professional"
            basis = "Out-of-State Services"
            decision = "Add to Claim - Use Tax on Exempt Services"
            confidence = 86
            citation = "WAC 458-20-178"
            notes = f"USE TAX SCENARIO: Services performed out-of-state are not subject to WA use tax under WAC 458-20-178. Refund of self-assessed use tax warranted."
        else:
            category = "Tangible Goods"
            additional = None
            basis = None
            decision = "Do Not Add to Claim - Use Tax Correctly Self-Assessed"
            confidence = 92
            citation = "RCW 82.12.020"
            notes = f"Use tax correctly self-assessed on goods shipped from out-of-state per RCW 82.12.020."

    else:
        # Default case
        category = "Services"
        additional = None
        basis = "Non-Taxable"
        decision = "Needs Review - Unclear Category"
        confidence = 65
        citation = "Requires manual review"
        notes = f"Unable to definitively categorize. Description: {desc[:100]}. Requires manual analyst review."

    # Calculate estimated refund
    if "Add to Claim" in decision:
        if tax_amount > 0:
            estimated_refund = tax_amount
        elif amount % 1 != 0:  # Odd dollar amount - hidden tax
            estimated_refund = round(amount - (amount / 1.105), 2)
        else:
            estimated_refund = 0
    else:
        estimated_refund = 0

    return {
        'Analysis_Notes': notes,
        'Final_Decision': decision,
        'Tax_Category': category,
        'Additional_Info': additional if additional else "",
        'Refund_Basis': basis if basis else "",
        'Estimated_Refund': estimated_refund,
        'Legal_Citation': citation,
        'AI_Confidence': confidence
    }


def main():
    """Run analysis on comprehensive test data."""

    print("=" * 80)
    print("RUNNING COMPREHENSIVE ANALYSIS")
    print("=" * 80)

    # Read Excel
    input_file = Path("test_data/Master_Claim_Sheet_Comprehensive.xlsx")
    df = pd.read_excel(input_file)

    print(f"\n📊 Loaded {len(df)} transactions from {input_file.name}")
    print(f"   Invoices: {df['Invoice_Number'].nunique()}")
    print(f"   POs: {df['Purchase_Order_Number'].nunique()}")
    print(f"   Vendors: {df['Vendor_Name'].nunique()}")

    print("\n🤖 Running AI analysis...")

    # Analyze each row
    for idx, row in df.iterrows():
        result = analyze_line_item(row)

        # Populate OUTPUT columns
        for col, value in result.items():
            df.at[idx, col] = value

        # Progress
        if (idx + 1) % 5 == 0:
            print(f"   Analyzed {idx + 1}/{len(df)} rows...")

    print(f"   ✅ Analyzed all {len(df)} rows")

    # Save analyzed Excel
    output_file = Path("test_data/Master_Claim_Sheet_ANALYZED.xlsx")
    df.to_excel(output_file, index=False)

    print(f"\n💾 Saved analyzed data: {output_file}")

    # Summary statistics
    print("\n" + "=" * 80)
    print("ANALYSIS SUMMARY")
    print("=" * 80)

    decisions = df['Final_Decision'].value_counts()
    print("\n📋 Decisions:")
    for decision, count in decisions.items():
        print(f"   {decision}: {count}")

    avg_confidence = df['AI_Confidence'].mean()
    print(f"\n📊 Average Confidence: {avg_confidence:.1f}%")

    flagged = len(df[df['AI_Confidence'] < 90])
    print(f"   Flagged for Review (<90%): {flagged} ({flagged/len(df)*100:.1f}%)")

    total_refund = df['Estimated_Refund'].sum()
    print(f"\n💰 Total Estimated Refund: ${total_refund:,.2f}")

    # Save summary
    summary = {
        'Total Rows': len(df),
        'Avg Confidence': avg_confidence,
        'Flagged for Review': flagged,
        'Total Refund': total_refund
    }

    with open('test_data/ANALYSIS_SUMMARY.txt', 'w') as f:
        f.write("COMPREHENSIVE ANALYSIS SUMMARY\n")
        f.write("=" * 60 + "\n\n")
        for key, value in summary.items():
            f.write(f"{key}: {value}\n")

    print("\n✅ Analysis complete!")
    print(f"   Analyzed Excel: {output_file}")
    print(f"   Summary: test_data/ANALYSIS_SUMMARY.txt")

    print("\n" + "=" * 80)
    print("NEXT STEP: Load into dashboard for preview")
    print("=" * 80)


if __name__ == '__main__':
    main()
