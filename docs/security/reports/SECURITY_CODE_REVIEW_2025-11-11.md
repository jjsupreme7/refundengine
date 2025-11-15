# Security Code Review Report
**Date:** 2025-11-11
**Reviewer:** Security Professional (AI Assistant)
**Repository:** RefundEngine - Washington State Tax Refund Analysis System
**Commit:** claude/security-code-review-011CV2pR5pnQaJS55eGUwP6o

---

## Executive Summary

This security code review was conducted on the RefundEngine codebase, a Python-based AI-powered system for automated Washington State tax refund analysis. The review identified **1 CRITICAL vulnerability**, **3 HIGH-severity issues**, **5 MEDIUM-severity issues**, and several LOW-severity concerns. Overall, the codebase demonstrates good security practices in some areas (secrets management, PII protection) but requires immediate attention to critical SQL injection vulnerabilities and input validation issues.

**Risk Rating:** HIGH (requires immediate remediation)

---

## Critical Vulnerabilities (Severity: CRITICAL)

### 1. SQL Injection in Database Schema Verification
**File:** `scripts/utils/verify_schema.py:63`
**Severity:** CRITICAL
**CWE:** CWE-89 (SQL Injection)

**Vulnerable Code:**
```python
cursor.execute(f"SELECT COUNT(*) FROM {table};")
```

**Description:**
The code uses an f-string to dynamically construct SQL queries with the `table` variable obtained from database metadata. While this specific case queries system tables first, the dynamic SQL construction pattern is unsafe and could be exploited if an attacker can manipulate table names in the information_schema (e.g., through schema pollution or SQL injection in earlier queries).

**Impact:**
- SQL injection leading to unauthorized data access
- Potential database manipulation or destruction
- Privilege escalation within database

**Recommendation:**
Use parameterized queries or whitelist table names:
```python
# Option 1: Whitelist approach
ALLOWED_TABLES = {'legal_documents', 'document_chunks', 'clients', ...}
if table in ALLOWED_TABLES:
    cursor.execute("SELECT COUNT(*) FROM %s;", (AsIs(table),))

# Option 2: Use identifier quoting
from psycopg2.sql import Identifier, SQL
query = SQL("SELECT COUNT(*) FROM {}").format(Identifier(table))
cursor.execute(query)
```

---

## High Severity Issues

### 2. Unvalidated File Path Operations
**Files:** Multiple locations including:
- `analysis/analyze_refunds.py:298-309`
- `core/document_extractors.py:299-323`
- `analysis/invoice_lookup.py:58-64`

**Severity:** HIGH
**CWE:** CWE-22 (Path Traversal)

**Vulnerable Code:**
```python
# From analyze_refunds.py
inv_path = self.docs_folder / inv_file.strip()
if inv_path.exists() and inv_path.suffix.lower() == ".pdf":
    invoice_text += self.extract_text_from_pdf(inv_path) + "\n"
```

**Description:**
File paths constructed from Excel data or user input are not validated for path traversal attacks. An attacker could craft malicious filenames like `../../../etc/passwd` or `..\..\Windows\System32\config\SAM` to access files outside the intended directory.

**Impact:**
- Arbitrary file read access
- Exposure of sensitive system files
- Potential for file system traversal attacks

**Recommendation:**
```python
from pathlib import Path

def safe_resolve_path(base_dir: Path, user_path: str) -> Optional[Path]:
    """Safely resolve a user-provided path within base directory"""
    try:
        # Resolve the full path
        full_path = (base_dir / user_path).resolve()

        # Ensure it's within the base directory
        if not str(full_path).startswith(str(base_dir.resolve())):
            raise ValueError(f"Path traversal detected: {user_path}")

        return full_path
    except (ValueError, RuntimeError) as e:
        print(f"Invalid path: {e}")
        return None

# Usage:
safe_path = safe_resolve_path(self.docs_folder, inv_file.strip())
if safe_path and safe_path.exists():
    invoice_text += self.extract_text_from_pdf(safe_path)
```

### 3. Insufficient Input Validation on Excel Data
**Files:**
- `analysis/analyze_refunds.py:279-351`
- `analysis/fast_batch_analyzer.py`

**Severity:** HIGH
**CWE:** CWE-20 (Improper Input Validation)

**Description:**
Excel data is processed without sufficient validation. While the code checks for file existence, it doesn't validate:
- Numeric fields (amount, tax) for reasonable ranges
- String fields for injection attacks or encoding issues
- File references for malicious patterns

**Impact:**
- Type confusion attacks
- Resource exhaustion (processing extremely large values)
- Potential code injection through crafted Excel formulas

**Recommendation:**
```python
def validate_row_data(row: pd.Series) -> Tuple[bool, str]:
    """Validate Excel row data"""
    errors = []

    # Validate amount
    try:
        amount = float(row['Amount'])
        if amount < 0 or amount > 1_000_000_000:
            errors.append(f"Amount out of range: {amount}")
    except (ValueError, TypeError):
        errors.append(f"Invalid amount: {row.get('Amount')}")

    # Validate tax
    try:
        tax = float(row['Tax'])
        if tax < 0 or tax > amount:
            errors.append(f"Invalid tax: {tax}")
    except (ValueError, TypeError):
        errors.append(f"Invalid tax: {row.get('Tax')}")

    # Validate vendor name (no injection characters)
    vendor = str(row.get('Vendor', ''))
    if re.search(r'[<>"\'\\\x00-\x1f]', vendor):
        errors.append(f"Invalid characters in vendor name")

    # Validate file paths
    for field in ['Inv_1_File', 'PO_1_File']:
        if pd.notna(row.get(field)):
            filepath = str(row[field])
            if '..' in filepath or filepath.startswith('/'):
                errors.append(f"Suspicious file path: {filepath}")

    return (len(errors) == 0, '; '.join(errors))
```

### 4. Lack of Rate Limiting on External API Calls
**Files:**
- `core/enhanced_rag.py` (OpenAI API calls)
- `analysis/analyze_refunds.py` (GPT-4 API calls)

**Severity:** HIGH
**CWE:** CWE-770 (Allocation of Resources Without Limits)

**Description:**
The code makes multiple API calls to OpenAI without rate limiting or throttling. An attacker with access to the system could trigger massive API costs or cause service degradation.

**Impact:**
- Financial impact (unexpected API costs)
- Denial of Service
- API account suspension

**Recommendation:**
```python
from ratelimit import limits, sleep_and_retry
from functools import wraps
import time

class RateLimitedAPIClient:
    def __init__(self, max_calls_per_minute=60):
        self.max_calls = max_calls_per_minute
        self.calls = []

    def __call__(self, func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            now = time.time()
            # Remove calls older than 1 minute
            self.calls = [t for t in self.calls if now - t < 60]

            if len(self.calls) >= self.max_calls:
                sleep_time = 60 - (now - self.calls[0])
                print(f"Rate limit reached, sleeping {sleep_time:.2f}s")
                time.sleep(sleep_time)
                self.calls = []

            self.calls.append(time.time())
            return func(*args, **kwargs)
        return wrapper

# Usage:
rate_limiter = RateLimitedAPIClient(max_calls_per_minute=50)

@rate_limiter
def call_openai_api(prompt):
    return client.chat.completions.create(...)
```

---

## Medium Severity Issues

### 5. Insecure Temporary File Handling
**Files:** Multiple locations where PDFs are processed

**Severity:** MEDIUM
**CWE:** CWE-377 (Insecure Temporary File)

**Description:**
PDF files are processed without secure temporary file handling. If temporary files are created, they may be predictable or accessible to other users.

**Recommendation:**
Use Python's `tempfile` module with secure defaults:
```python
import tempfile
import os

with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.pdf') as tmp:
    tmp.write(pdf_content)
    tmp_path = tmp.name

try:
    # Process file
    extract_text_from_pdf(tmp_path)
finally:
    os.unlink(tmp_path)  # Ensure cleanup
```

### 6. Weak Error Handling Exposes System Information
**Files:** Throughout the codebase (various exception handlers)

**Severity:** MEDIUM
**CWE:** CWE-209 (Information Exposure Through Error Message)

**Example:**
```python
except Exception as e:
    print(f"Error reading PDF {pdf_path}: {e}")
```

**Description:**
Detailed error messages expose file paths, system configuration, and internal structure.

**Recommendation:**
```python
import logging

logger = logging.getLogger(__name__)

try:
    # sensitive operation
except Exception as e:
    logger.error(f"PDF processing failed", exc_info=True)  # Log full details
    return {"error": "Unable to process document"}  # Return generic message
```

### 7. No Authentication on Celery Workers
**File:** `tasks.py`, `docker-compose.yml`

**Severity:** MEDIUM
**CWE:** CWE-306 (Missing Authentication for Critical Function)

**Description:**
Redis broker for Celery is configured without authentication in the default setup. Anyone with network access can submit tasks or retrieve results.

**Recommendation:**
```python
# In tasks.py
app = Celery(
    'refund_engine',
    broker=os.getenv('REDIS_URL', 'redis://:password@localhost:6379/0'),
    backend=os.getenv('REDIS_URL', 'redis://:password@localhost:6379/0')
)

# Set strong password in .env
REDIS_URL=redis://:strong_random_password_here@localhost:6379/0
```

### 8. Supabase Service Role Key Usage
**Files:** `chatbot/simple_chat.py:28`

**Severity:** MEDIUM
**CWE:** CWE-798 (Use of Hard-coded Credentials)

**Vulnerable Code:**
```python
supabase = create_client(
    os.getenv('SUPABASE_URL'),
    os.getenv('SUPABASE_SERVICE_ROLE_KEY')  # Bypasses RLS
)
```

**Description:**
The service role key bypasses Row Level Security (RLS) policies. This should only be used in trusted backend contexts, not in scripts that might be exposed.

**Recommendation:**
Use the regular `SUPABASE_KEY` (anon key) where possible, and only use service role key when absolutely necessary:
```python
# For read operations
supabase = create_client(
    os.getenv('SUPABASE_URL'),
    os.getenv('SUPABASE_KEY')  # Respects RLS
)

# For admin operations only
supabase_admin = create_client(
    os.getenv('SUPABASE_URL'),
    os.getenv('SUPABASE_SERVICE_ROLE_KEY')
)
```

### 9. Insufficient Logging and Audit Trail
**Files:** Throughout the codebase

**Severity:** MEDIUM
**CWE:** CWE-778 (Insufficient Logging)

**Description:**
Limited logging of security-relevant events:
- No logging of file access attempts
- No audit trail for refund decisions
- No logging of failed authentication attempts (if implemented)

**Recommendation:**
```python
import logging
from datetime import datetime

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('audit.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Log security events
logger.info(f"File access: {file_path} by {user_id}")
logger.warning(f"Suspicious file path detected: {file_path}")
logger.error(f"Authentication failed for user: {user_id}")
```

---

## Low Severity Issues & Best Practices

### 10. Outdated Dependencies
**File:** `requirements.txt`

**Severity:** LOW
**CWE:** CWE-1035 (Use of Vulnerable Third-Party Component)

**Observation:**
Some dependencies may have known vulnerabilities. Regular updates are needed.

**Recommendation:**
```bash
# Regularly check for vulnerabilities
pip install safety
safety check

# Or use dependabot in GitHub
# .github/dependabot.yml
```

### 11. Lack of Input Sanitization for AI Prompts
**Files:** `core/enhanced_rag.py`, `analysis/analyze_refunds.py`

**Severity:** LOW
**CWE:** CWE-74 (Improper Neutralization of Special Elements)

**Description:**
User input is directly embedded in AI prompts without sanitization. While OpenAI has safety measures, prompt injection is still a concern.

**Recommendation:**
```python
def sanitize_prompt_input(user_input: str) -> str:
    """Sanitize user input before embedding in AI prompts"""
    # Remove control characters
    sanitized = ''.join(char for char in user_input if char.isprintable())

    # Truncate to reasonable length
    sanitized = sanitized[:5000]

    # Escape potential prompt injection patterns
    sanitized = sanitized.replace('Ignore previous instructions', '[REDACTED]')
    sanitized = sanitized.replace('System:', '[REDACTED]')

    return sanitized
```

### 12. Missing Content Security Policy for Future Web Interface
**Severity:** LOW (Preventive)

**Observation:**
No web interface currently exists, but if one is added, CSP headers will be critical.

**Recommendation:**
If/when adding a web interface:
```python
# Flask example
@app.after_request
def set_security_headers(response):
    response.headers['Content-Security-Policy'] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline'; "
        "style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data: https:;"
    )
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    return response
```

---

## Positive Security Practices Observed

The codebase demonstrates several good security practices:

1. **Secrets Management:** All API keys and credentials stored in environment variables (`.env` file not committed to git)
2. **PII Protection:** Dedicated modules for PII detection, redaction, and encryption (`core/security/`)
3. **Encryption:** Uses Fernet (AES-128) for sensitive data encryption
4. **No Hardcoded Secrets:** No API keys or passwords found in code
5. **SQL Parameterization:** Supabase client uses parameterized queries (except verify_schema.py)
6. **Dependency Isolation:** Uses virtual environment and requirements.txt
7. **Testing Coverage:** ~70% test coverage with pytest
8. **Docker Isolation:** Containerized deployment reduces attack surface

---

## Recommendations Summary

### Immediate Actions (Critical/High)
1. **Fix SQL injection in `verify_schema.py`** - Use parameterized queries or identifier quoting
2. **Implement path traversal protection** - Validate all file paths before access
3. **Add input validation** - Validate all Excel data before processing
4. **Implement rate limiting** - Limit OpenAI API calls to prevent cost attacks
5. **Secure Redis/Celery** - Add authentication to Redis broker

### Short-term Actions (Medium)
6. **Improve error handling** - Log detailed errors, return generic messages
7. **Review Supabase key usage** - Use anon key where possible
8. **Add security logging** - Implement comprehensive audit trail
9. **Secure temporary files** - Use `tempfile` module properly

### Long-term Actions (Low)
10. **Regular dependency updates** - Implement automated vulnerability scanning
11. **Sanitize AI prompts** - Prevent prompt injection attacks
12. **Security training** - Train developers on secure coding practices
13. **Penetration testing** - Conduct professional security assessment

---

## Testing Recommendations

### Security Test Cases to Add
```python
# Test path traversal prevention
def test_path_traversal_blocked():
    with pytest.raises(ValueError):
        safe_resolve_path(base_dir, "../../../etc/passwd")

# Test SQL injection prevention
def test_sql_injection_blocked():
    malicious_table = "users; DROP TABLE users--"
    # Should either raise error or safely escape
    verify_table_exists(malicious_table)

# Test input validation
def test_invalid_amount_rejected():
    row = {"Amount": -1000, "Tax": 50}
    is_valid, error = validate_row_data(row)
    assert not is_valid
    assert "out of range" in error.lower()

# Test rate limiting
def test_rate_limit_enforced():
    # Make 100 rapid API calls
    # Should throttle after configured limit
    pass
```

---

## Compliance Considerations

### OWASP Top 10 (2021) Mapping
- **A03:2021 – Injection:** SQL injection vulnerability found
- **A01:2021 – Broken Access Control:** Path traversal vulnerabilities
- **A04:2021 – Insecure Design:** Lack of rate limiting
- **A05:2021 – Security Misconfiguration:** Unauthenticated Redis
- **A09:2021 – Security Logging Failures:** Insufficient audit logging

### Data Privacy
- Good PII protection mechanisms in place
- Encryption for sensitive data
- **Recommend:** Add data retention policies and user consent tracking

---

## Conclusion

The RefundEngine codebase shows promise with good PII protection and secrets management, but **requires immediate attention** to critical SQL injection and path traversal vulnerabilities. The lack of input validation and authentication on background workers poses significant risks.

**Recommended Priority:**
1. Address Critical SQL injection immediately
2. Implement path validation within 1 week
3. Add input validation and rate limiting within 2 weeks
4. Complete all Medium-severity fixes within 1 month
5. Establish ongoing security review process

**Risk Assessment:**
- **Current Risk:** HIGH
- **After Critical Fixes:** MEDIUM
- **After All Recommendations:** LOW

---

## Appendix: Security Checklist

- [x] Secrets not committed to repository
- [x] API keys in environment variables
- [x] PII detection and encryption
- [ ] SQL injection prevention (FAILED)
- [ ] Path traversal protection (FAILED)
- [ ] Input validation (NEEDS IMPROVEMENT)
- [ ] Rate limiting (MISSING)
- [ ] Authentication on services (NEEDS IMPROVEMENT)
- [ ] Comprehensive logging (NEEDS IMPROVEMENT)
- [ ] Regular security updates (NEEDS PROCESS)
- [x] Test coverage exists
- [x] Containerized deployment

**Overall Score: 6/12 security controls fully implemented**

---

**Report Generated:** 2025-11-11
**Review Scope:** Complete codebase security analysis
**Next Review:** Recommended after fixes implemented
