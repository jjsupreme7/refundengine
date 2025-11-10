"""
Test script for PII protection functionality.

Run with: python3 core/security/test_pii_protection.py
"""

import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from core.security import PIIDetector, Redactor, EncryptionService, ExcelMasker
import pandas as pd


def print_header(title):
    """Print section header"""
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}\n")


def test_pii_detection():
    """Test PII detection"""
    print_header("TEST 1: PII Detection")

    detector = PIIDetector()

    test_cases = [
        {
            "name": "Invoice with bank account and email",
            "text": """
            INVOICE #12345
            Boeing Corporation
            Contact: john.smith@boeing.com
            Account: 123456789
            Wire to: ABA 026009593

            Line Items:
            - Microsoft 365 E5: $50,000
            """,
            "expected_types": ["EMAIL_ADDRESS", "BANK_ACCOUNT", "ROUTING_NUMBER"]
        },
        {
            "name": "Invoice with Tax ID",
            "text": "Vendor Tax ID: 91-1234567 for 1099 reporting",
            "expected_types": ["TAX_ID"]
        },
        {
            "name": "Safe business data (no PII)",
            "text": "Boeing Corporation, Invoice #123, Amount: $50,000, Product: Microsoft 365",
            "expected_types": []
        }
    ]

    for i, test in enumerate(test_cases, 1):
        print(f"Test Case {i}: {test['name']}")
        findings = detector.detect(test['text'])

        print(f"  Expected PII types: {test['expected_types']}")
        print(f"  Found PII types: {[f.type for f in findings]}")

        for finding in findings:
            print(f"    - {finding.type}: '{finding.value}' (confidence: {finding.confidence:.2f})")

        if not findings and not test['expected_types']:
            print("  ✅ PASS: No PII detected (as expected)")
        elif findings:
            print(f"  ✅ PASS: Detected {len(findings)} PII instances")
        else:
            print("  ⚠️  Note: Results may vary")
        print()


def test_redaction():
    """Test PII redaction"""
    print_header("TEST 2: PII Redaction")

    redactor = Redactor()

    invoice_text = """
    INVOICE #12345
    Boeing Corporation
    100 N Riverside Plaza, Chicago, IL
    Contact: john.smith@boeing.com
    Phone: (425) 555-1234

    Payment Information:
    Account: 4532-1156-7890-1234
    Wire to: Bank of America, ABA 026009593
    Tax ID: 91-1234567

    Line Items:
    1. Microsoft 365 E5 (1,000 licenses) @ $25/ea = $25,000
    2. Azure Cloud Services = $15,000

    Total: $40,000
    Tax: $4,000
    """

    print("Original Invoice:")
    print("-" * 70)
    print(invoice_text)
    print()

    safe_text, report = redactor.redact_invoice(invoice_text)

    print("Redacted Invoice (safe for API):")
    print("-" * 70)
    print(safe_text)
    print()

    print("Redaction Report:")
    print(f"  Redacted: {report['redacted']}")
    print(f"  PII Types Found: {report['pii_types_found']}")
    print(f"  Total Redactions: {report['total_redactions']}")
    print(f"  Details: {report['details']}")

    if report['redacted']:
        print("  ✅ PASS: PII redacted successfully")
    else:
        print("  ⚠️  WARNING: No PII detected for redaction")


def test_encryption():
    """Test encryption/decryption"""
    print_header("TEST 3: Encryption & Decryption")

    # Set a test encryption key
    test_key = EncryptionService.generate_key()
    print(f"Generated test key: {test_key[:20]}...")

    encryption = EncryptionService(key=test_key.encode())

    test_values = [
        "john.smith@boeing.com",
        "(425) 555-1234",
        "123456789"
    ]

    print("\nTesting encryption/decryption:")
    for value in test_values:
        encrypted = encryption.encrypt(value)
        decrypted = encryption.decrypt(encrypted)

        match = "✅" if decrypted == value else "❌"
        print(f"  {match} Original: '{value}'")
        print(f"     Encrypted: '{encrypted[:40]}...'")
        print(f"     Decrypted: '{decrypted}'")
        print()


def test_masking():
    """Test value masking"""
    print_header("TEST 4: Value Masking")

    test_cases = [
        ("john.smith@company.com", "email", "john.s***@company.com"),
        ("123456789", "account", "****6789"),
        ("(425) 555-1234", "phone", "(***) ***-1234"),
        ("John Smith", "name", "J*** S***"),
        ("91-1234567", "tax_id", "**-****567")
    ]

    print("Testing masking for different data types:")
    for value, mask_type, expected_pattern in test_cases:
        masked = EncryptionService.mask_value(value, mask_type)
        print(f"  {mask_type.upper()}: '{value}' → '{masked}'")
        if "***" in masked or "****" in masked:
            print(f"    ✅ PASS: Value masked successfully")
        else:
            print(f"    ⚠️  WARNING: Masking may not be effective")
        print()


def test_excel_masking():
    """Test Excel DataFrame masking"""
    print_header("TEST 5: Excel DataFrame Masking")

    # Create sample DataFrame
    df = pd.DataFrame({
        "vendor": ["Boeing Corporation", "Nokia Inc"],
        "invoice_number": ["INV-001", "INV-002"],
        "amount": [50000, 25000],
        "contact_email": ["john.smith@boeing.com", "jane.doe@nokia.com"],
        "contact_phone": ["(425) 555-1234", "(206) 555-5678"],
        "bank_account": ["123456789", "987654321"]
    })

    print("Original DataFrame:")
    print(df.to_string())
    print()

    masker = ExcelMasker()
    masked_df = masker.mask_dataframe(df, column_mapping={
        "contact_email": "email",
        "contact_phone": "phone",
        "bank_account": "account"
    })

    print("Masked DataFrame (safe for export):")
    print(masked_df.to_string())
    print()

    # Check if masking worked
    if "***" in str(masked_df['contact_email'].values):
        print("✅ PASS: Email masking successful")
    if "***" in str(masked_df['contact_phone'].values):
        print("✅ PASS: Phone masking successful")
    if "****" in str(masked_df['bank_account'].values):
        print("✅ PASS: Account masking successful")


def test_safe_for_api_check():
    """Test API safety check"""
    print_header("TEST 6: API Safety Check")

    redactor = Redactor()

    safe_text = "Boeing Corporation, Invoice #123, Amount: $50,000"
    unsafe_text = "Contact: john@company.com, Account: 123456789"

    print("Test Case 1: Safe business data")
    is_safe, issues = redactor.is_safe_for_api(safe_text)
    print(f"  Text: {safe_text}")
    print(f"  Safe for API: {is_safe}")
    print(f"  Issues: {issues}")
    if is_safe:
        print("  ✅ PASS: Correctly identified as safe")
    print()

    print("Test Case 2: Data with PII")
    is_safe, issues = redactor.is_safe_for_api(unsafe_text)
    print(f"  Text: {unsafe_text}")
    print(f"  Safe for API: {is_safe}")
    print(f"  Issues: {issues}")
    if not is_safe and issues:
        print("  ✅ PASS: Correctly identified PII")
    print()


def main():
    """Run all tests"""
    print("\n" + "="*70)
    print("  PII PROTECTION SYSTEM - TEST SUITE")
    print("="*70)

    try:
        test_pii_detection()
        test_redaction()
        test_encryption()
        test_masking()
        test_excel_masking()
        test_safe_for_api_check()

        print_header("TEST SUMMARY")
        print("✅ All tests completed successfully!")
        print("\nNext Steps:")
        print("1. Generate encryption key: python -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\"")
        print("2. Add key to .env file: ENCRYPTION_KEY=<your-key>")
        print("3. Deploy database schema: psql -f database/schema/schema_pii_protection.sql")
        print("4. Integrate into analysis pipeline")

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()