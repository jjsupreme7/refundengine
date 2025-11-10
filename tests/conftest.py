"""
Pytest configuration and fixtures
"""

import os
import sys
from pathlib import Path
import pytest
from unittest.mock import Mock, MagicMock

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Mock environment variables for testing
os.environ["OPENAI_API_KEY"] = "test-key-123"
os.environ["SUPABASE_URL"] = "https://test.supabase.co"
os.environ["SUPABASE_KEY"] = "test-key"
os.environ["SUPABASE_SERVICE_ROLE_KEY"] = "test-service-key"


@pytest.fixture
def mock_openai_client():
    """Mock OpenAI client for testing"""
    mock = MagicMock()

    # Mock embeddings
    mock.embeddings.create.return_value = Mock(data=[Mock(embedding=[0.1] * 1536)])

    # Mock chat completions
    mock.chat.completions.create.return_value = Mock(
        choices=[
            Mock(
                message=Mock(
                    content='{"product_desc": "Test Product", "product_type": "Software", "details": "Test details", "line_item_found": true, "confidence": 95}'
                )
            )
        ]
    )

    return mock


@pytest.fixture
def mock_supabase_client():
    """Mock Supabase client for testing"""
    mock = MagicMock()

    # Mock table queries
    mock.table.return_value.select.return_value.eq.return_value.execute.return_value = (
        Mock(data=[])
    )

    # Mock RPC calls
    mock.rpc.return_value.execute.return_value = Mock(data=[])

    return mock


@pytest.fixture
def sample_invoice_data():
    """Sample invoice data for testing"""
    return {
        "vendor": "Microsoft Corporation",
        "invoice_number": "INV-001",
        "date": "2024-01-15",
        "amount": 50000.00,
        "tax": 5000.00,
        "product_desc": "Microsoft 365 E5 Licenses",
        "invoice_file": "test_invoice.pdf",
    }


@pytest.fixture
def sample_vendor_data():
    """Sample vendor metadata for testing"""
    return {
        "vendor_name": "MICROSOFT CORPORATION",
        "normalized_name": "MICROSOFT",
        "industry": "Software & Technology",
        "business_model": "B2B SaaS",
        "products": ["Microsoft 365", "Azure", "Dynamics"],
        "delivery_method": "Cloud/SaaS",
    }


@pytest.fixture
def temp_pdf_file(tmp_path):
    """Create a temporary PDF file for testing"""
    pdf_path = tmp_path / "test_invoice.pdf"
    # Create a minimal valid PDF
    pdf_content = b"""%PDF-1.4
1 0 obj
<<
/Type /Catalog
/Pages 2 0 R
>>
endobj
2 0 obj
<<
/Type /Pages
/Kids [3 0 R]
/Count 1
>>
endobj
3 0 obj
<<
/Type /Page
/Parent 2 0 R
/Resources <<
/Font <<
/F1 <<
/Type /Font
/Subtype /Type1
/BaseFont /Helvetica
>>
>>
>>
/MediaBox [0 0 612 792]
/Contents 4 0 R
>>
endobj
4 0 obj
<<
/Length 44
>>
stream
BT
/F1 12 Tf
100 700 Td
(Test Invoice) Tj
ET
endstream
endobj
xref
0 5
0000000000 65535 f
0000000009 00000 n
0000000058 00000 n
0000000115 00000 n
0000000317 00000 n
trailer
<<
/Size 5
/Root 1 0 R
>>
startxref
409
%%EOF"""
    pdf_path.write_bytes(pdf_content)
    return pdf_path
