# Security Fixes Quick Reference Guide

## Critical Fixes Required Before Production

### 1. Document Server Authentication (HIGH - 30 minutes)
```python
# File: chatbot/document_server.py
# Add before app.run():

from functools import wraps

def require_api_key(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        if not api_key or api_key != os.getenv('DOCUMENT_SERVER_API_KEY'):
            abort(401, description="Unauthorized")
        return f(*args, **kwargs)
    return decorated_function

# Update serve_document:
@app.route('/documents/<path:filename>', methods=['GET'])
@require_api_key  # Add this line
def serve_document(filename):
    # existing code...

# Change host binding:
app.run(
    host='127.0.0.1',  # Change from 0.0.0.0
    port=5001,
    debug=False,
    threaded=True
)
```

### 2. Redis Authentication (HIGH - 15 minutes)
```yaml
# File: docker-compose.yml
redis:
  image: redis:7-alpine
  command: redis-server --requirepass ${REDIS_PASSWORD}
  expose:
    - "6379"  # Change from ports
  environment:
    - REDIS_PASSWORD=${REDIS_PASSWORD}
```

```python
# File: tasks.py
app = Celery(
    'refund_engine',
    broker=f'redis://:{os.getenv("REDIS_PASSWORD")}@redis:6379/0',
    backend=f'redis://:{os.getenv("REDIS_PASSWORD")}@redis:6379/0'
)
```

```bash
# Add to .env:
REDIS_PASSWORD=$(openssl rand -base64 32)
```

### 3. XSS Protection in Streamlit (HIGH - 20 minutes)
```python
# File: chatbot/web_chat.py
import html
from urllib.parse import urlparse

def sanitize_url(url: str) -> str:
    """Sanitize URL to prevent XSS"""
    parsed = urlparse(url)
    if parsed.scheme not in ['http', 'https']:
        return '#'
    return html.escape(url)

def render_source_with_link(doc: Dict, index: int):
    citation = html.escape(doc['citation'])  # Add escaping
    section = html.escape(doc['section']) if doc['section'] else ''  # Add escaping
    file_url = sanitize_url(doc.get('file_url', ''))  # Add sanitization

    if file_url and file_url != '#':
        citation_display = f'<a href="{file_url}" target="_blank" class="citation-link">{citation}</a>'
    else:
        citation_display = f'<span class="citation-link">{citation}</span>'

    # Escape all tags
    tags_html = ""
    if doc.get('tax_types'):
        for tax in doc['tax_types']:
            tags_html += f'<span class="tag">Tax: {html.escape(tax)}</span>'
    if doc.get('industries'):
        for industry in doc['industries']:
            tags_html += f'<span class="tag">Industry: {html.escape(industry)}</span>'

    # Rest of function...
```

### 4. File Path Validation (MEDIUM - 15 minutes)
```python
# File: tasks.py
from werkzeug.utils import secure_filename

def validate_invoice_path(invoice_file: str) -> Path:
    """Validate and return safe invoice path"""
    safe_name = secure_filename(invoice_file)
    if not safe_name or '..' in safe_name:
        raise ValueError("Invalid filename")

    pdf_path = (Path('client_documents') / safe_name).resolve()
    allowed_dir = Path('client_documents').resolve()

    try:
        pdf_path.relative_to(allowed_dir)
    except ValueError:
        raise ValueError("Path traversal detected")

    if not pdf_path.exists():
        raise FileNotFoundError(f"File not found: {safe_name}")

    return pdf_path

# Update analyze_single_invoice:
@app.task(...)
def analyze_single_invoice(self, row_data: Dict[str, Any]) -> Dict[str, Any]:
    try:
        # ... existing code ...

        invoice_file = row_data.get('invoice_file', '')
        if not invoice_file:
            return {'status': 'error', 'error': 'No invoice file specified'}

        # Use validation function
        try:
            pdf_path = validate_invoice_path(invoice_file)
        except (ValueError, FileNotFoundError) as e:
            return {'status': 'error', 'error': str(e)}

        # Continue with existing code...
```

### 5. Implement Supabase RLS (HIGH - 1 hour)
```sql
-- File: database/security/rls_policies.sql (NEW FILE)

-- Enable RLS on all tables
ALTER TABLE clients ENABLE ROW LEVEL SECURITY;
ALTER TABLE client_documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE refund_analysis_results ENABLE ROW LEVEL SECURITY;

-- Create policies for clients table
CREATE POLICY "Users can view own clients"
  ON clients FOR SELECT
  USING (auth.uid() = owner_id);

CREATE POLICY "Users can insert own clients"
  ON clients FOR INSERT
  WITH CHECK (auth.uid() = owner_id);

CREATE POLICY "Users can update own clients"
  ON clients FOR UPDATE
  USING (auth.uid() = owner_id);

-- Create policies for client_documents
CREATE POLICY "Users can view own documents"
  ON client_documents FOR SELECT
  USING (client_id IN (
    SELECT id FROM clients WHERE owner_id = auth.uid()
  ));

-- Create policies for refund_analysis_results
CREATE POLICY "Users can view own analysis"
  ON refund_analysis_results FOR SELECT
  USING (client_id IN (
    SELECT id FROM clients WHERE owner_id = auth.uid()
  ));

-- Public read for legal documents (knowledge base)
CREATE POLICY "Anyone can read legal documents"
  ON legal_documents FOR SELECT
  USING (true);

CREATE POLICY "Anyone can read tax law chunks"
  ON tax_law_chunks FOR SELECT
  USING (true);
```

### 6. Sanitize Logging (MEDIUM - 30 minutes)
```python
# File: core/logging.py (NEW FILE)
import logging
import re
from typing import Any

class PIISanitizer(logging.Filter):
    """Filter to redact PII from logs"""

    PII_PATTERNS = [
        (r'\b\d{3}-\d{2}-\d{4}\b', '[SSN_REDACTED]'),  # SSN
        (r'\b\d{16}\b', '[CARD_REDACTED]'),  # Credit card
        (r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[EMAIL_REDACTED]'),
        (r'\b\d{9,17}\b', '[ACCOUNT_REDACTED]'),  # Account numbers
        (r'api_key["\']?\s*[:=]\s*["\']?([A-Za-z0-9_-]+)', 'api_key=[KEY_REDACTED]'),
    ]

    def filter(self, record: logging.LogRecord) -> bool:
        record.msg = self.sanitize(str(record.msg))
        if record.args:
            record.args = tuple(self.sanitize(str(arg)) for arg in record.args)
        return True

    def sanitize(self, text: str) -> str:
        """Remove PII from text"""
        for pattern, replacement in self.PII_PATTERNS:
            text = re.sub(pattern, replacement, text)
        return text

# Setup logging
def setup_logging():
    logger = logging.getLogger()
    logger.addFilter(PIISanitizer())
    return logger
```

```python
# File: tasks.py
from core.logging import setup_logging

logger = setup_logging()

class CallbackTask(Task):
    def on_success(self, retval, task_id, args, kwargs):
        # Don't log retval - may contain PII
        logger.info(f"Task {task_id} completed successfully")

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        # Sanitize exception before logging
        logger.error(f"Task {task_id} failed: {type(exc).__name__}")
```

### 7. Add Security Headers (LOW - 10 minutes)
```python
# File: chatbot/document_server.py
@app.after_request
def set_security_headers(response):
    """Add security headers to all responses"""
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    response.headers['Content-Security-Policy'] = "default-src 'self'"
    response.headers['Referrer-Policy'] = 'no-referrer'
    return response
```

### 8. Environment Variable Validation (MEDIUM - 20 minutes)
```python
# File: core/config.py (NEW FILE)
import os
from typing import Optional

class ConfigValidator:
    """Validate all required environment variables on startup"""

    REQUIRED_VARS = {
        'OPENAI_API_KEY': r'^sk-[a-zA-Z0-9]{32,}$',
        'SUPABASE_URL': r'^https://[a-zA-Z0-9-]+\.supabase\.co$',
        'SUPABASE_SERVICE_ROLE_KEY': r'^.{40,}$',
        'ENCRYPTION_KEY': r'^[A-Za-z0-9+/=]{44}$',  # Fernet key format
        'REDIS_PASSWORD': r'^.{16,}$',
    }

    @classmethod
    def validate_all(cls) -> None:
        """Validate all required environment variables"""
        import re
        errors = []

        for var_name, pattern in cls.REQUIRED_VARS.items():
            value = os.getenv(var_name)

            if not value:
                errors.append(f"Missing required variable: {var_name}")
            elif not re.match(pattern, value):
                errors.append(f"Invalid format for {var_name}")

        if errors:
            raise ValueError(f"Configuration errors:\n" + "\n".join(errors))

# Add to main application files:
from core.config import ConfigValidator

# At startup:
ConfigValidator.validate_all()
```

### 9. Audit Git History (CRITICAL - 15 minutes)
```bash
# Run these commands to check for exposed secrets:

# Check for API keys
git log -p | grep -i "sk-" | head -20
git log -p | grep -i "api_key" | head -20

# Check for passwords
git log -p | grep -i "password.*=" | head -20

# Check .env files
git log -p -- .env | head -50

# If secrets found, rotate ALL keys:
# 1. Generate new keys in services (OpenAI, Supabase)
# 2. Update .env with new keys
# 3. Use BFG Repo-Cleaner to remove from git history:
#    java -jar bfg.jar --replace-text secrets.txt
#    git reflog expire --expire=now --all
#    git gc --prune=now --aggressive

# Install git-secrets to prevent future leaks:
git secrets --install
git secrets --register-aws
```

## Testing Security Fixes

```bash
# 1. Test document server authentication
curl -X GET http://localhost:5001/documents/test.pdf
# Should return 401 Unauthorized

curl -X GET http://localhost:5001/documents/test.pdf -H "X-API-Key: YOUR_KEY"
# Should return document

# 2. Test Redis authentication
redis-cli -h localhost -p 6379 ping
# Should return (error) NOAUTH Authentication required

redis-cli -h localhost -p 6379 -a YOUR_REDIS_PASSWORD ping
# Should return PONG

# 3. Test path traversal protection
# Should fail with error:
python -c "from tasks import validate_invoice_path; validate_invoice_path('../../../etc/passwd')"

# 4. Test XSS protection
# Verify HTML escaping in browser dev tools

# 5. Run security scan
pip install safety
safety check --json

# 6. Run dependency audit
pip-audit
```

## Deployment Checklist

Before deploying to production:

- [ ] All HIGH severity vulnerabilities fixed
- [ ] Redis password configured
- [ ] Document server authentication enabled
- [ ] XSS protections implemented
- [ ] Git history audited for secrets
- [ ] All API keys rotated
- [ ] Supabase RLS policies enabled
- [ ] Security headers added
- [ ] Logging sanitization implemented
- [ ] Environment variable validation added
- [ ] Security testing completed
- [ ] Monitoring and alerting configured
- [ ] Incident response plan documented

## Estimated Time to Fix All Critical Issues

- **Immediate fixes:** 2-3 hours
- **Short-term fixes:** 1-2 days
- **Full remediation:** 3-4 weeks

## Emergency Contact

If a security incident is detected:
1. Immediately rotate all API keys
2. Disable affected services
3. Review audit logs
4. Document incident details
5. Notify stakeholders
