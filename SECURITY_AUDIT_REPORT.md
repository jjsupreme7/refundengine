# Security Audit Report
## Washington State Tax Refund Engine

**Audit Date:** November 13, 2025
**Auditor:** Security Professional
**Codebase Version:** Git commit 7e47d1a

---

## Executive Summary

This security audit was conducted on the Washington State Tax Refund Engine, a Python-based application that processes sensitive financial data including invoices, tax IDs, bank accounts, and personally identifiable information (PII). The system uses AI (OpenAI GPT-4) for invoice analysis and maintains a vector database (Supabase) for tax law research.

**Overall Security Posture:** MODERATE with several HIGH-SEVERITY vulnerabilities identified

**Critical Findings:** 7 High Severity, 5 Medium Severity, 4 Low Severity

---

## 1. HIGH SEVERITY VULNERABILITIES

### 🔴 1.1 Supabase Service Role Key Exposure Risk

**Severity:** HIGH
**CWE:** CWE-798 (Use of Hard-coded Credentials)
**Location:** Multiple files

**Issue:**
The application uses `SUPABASE_SERVICE_ROLE_KEY` throughout the codebase, which provides FULL ADMINISTRATIVE ACCESS to the database, bypassing Row-Level Security (RLS) policies. This key is stored only in environment variables without additional protection layers.

**Affected Files:**
- `core/database.py:83`
- `chatbot/web_chat.py:36`
- `docker-compose.yml:49`
- All analysis scripts

**Risk:**
- If the service role key is compromised, an attacker gains complete database access
- No Row-Level Security enforcement when using service role key
- All PII and financial data becomes accessible
- Container logs or error messages could expose the key

**Proof of Vulnerability:**
```python
# core/database.py line 83-94
key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")  # Full admin access
if not key:
    raise ValueError("SUPABASE_SERVICE_ROLE_KEY not set...")
_supabase_client = create_client(url, key)
```

**Recommendation:**
1. **CRITICAL:** Implement Row-Level Security (RLS) policies on all Supabase tables
2. Use the anon/authenticated key for read operations where possible
3. Reserve service role key only for administrative operations
4. Implement key rotation policy (quarterly at minimum)
5. Use secret management service (AWS Secrets Manager, HashiCorp Vault)
6. Add key expiration monitoring

---

### 🔴 1.2 Flask Document Server Running Without Authentication

**Severity:** HIGH
**CWE:** CWE-306 (Missing Authentication for Critical Function)
**Location:** `chatbot/document_server.py`

**Issue:**
The Flask document server serves PDF files on port 5001 without any authentication mechanism. While path validation prevents directory traversal, anyone with network access can download all legal documents.

**Affected Code:**
```python
# chatbot/document_server.py line 204-209
app.run(
    host='0.0.0.0',  # Binds to all interfaces!
    port=5001,
    debug=False,
    threaded=True
)
```

**Risk:**
- Legal documents and tax law PDFs accessible to unauthorized users
- If deployed to production, documents are publicly accessible
- No rate limiting to prevent scraping
- No audit logging of document access

**Attack Scenario:**
```bash
# Attacker can enumerate and download all documents
curl http://localhost:5001/documents/WAC_458-20-15502.pdf
curl http://localhost:5001/documents/WAC_458-20-15503.pdf
# etc.
```

**Recommendation:**
1. **CRITICAL:** Implement authentication (API key, OAuth, JWT)
2. Change host binding from `0.0.0.0` to `127.0.0.1` for localhost-only access
3. Add rate limiting (e.g., Flask-Limiter)
4. Implement audit logging for all file access
5. Use HTTPS/TLS in production
6. Consider using Supabase Storage with signed URLs instead

**Proof-of-Concept Fix:**
```python
# Add authentication middleware
from functools import wraps
from flask import request, abort

def require_api_key(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        if not api_key or api_key != os.getenv('DOCUMENT_SERVER_API_KEY'):
            abort(401, description="Unauthorized")
        return f(*args, **kwargs)
    return decorated_function

@app.route('/documents/<path:filename>', methods=['GET'])
@require_api_key  # Add this
def serve_document(filename):
    # ... existing code
```

---

### 🔴 1.3 Hardcoded API Keys in Multiple Files

**Severity:** HIGH
**CWE:** CWE-798 (Use of Hard-coded Credentials)
**Location:** Multiple Python files

**Issue:**
Multiple files contain direct API key initialization from environment variables without validation, error handling, or fallback mechanisms. Additionally, API keys appear in grep search results suggesting potential exposure.

**Affected Files:**
- `chatbot/web_chat.py:30`
- `analysis/fast_batch_analyzer.py:37`
- All analysis scripts
- Docker compose environment variables

**Vulnerable Pattern:**
```python
# chatbot/web_chat.py line 30
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
# No validation, no error handling

# analysis/fast_batch_analyzer.py line 37-40
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
supabase: Client = create_client(
    os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_SERVICE_ROLE_KEY")
)
```

**Risk:**
- API keys may be logged in error messages or stack traces
- No validation means silent failures or unexpected behavior
- Keys could appear in debugging output
- Git history might contain accidentally committed keys

**Recommendation:**
1. **CRITICAL:** Audit git history for exposed keys: `git log -p | grep -i "api_key\|sk-"`
2. Centralize API key management in a single module
3. Add validation and fail-fast on missing keys
4. Implement key rotation procedures
5. Use key management services in production
6. Add pre-commit hooks to prevent key commits (e.g., git-secrets)

**Proof-of-Concept Fix:**
```python
# core/secrets.py (new file)
import os
from typing import Optional

class SecretManager:
    @staticmethod
    def get_openai_key() -> str:
        key = os.getenv('OPENAI_API_KEY')
        if not key or not key.startswith('sk-'):
            raise ValueError("Invalid OPENAI_API_KEY")
        return key

    @staticmethod
    def get_supabase_service_key() -> str:
        key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
        if not key:
            raise ValueError("SUPABASE_SERVICE_ROLE_KEY not set")
        # Validate format
        return key
```

---

### 🔴 1.4 Redis Message Broker Without Authentication

**Severity:** HIGH
**CWE:** CWE-306 (Missing Authentication)
**Location:** `docker-compose.yml:5-16`, `tasks.py:19`

**Issue:**
The Redis instance used as Celery message broker runs without authentication and is exposed on port 6379. While containerized, this allows any process with network access to read/write task data.

**Vulnerable Configuration:**
```yaml
# docker-compose.yml line 5-16
redis:
  image: redis:7-alpine
  ports:
    - "6379:6379"  # Exposed to host!
  # NO PASSWORD CONFIGURED
```

```python
# tasks.py line 19
broker=os.getenv('REDIS_URL', 'redis://localhost:6379/0')
# No authentication in connection string
```

**Risk:**
- Task data contains sensitive invoice information
- Attacker can inject malicious Celery tasks
- Can read results containing PII/financial data
- Potential for code execution via task injection

**Attack Scenario:**
```python
# Attacker can inject tasks remotely
import redis
r = redis.Redis(host='victim-host', port=6379)
r.lpush('celery', malicious_task_payload)
```

**Recommendation:**
1. **CRITICAL:** Enable Redis authentication with strong password
2. Use Redis ACL (Access Control Lists) for fine-grained permissions
3. Bind Redis to localhost only (remove port exposure)
4. Enable Redis TLS for encryption in transit
5. Implement Celery message signing
6. Use Redis Sentinel or Redis Cluster for production

**Fix:**
```yaml
# docker-compose.yml
redis:
  image: redis:7-alpine
  command: redis-server --requirepass ${REDIS_PASSWORD}
  # Don't expose port externally
  expose:
    - "6379"
  environment:
    - REDIS_PASSWORD=${REDIS_PASSWORD}
```

```python
# tasks.py
app = Celery(
    'refund_engine',
    broker=f'redis://:{os.getenv("REDIS_PASSWORD")}@redis:6379/0',
    backend=f'redis://:{os.getenv("REDIS_PASSWORD")}@redis:6379/0'
)

# Enable message signing
app.conf.task_serializer = 'json'
app.conf.accept_content = ['json']
app.conf.task_protocol = 2
```

---

### 🔴 1.5 Insufficient Encryption Key Protection

**Severity:** HIGH
**CWE:** CWE-320 (Key Management Errors)
**Location:** `core/security/encryption.py`

**Issue:**
The application uses Fernet symmetric encryption for PII, but the encryption key is stored in a plain text environment variable without key derivation, rotation support, or secure storage.

**Vulnerable Code:**
```python
# core/security/encryption.py line 32-39
if key is None:
    key_str = os.getenv("ENCRYPTION_KEY")
    if not key_str:
        raise ValueError("ENCRYPTION_KEY environment variable not set...")
    key = key_str.encode()
```

**Risk:**
- Single encryption key for all data (no key rotation)
- Key stored in plain text in .env file
- If key is compromised, ALL encrypted data is exposed
- No key versioning or migration path
- Container logs may expose the key
- Backups contain unprotected keys

**Recommendation:**
1. **CRITICAL:** Implement key rotation mechanism with versioning
2. Use AWS KMS, Azure Key Vault, or HashiCorp Vault for key storage
3. Derive encryption keys using PBKDF2/scrypt from master key
4. Store key version in encrypted records
5. Implement key migration for re-encryption
6. Never log the encryption key

**Proof-of-Concept Fix:**
```python
# core/security/encryption_v2.py
class EncryptionServiceV2:
    def __init__(self):
        master_key = self._get_master_key_from_vault()
        self.key_version = os.getenv('ENCRYPTION_KEY_VERSION', 'v1')
        self.cipher = self._derive_key(master_key, self.key_version)

    def encrypt(self, value: str) -> str:
        encrypted = self.cipher.encrypt(value.encode())
        # Prepend version tag
        return f"{self.key_version}:{encrypted.decode()}"

    def decrypt(self, encrypted_value: str) -> str:
        version, data = encrypted_value.split(':', 1)
        cipher = self._get_cipher_for_version(version)
        return cipher.decrypt(data.encode()).decode()
```

---

### 🔴 1.6 PII Logging in Debug Mode

**Severity:** HIGH
**CWE:** CWE-532 (Information Exposure Through Log Files)
**Location:** Multiple files

**Issue:**
The application logs potentially sensitive data in debug mode, including task details, error messages, and API responses that may contain PII.

**Vulnerable Code:**
```python
# tasks.py line 43, 47
def on_success(self, retval, task_id, args, kwargs):
    print(f"✅ Task {task_id} completed successfully")  # retval may contain PII

def on_failure(self, exc, task_id, args, kwargs, einfo):
    print(f"❌ Task {task_id} failed: {exc}")  # exc may contain sensitive data

# core/enhanced_rag.py line 114, 147
print(f"Context: {', '.join([f'{k}={v}' for k, v in list(context.items())[:3]])}")
# May log sensitive context including tax IDs, amounts
```

**Risk:**
- PII exposure in application logs
- Logs may be centralized without encryption
- Compliance violations (PCI-DSS, GDPR, etc.)
- Log files readable by multiple users

**Recommendation:**
1. **CRITICAL:** Implement PII redaction in all logging
2. Use structured logging (e.g., structlog) with filters
3. Never log raw task arguments/results
4. Sanitize exception messages before logging
5. Encrypt log files at rest
6. Implement log retention policies

---

### 🔴 1.7 Streamlit XSS via unsafe_allow_html

**Severity:** HIGH
**CWE:** CWE-79 (Cross-Site Scripting)
**Location:** `chatbot/web_chat.py`

**Issue:**
The Streamlit chatbot uses `unsafe_allow_html=True` to render user-provided content, creating XSS vulnerabilities if citation URLs or file names contain malicious JavaScript.

**Vulnerable Code:**
```python
# chatbot/web_chat.py line 81
st.markdown("""<style>...</style>""", unsafe_allow_html=True)

# chatbot/web_chat.py line 228
if file_url:
    citation_display = f'<a href="{file_url}" target="_blank" class="citation-link">{citation}</a>'
else:
    citation_display = f'<span class="citation-link">{citation}</span>'

# chatbot/web_chat.py line 252
st.markdown(source_html, unsafe_allow_html=True)
```

**Risk:**
- Stored XSS if malicious data in database
- Session hijacking via cookie theft
- Clickjacking attacks
- Phishing via fake forms

**Attack Scenario:**
```python
# Malicious citation in database
citation = '"><script>alert(document.cookie)</script><a href="'
file_url = 'javascript:alert("XSS")'

# Results in:
# <a href="javascript:alert("XSS")" target="_blank">"><script>...</script></a>
```

**Recommendation:**
1. **CRITICAL:** Sanitize all user inputs and database content before rendering
2. Use HTML escaping for dynamic content
3. Implement Content Security Policy (CSP) headers
4. Avoid `unsafe_allow_html` where possible
5. Validate URLs against allowed protocols (http/https only)

**Fix:**
```python
import html
from urllib.parse import urlparse

def sanitize_url(url: str) -> str:
    """Sanitize URL to prevent XSS"""
    parsed = urlparse(url)
    if parsed.scheme not in ['http', 'https']:
        return '#'  # Block javascript:, data:, etc.
    return html.escape(url)

def render_source_with_link(doc: Dict, index: int):
    citation = html.escape(doc['citation'])
    file_url = sanitize_url(doc.get('file_url', ''))

    if file_url and file_url != '#':
        citation_display = f'<a href="{file_url}" target="_blank" class="citation-link">{citation}</a>'
    else:
        citation_display = f'<span class="citation-link">{citation}</span>'

    # Safe HTML rendering
    st.markdown(source_html, unsafe_allow_html=True)
```

---

## 2. MEDIUM SEVERITY VULNERABILITIES

### 🟡 2.1 Celery Task Deserialization Vulnerabilities

**Severity:** MEDIUM
**CWE:** CWE-502 (Deserialization of Untrusted Data)
**Location:** `tasks.py:24-29`

**Issue:**
While Celery is configured to use JSON serialization (safer than pickle), there's no message authentication to prevent task injection.

**Current Configuration:**
```python
app.conf.update(
    task_serializer='json',  # Good - not using pickle
    accept_content=['json'],  # But no message signing
    result_serializer='json',
)
```

**Recommendation:**
1. Enable Celery message signing with secret key
2. Implement task whitelisting
3. Add task rate limiting per user/IP

---

### 🟡 2.2 Missing Input Validation on Invoice File Paths

**Severity:** MEDIUM
**CWE:** CWE-20 (Improper Input Validation)
**Location:** `tasks.py:82`

**Issue:**
Invoice file paths from user input are used directly without validation beyond file existence check.

**Vulnerable Code:**
```python
# tasks.py line 73-88
invoice_file = row_data.get('invoice_file', '')
if not invoice_file:
    return {'status': 'error', 'error': 'No invoice file specified'}

pdf_path = Path('client_documents') / invoice_file  # Path traversal possible
if not pdf_path.exists():
    return {'status': 'error', 'error': f'Invoice file not found: {invoice_file}'}
```

**Risk:**
- Path traversal: `invoice_file = "../../etc/passwd"`
- Access to arbitrary files in filesystem

**Recommendation:**
1. Validate filename against whitelist pattern
2. Use `secure_filename()` from werkzeug
3. Resolve path and ensure it's within allowed directory
4. Implement file access logging

**Fix:**
```python
from werkzeug.utils import secure_filename
from pathlib import Path

def validate_invoice_path(invoice_file: str) -> Path:
    """Validate and return safe invoice path"""
    safe_name = secure_filename(invoice_file)
    if not safe_name:
        raise ValueError("Invalid filename")

    pdf_path = (Path('client_documents') / safe_name).resolve()
    allowed_dir = Path('client_documents').resolve()

    # Ensure path is within allowed directory
    try:
        pdf_path.relative_to(allowed_dir)
    except ValueError:
        raise ValueError("Path traversal detected")

    return pdf_path
```

---

### 🟡 2.3 Lack of Rate Limiting on AI API Calls

**Severity:** MEDIUM
**CWE:** CWE-770 (Allocation of Resources Without Limits)
**Location:** Multiple files using OpenAI API

**Issue:**
No rate limiting on expensive OpenAI API calls. A malicious user could cause significant costs or denial of service.

**Risk:**
- Cost explosion from API abuse
- Quota exhaustion
- Denial of service

**Recommendation:**
1. Implement rate limiting per user/session
2. Add cost tracking and alerts
3. Set maximum daily API budget
4. Use exponential backoff on retries
5. Implement circuit breaker pattern

---

### 🟡 2.4 Weak Error Messages Expose System Information

**Severity:** MEDIUM
**CWE:** CWE-209 (Information Exposure Through Error Message)
**Location:** Multiple files

**Issue:**
Detailed error messages expose internal system information including file paths, database structure, and API details.

**Examples:**
```python
# chatbot/web_chat.py line 152
st.error(f"Search error: {e}")  # Exposes database errors

# tasks.py line 133
print(f"Error processing row {row_data.get('row_id')}: {exc}")
```

**Recommendation:**
1. Use generic error messages for users
2. Log detailed errors separately
3. Implement error code system
4. Sanitize stack traces in production

---

### 🟡 2.5 Docker Container Running as Root

**Severity:** MEDIUM
**CWE:** CWE-250 (Execution with Unnecessary Privileges)
**Location:** `Dockerfile` (not provided but inferred from docker-compose.yml)

**Issue:**
Docker containers likely run as root user, increasing attack surface if container is compromised.

**Recommendation:**
1. Create non-root user in Dockerfile
2. Use USER directive to drop privileges
3. Apply principle of least privilege
4. Use read-only root filesystem where possible

---

## 3. LOW SEVERITY VULNERABILITIES

### 🟢 3.1 Missing HTTPS/TLS for Production Deployment

**Severity:** LOW
**CWE:** CWE-319 (Cleartext Transmission of Sensitive Information)

**Recommendation:**
1. Use HTTPS for all production endpoints
2. Implement TLS 1.2+ only
3. Use strong cipher suites
4. Implement HSTS headers

---

### 🟢 3.2 Lack of Security Headers

**Severity:** LOW
**CWE:** CWE-693 (Protection Mechanism Failure)
**Location:** `chatbot/document_server.py`

**Recommendation:**
Add security headers to Flask app:
```python
@app.after_request
def set_security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Strict-Transport-Security'] = 'max-age=31536000'
    return response
```

---

### 🟢 3.3 Insufficient Audit Logging

**Severity:** LOW
**CWE:** CWE-778 (Insufficient Logging)

**Recommendation:**
1. Log all authentication attempts
2. Log all file access (document server)
3. Log all database modifications
4. Implement log aggregation

---

### 🟢 3.4 Dependency Vulnerabilities

**Severity:** LOW
**CWE:** CWE-1035 (Use of Component with Known Vulnerabilities)
**Location:** `requirements.txt`

**Recommendation:**
1. Run `pip audit` or `safety check` regularly
2. Keep dependencies updated
3. Implement Dependabot or Renovate
4. Pin dependency versions

---

## 4. POSITIVE SECURITY CONTROLS

The following security controls are **well-implemented**:

✅ **PII Detection and Redaction** (`core/security/pii_detector.py`, `core/security/redactor.py`)
- Microsoft Presidio for ML-based PII detection
- Custom regex patterns for financial data
- Redaction before external API calls
- Well-structured approach

✅ **Field-Level Encryption** (`core/security/encryption.py`)
- Fernet (AES-128) encryption for sensitive fields
- Structured approach with field mapping
- Masking for exports

✅ **Path Traversal Protection** (`chatbot/document_server.py:82-87`)
- Uses `secure_filename()`
- Validates paths are within knowledge base
- Proper error handling

✅ **SQL Injection Protection**
- Uses Supabase SDK (not raw SQL)
- Parameterized queries via ORM
- No string concatenation in queries

✅ **Test Coverage Requirements**
- 70%+ coverage mandate
- Security testing included

---

## 5. COMPLIANCE CONCERNS

### PCI-DSS
- ❌ Insufficient encryption key management
- ❌ No network segmentation
- ❌ Insufficient logging

### GDPR/Privacy
- ✅ PII detection implemented
- ⚠️ Need data retention policies
- ⚠️ Need explicit consent tracking

### SOC 2
- ❌ Insufficient access controls
- ❌ Missing audit logs
- ⚠️ Need incident response plan

---

## 6. REMEDIATION PRIORITY

### Immediate (Fix within 48 hours)
1. Add authentication to document server
2. Enable Redis password authentication
3. Audit git history for exposed keys
4. Implement Supabase RLS policies
5. Fix XSS vulnerabilities in Streamlit

### Short-term (Fix within 2 weeks)
1. Implement key rotation for encryption
2. Add input validation for file paths
3. Implement rate limiting
4. Sanitize error messages
5. Add security headers

### Medium-term (Fix within 1 month)
1. Implement audit logging
2. Add monitoring and alerting
3. Conduct penetration testing
4. Update security documentation
5. Implement secret management service

---

## 7. SECURITY BEST PRACTICES RECOMMENDATIONS

### Development
1. Use pre-commit hooks to prevent key commits (git-secrets)
2. Implement SAST/DAST in CI/CD pipeline
3. Conduct regular security code reviews
4. Use branch protection rules

### Operations
1. Implement secrets management (HashiCorp Vault, AWS Secrets Manager)
2. Enable audit logging on all services
3. Implement SIEM for log aggregation
4. Set up security monitoring and alerting
5. Regular vulnerability scanning

### Architecture
1. Implement zero-trust network architecture
2. Use service mesh for inter-service communication
3. Implement API gateway with WAF
4. Use HSM for encryption key storage

---

## 8. CONCLUSION

The Washington State Tax Refund Engine has a **moderate security posture** with several critical vulnerabilities that must be addressed before production deployment. The application demonstrates good security awareness with PII detection and redaction, but suffers from:

1. **Insufficient access controls** (no authentication on document server)
2. **Inadequate secret management** (keys in environment variables)
3. **Missing authentication** on message broker (Redis)
4. **XSS vulnerabilities** in web interface
5. **Insufficient logging and monitoring**

**Estimated Remediation Effort:** 3-4 weeks of focused security work

**Risk Assessment:**
- Current state: **HIGH RISK** for production deployment
- Post-remediation: **MODERATE RISK** (acceptable with ongoing monitoring)

---

## 9. REFERENCES

- OWASP Top 10 2021: https://owasp.org/Top10/
- CWE/SANS Top 25: https://cwe.mitre.org/top25/
- NIST Cybersecurity Framework: https://www.nist.gov/cyberframework
- Supabase Security Best Practices: https://supabase.com/docs/guides/security
- OpenAI Security Guidelines: https://platform.openai.com/docs/guides/safety-best-practices

---

**Report Generated:** November 13, 2025
**Next Review Date:** December 13, 2025 (30 days)
