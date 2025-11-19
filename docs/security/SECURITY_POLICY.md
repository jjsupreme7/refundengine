# Security Policy & PII Protection

## Overview

This document describes how the Refund Engine protects personally identifiable information (PII) and sensitive financial data in compliance with GDPR, CCPA, and industry best practices.

---

## 🔒 **Security Architecture**

The system implements **three layers of protection**:

1. **Detection** - Identify PII in documents before processing
2. **Redaction** - Remove PII before sending to external APIs
3. **Encryption** - Encrypt PII before database storage

---

## 📋 **What Data We Protect**

### Critical (Always Redacted/Encrypted)

| Data Type | Examples | Protection |
|-----------|----------|------------|
| **Bank Accounts** | Account: 123456789 | Redacted before API, Encrypted in DB |
| **Routing Numbers** | ABA: 026009593 | Redacted before API, Encrypted in DB |
| **Credit Cards** | 4532-1156-7890-1234 | Redacted before API, Never stored |
| **SSN** | 123-45-6789 | Redacted before API, Never stored |
| **Tax ID/EIN** | 12-3456789 | Redacted before API, Encrypted in DB |

### Moderate (Context-Dependent)

| Data Type | Examples | Protection |
|-----------|----------|------------|
| **Email (Personal)** | john.smith@company.com | Redacted before API, Encrypted in DB |
| **Phone (Personal)** | (425) 555-1234 | Redacted before API, Encrypted in DB |
| **Employee Names** | John Smith, CFO | Masked in exports, Encrypted if sensitive |

### Safe (Business Data - Not Protected)

| Data Type | Examples | Protection |
|-----------|----------|------------|
| **Company Names** | Boeing Corporation | None (public info) |
| **Business Addresses** | 100 N Riverside Plaza | None (public info) |
| **Department Emails** | invoices@company.com | None (public info) |
| **Product Info** | Microsoft 365 E5 | None (needed for analysis) |
| **Prices/Amounts** | $50,000 | None (needed for analysis) |
| **Invoice Numbers** | INV-2024-12345 | None (needed for tracking) |

---

## 🛡️ **Protection Mechanisms**

### 1. PII Detection (`PIIDetector`)

**Technology:** Microsoft Presidio + Custom Regex Patterns

**What it detects:**
- Bank account numbers (8-17 digits)
- ABA routing numbers (9 digits)
- Credit card numbers (Luhn validated)
- Social Security Numbers (XXX-XX-XXXX)
- Tax IDs/EINs (XX-XXXXXXX)
- Email addresses (personal)
- Phone numbers (personal)
- Person names (in sensitive contexts)

**Usage:**
```python
from core.security import PIIDetector

detector = PIIDetector()
findings = detector.detect(invoice_text)

# Example output:
# [
#   PIIFinding(type="BANK_ACCOUNT", value="123456789", start=45, end=54, confidence=0.85),
#   PIIFinding(type="EMAIL_ADDRESS", value="john@company.com", start=120, end=137, confidence=0.9)
# ]
```

---

### 2. Text Redaction (`Redactor`)

**Purpose:** Remove PII before sending to OpenAI API

**How it works:**
1. Detects all PII in invoice text
2. Replaces with placeholder tokens
3. Preserves business context needed for analysis
4. Logs redaction details for audit

**Example:**

**Before Redaction:**
```
INVOICE #12345
Boeing Corporation
Contact: john.smith@boeing.com
Account: 4532-1156-7890-1234
Wire to: ABA 026009593

Line Items:
1. Microsoft 365 E5 - $50,000
   Tax: $5,000
```

**After Redaction (sent to OpenAI):**
```
INVOICE #12345
Boeing Corporation
Contact: [REDACTED_EMAIL]
Account: [REDACTED_ACCOUNT]
Wire to: [REDACTED_ROUTING]

Line Items:
1. Microsoft 365 E5 - $50,000
   Tax: $5,000
```

**Usage:**
```python
from core.security import Redactor

redactor = Redactor()
safe_text, report = redactor.redact_invoice(invoice_text)

# Report includes:
# {
#   "redacted": True,
#   "pii_types_found": ["EMAIL_ADDRESS", "BANK_ACCOUNT", "ROUTING_NUMBER"],
#   "total_redactions": 3
# }
```

---

### 3. Field Encryption (`EncryptionService`)

**Purpose:** Encrypt PII before database storage

**Technology:** Fernet (AES-128 in CBC mode)

**What gets encrypted:**
- contact_email
- contact_phone
- approver_email
- bank_account (if stored)
- routing_number (if stored)
- tax_id

**Key Management:**
- Encryption key stored in `ENCRYPTION_KEY` environment variable
- **Never commit the key to version control**
- Key should be stored in secure vault (AWS Secrets Manager, Azure Key Vault, etc.)
- Generate new key: `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`

**Usage:**
```python
from core.security import EncryptionService

encryption = EncryptionService()

# Encrypt before storing
encrypted_email = encryption.encrypt("john.smith@company.com")
# Result: "gAAAAABh5Q2..."

# Decrypt when needed
decrypted_email = encryption.decrypt(encrypted_email)
# Result: "john.smith@company.com"
```

---

### 4. Excel Masking (`ExcelMasker`)

**Purpose:** Mask PII in Excel exports for safe sharing

**How it works:**
- Emails: `john.smith@company.com` → `john.s***@company.com`
- Phones: `(425) 555-1234` → `(***) ***-1234`
- Accounts: `123456789` → `****6789`
- Names: `John Smith` → `J*** S***`

**Usage:**
```python
from core.security import ExcelMasker

masker = ExcelMasker()

# Mask entire Excel file
masker.mask_excel_export(
    input_file="analysis_results.xlsx",
    output_file="analysis_results_safe.xlsx"
)

# Or mask DataFrame
masked_df = masker.mask_dataframe(df, column_mapping={
    "contact_email": "email",
    "contact_phone": "phone",
    "account_number": "account"
})
```

---

## 🔄 **Data Flow with PII Protection**

### Invoice Analysis Pipeline

```
1. Upload Invoice PDF
   ↓
2. Extract Text (GPT-4 Vision)
   ↓
3. [PII DETECTION] ← Scan for sensitive data
   ↓
4. [REDACTION] ← Remove PII from text
   ↓
5. Send to OpenAI (safe text only)
   ↓
6. Receive Analysis Results
   ↓
7. [ENCRYPTION] ← Encrypt sensitive fields
   ↓
8. Store in Database (encrypted PII)
   ↓
9. [MASKING] ← Mask PII in Excel export
   ↓
10. Export to Excel (masked data)
```

### What Goes Where

| Location | PII Status | Example |
|----------|-----------|---------|
| **Invoice PDF (original)** | Contains PII | Full bank account: 123456789 |
| **Extracted Text (memory)** | Contains PII | Full bank account: 123456789 |
| **Redacted Text (to API)** | **PII REMOVED** | [REDACTED_ACCOUNT] |
| **Database Storage** | **PII ENCRYPTED** | Encrypted blob: gAAAAABh5Q2... |
| **Excel Export** | **PII MASKED** | Masked account: ****6789 |

---

## 📊 **Audit & Compliance**

### Audit Logs

The system maintains three audit logs:

1. **PII Access Log** (`pii_access_log`)
   - Tracks every access to encrypted PII
   - Records who, when, why, and what
   - Retained for 7 years per compliance requirements

2. **PII Redaction Log** (`pii_redaction_log`)
   - Logs all redactions before API calls
   - Records PII types found (not values!)
   - Tracks which API received redacted data

3. **Audit Trail** (`audit_trail`)
   - General change tracking
   - Links to PII logs for sensitive operations

### Compliance Features

| Regulation | Requirement | Implementation |
|------------|-------------|----------------|
| **GDPR** | Right to be forgotten | Data retention policies + delete functions |
| **GDPR** | Data minimization | Only collect PII needed for tax analysis |
| **GDPR** | Encryption at rest | Fernet encryption for all PII fields |
| **CCPA** | Data access logging | PII access log with full audit trail |
| **CCPA** | Right to know | PII summary and export functions |
| **HIPAA** | Audit controls | Complete PII access logging |
| **SOC 2** | Access monitoring | Real-time PII access tracking |

---

## 🚨 **Security Best Practices**

### For Developers

1. **Never log PII**
   ```python
   # ❌ BAD
   print(f"Processing invoice for {customer_email}")

   # ✅ GOOD
   print(f"Processing invoice #{invoice_number}")
   ```

2. **Always redact before API calls**
   ```python
   # ❌ BAD
   result = openai.analyze(invoice_text)

   # ✅ GOOD
   redactor = Redactor()
   safe_text, _ = redactor.redact(invoice_text)
   result = openai.analyze(safe_text)
   ```

3. **Encrypt before database storage**
   ```python
   # ❌ BAD
   db.insert({"email": customer_email})

   # ✅ GOOD
   encryption = EncryptionService()
   db.insert({"email": encryption.encrypt(customer_email)})
   ```

4. **Mask before Excel export**
   ```python
   # ❌ BAD
   df.to_excel("results.xlsx")

   # ✅ GOOD
   masker = ExcelMasker()
   masked_df = masker.apply_safe_export_policy(df)
   masked_df.to_excel("results.xlsx")
   ```

### For System Administrators

1. **Secure the encryption key**
   - Store in secure vault (AWS Secrets Manager, Azure Key Vault)
   - Never commit to Git
   - Rotate annually
   - Use different keys for dev/staging/prod

2. **Monitor PII access**
   ```sql
   SELECT * FROM v_pii_access_summary
   WHERE access_date >= CURRENT_DATE - INTERVAL '7 days';
   ```

3. **Regular security audits**
   - Review PII access logs monthly
   - Check for unauthorized access patterns
   - Verify redaction effectiveness

4. **Data retention compliance**
   ```sql
   SELECT * FROM data_retention_policy;
   -- Ensure policies match legal requirements
   ```

---

## 🧪 **Testing PII Protection**

### Quick Test

```bash
source venv/bin/activate
python3 core/security/test_pii_protection.py
```

This will:
1. Test PII detection with sample data
2. Verify redaction effectiveness
3. Test encryption/decryption
4. Check Excel masking

### Manual Testing

```python
from core.security import PIIDetector, Redactor, EncryptionService, ExcelMasker

# Test detection
detector = PIIDetector()
test_text = "Contact john.smith@company.com, Account: 123456789"
findings = detector.detect(test_text)
print(f"Found {len(findings)} PII instances")

# Test redaction
redactor = Redactor()
safe_text, report = redactor.redact(test_text)
print(f"Redacted text: {safe_text}")
print(f"Report: {report}")

# Test encryption
encryption = EncryptionService()
encrypted = encryption.encrypt("sensitive data")
decrypted = encryption.decrypt(encrypted)
assert decrypted == "sensitive data"

# Test masking
masked = EncryptionService.mask_value("john.smith@company.com", "email")
print(f"Masked email: {masked}")  # john.s***@company.com
```

---

## 📞 **Incident Response**

### If PII is Accidentally Exposed

1. **Immediate Actions:**
   - Revoke API keys if sent to external service
   - Delete exposed files/exports
   - Check audit logs for access

2. **Investigation:**
   ```sql
   -- Check what was accessed
   SELECT * FROM pii_access_log
   WHERE access_timestamp >= '[incident_time]';

   -- Check what was redacted
   SELECT * FROM pii_redaction_log
   WHERE created_at >= '[incident_time]';
   ```

3. **Remediation:**
   - Notify affected parties (if required by GDPR/CCPA)
   - Document incident
   - Update procedures to prevent recurrence

4. **Legal Notifications (if required):**
   - GDPR: Within 72 hours of discovery
   - CCPA: Without unreasonable delay

---

## 🔗 **Related Documentation**

- [GDPR Compliance Checklist](./GDPR_COMPLIANCE.md)
- [CCPA Compliance Checklist](./CCPA_COMPLIANCE.md)
- [Data Retention Policy](./DATA_RETENTION_POLICY.md)
- [Incident Response Plan](./INCIDENT_RESPONSE.md)

---

## ✅ **Security Checklist for Production**

Before deploying to production:

- [ ] `ENCRYPTION_KEY` set in environment (not in code)
- [ ] PII detection enabled in analysis pipeline
- [ ] Redaction active before all API calls
- [ ] Database encryption active
- [ ] Excel masking applied to all exports
- [ ] Audit logging enabled
- [ ] Data retention policies configured
- [ ] Security testing passed
- [ ] Penetration testing completed
- [ ] Compliance review approved
- [ ] Incident response plan documented
- [ ] Team trained on PII handling

---

**Last Updated:** 2025-01-08

**Contact:** security@your-company.com
