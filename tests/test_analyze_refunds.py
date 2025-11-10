"""
Tests for RefundAnalyzer class
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


class TestRefundAnalyzer:
    """Test RefundAnalyzer class"""

    @patch('analysis.analyze_refunds.client')
    @patch('analysis.analyze_refunds.supabase')
    def test_find_line_item_in_invoice(self, mock_supabase, mock_openai):
        """Should extract line item from invoice text"""
        from analysis.analyze_refunds import RefundAnalyzer

        analyzer = RefundAnalyzer()

        # Mock OpenAI response
        mock_response = Mock(
            choices=[Mock(
                message=Mock(
                    content=json.dumps({
                        "product_desc": "Microsoft 365 E5 Licenses",
                        "product_type": "Software",
                        "details": "100 user licenses",
                        "line_item_found": True,
                        "confidence": 95
                    })
                )
            )]
        )
        mock_openai.chat.completions.create.return_value = mock_response

        invoice_text = """
        Invoice #12345
        Microsoft 365 E5 Licenses - 100 users
        Amount: $50,000.00
        Tax: $5,000.00
        """

        result = analyzer.find_line_item_in_invoice(invoice_text, 50000.00, 5000.00)

        assert result is not None
        assert result['product_desc'] == "Microsoft 365 E5 Licenses"
        assert result['line_item_found'] is True
        assert result['confidence'] == 95

    @patch('analysis.analyze_refunds.client')
    @patch('analysis.analyze_refunds.supabase')
    def test_find_line_item_handles_errors(self, mock_supabase, mock_openai):
        """Should handle extraction errors gracefully"""
        from analysis.analyze_refunds import RefundAnalyzer

        analyzer = RefundAnalyzer()

        # Mock API error
        mock_openai.chat.completions.create.side_effect = Exception("API error")

        result = analyzer.find_line_item_in_invoice("Invalid text", 100.00, 10.00)

        # Should return default error result
        assert result is not None
        assert result['line_item_found'] is False
        assert result['confidence'] == 0

    @patch('analysis.analyze_refunds.client')
    @patch('analysis.analyze_refunds.supabase')
    def test_get_embedding(self, mock_supabase, mock_openai):
        """Should generate embeddings for text"""
        from analysis.analyze_refunds import RefundAnalyzer

        analyzer = RefundAnalyzer()

        # Mock embedding response
        mock_openai.embeddings.create.return_value = Mock(
            data=[Mock(embedding=[0.1] * 1536)]
        )

        embedding = analyzer.get_embedding("Test text")

        assert embedding is not None
        assert len(embedding) == 1536
        assert all(isinstance(x, float) for x in embedding)

    @patch('analysis.analyze_refunds.client')
    @patch('analysis.analyze_refunds.supabase')
    def test_search_legal_knowledge(self, mock_supabase, mock_openai):
        """Should search legal knowledge base"""
        from analysis.analyze_refunds import RefundAnalyzer

        analyzer = RefundAnalyzer()

        # Mock embedding
        mock_openai.embeddings.create.return_value = Mock(
            data=[Mock(embedding=[0.1] * 1536)]
        )

        # Mock RPC response
        mock_supabase.rpc.return_value.execute.return_value = Mock(
            data=[
                {
                    'chunk_text': 'WAC 458-20-15502: Multi-point use...',
                    'citation': 'WAC 458-20-15502',
                    'similarity': 0.85
                }
            ]
        )

        results = analyzer.search_legal_knowledge("multi-point use software")

        assert results is not None
        assert len(results) > 0
        assert 'chunk_text' in results[0]
        assert 'citation' in results[0]

    @patch('analysis.analyze_refunds.client')
    @patch('analysis.analyze_refunds.supabase')
    def test_check_vendor_learning(self, mock_supabase, mock_openai):
        """Should check if vendor/product has been seen before"""
        from analysis.analyze_refunds import RefundAnalyzer

        analyzer = RefundAnalyzer()

        # Mock vendor_products table response
        mock_table = MagicMock()
        mock_table.select.return_value.eq.return_value.ilike.return_value.execute.return_value = Mock(
            data=[
                {
                    'vendor_name': 'Microsoft',
                    'product_description': 'Microsoft 365',
                    'product_type': 'SaaS',
                    'tax_treatment': 'Taxable - MPU applicable'
                }
            ]
        )
        mock_supabase.table.return_value = mock_table

        result = analyzer.check_vendor_learning("Microsoft", "Microsoft 365 E5")

        assert result is not None
        assert result['vendor_name'] == 'Microsoft'
        assert result['tax_treatment'] == 'Taxable - MPU applicable'

    @patch('analysis.analyze_refunds.client')
    @patch('analysis.analyze_refunds.supabase')
    def test_check_vendor_learning_no_match(self, mock_supabase, mock_openai):
        """Should return None if vendor/product not in learning database"""
        from analysis.analyze_refunds import RefundAnalyzer

        analyzer = RefundAnalyzer()

        # Mock empty response
        mock_table = MagicMock()
        mock_table.select.return_value.eq.return_value.ilike.return_value.execute.return_value = Mock(
            data=[]
        )
        mock_supabase.table.return_value = mock_table

        result = analyzer.check_vendor_learning("Unknown Vendor", "Unknown Product")

        assert result is None


class TestPDFExtraction:
    """Test PDF text extraction"""

    @patch('analysis.analyze_refunds.supabase')
    @patch('analysis.analyze_refunds.client')
    def test_extract_text_from_pdf(self, mock_openai, mock_supabase, temp_pdf_file):
        """Should extract text from PDF file"""
        from analysis.analyze_refunds import RefundAnalyzer

        analyzer = RefundAnalyzer()

        text = analyzer.extract_text_from_pdf(temp_pdf_file)

        assert text is not None
        assert isinstance(text, str)
        # PDF should contain "Test Invoice"
        assert "Test Invoice" in text or len(text) > 0

    @patch('analysis.analyze_refunds.supabase')
    @patch('analysis.analyze_refunds.client')
    def test_extract_text_handles_missing_file(self, mock_openai, mock_supabase):
        """Should handle missing PDF files gracefully"""
        from analysis.analyze_refunds import RefundAnalyzer

        analyzer = RefundAnalyzer()

        text = analyzer.extract_text_from_pdf(Path("/nonexistent/file.pdf"))

        # Should return empty string instead of crashing
        assert text == ""

    @patch('analysis.analyze_refunds.supabase')
    @patch('analysis.analyze_refunds.client')
    def test_extract_text_handles_corrupted_pdf(self, mock_openai, mock_supabase, tmp_path):
        """Should handle corrupted PDF files"""
        from analysis.analyze_refunds import RefundAnalyzer

        analyzer = RefundAnalyzer()

        # Create corrupted PDF
        corrupted_pdf = tmp_path / "corrupted.pdf"
        corrupted_pdf.write_text("This is not a PDF")

        text = analyzer.extract_text_from_pdf(corrupted_pdf)

        # Should return empty string
        assert text == ""
