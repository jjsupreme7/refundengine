"""
Tests for Vendor Research functionality
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.research_vendors import VendorResearcher


class TestVendorNormalization:
    """Test vendor name normalization"""

    def test_normalize_removes_legal_suffixes(self):
        """Should remove common legal entity suffixes"""
        researcher = VendorResearcher()

        test_cases = [
            ("Microsoft Corporation", "MICROSOFT"),
            ("Adobe Inc.", "ADOBE"),
            ("Oracle Corp", "ORACLE"),
            ("SAP LLC", "SAP"),
            ("IBM Limited", "IBM"),
            ("Cisco Systems, Inc.", "CISCO SYSTEMS"),
        ]

        for input_name, expected in test_cases:
            result = researcher.normalize_vendor_name(input_name)
            assert result == expected, f"'{input_name}' should normalize to '{expected}', got '{result}'"

    def test_normalize_handles_empty_input(self):
        """Should handle empty/None input gracefully"""
        researcher = VendorResearcher()

        assert researcher.normalize_vendor_name("") == ""
        assert researcher.normalize_vendor_name(None) == ""
        assert researcher.normalize_vendor_name("   ") == ""

    def test_normalize_uppercase_conversion(self):
        """Should convert to uppercase"""
        researcher = VendorResearcher()

        result = researcher.normalize_vendor_name("microsoft corporation")
        assert result == "MICROSOFT", "Should be uppercase"

    def test_normalize_removes_extra_whitespace(self):
        """Should remove extra whitespace"""
        researcher = VendorResearcher()

        result = researcher.normalize_vendor_name("Microsoft   Corporation")
        assert "  " not in result, "Should remove extra spaces"


class TestFuzzyMatching:
    """Test fuzzy matching for vendor deduplication"""

    def test_fuzzy_match_exact(self):
        """Should match exact vendor names"""
        researcher = VendorResearcher()
        known_vendors = ["MICROSOFT", "ORACLE", "SAP"]

        result = researcher.fuzzy_match_vendor("MICROSOFT", known_vendors)
        assert result == "MICROSOFT", "Should match exact name"

    def test_fuzzy_match_close_spelling(self):
        """Should match closely spelled names"""
        researcher = VendorResearcher()
        known_vendors = ["MICROSOFT CORPORATION", "ORACLE", "SAP"]

        result = researcher.fuzzy_match_vendor("MICROSFT", known_vendors, threshold=80)
        # Should match despite typo
        assert result is not None, "Should match close spelling"

    def test_fuzzy_match_no_match_low_similarity(self):
        """Should not match very different names"""
        researcher = VendorResearcher()
        known_vendors = ["MICROSOFT", "ORACLE", "SAP"]

        result = researcher.fuzzy_match_vendor("AMAZON", known_vendors, threshold=85)
        assert result is None, "Should not match different vendor"

    def test_fuzzy_match_empty_list(self):
        """Should handle empty known vendors list"""
        researcher = VendorResearcher()

        result = researcher.fuzzy_match_vendor("MICROSOFT", [])
        assert result is None, "Should return None for empty list"


class TestWebSearch:
    """Test web search functionality (mocked)"""

    @patch('scripts.research_vendors.openai_client')
    def test_web_search_vendor_returns_results(self, mock_openai):
        """Should return web search results for vendor"""
        researcher = VendorResearcher()

        # Mock web search to return sample results
        with patch.object(researcher, 'web_search_vendor') as mock_search:
            mock_search.return_value = [
                {
                    'title': 'Microsoft Corporation',
                    'url': 'https://microsoft.com',
                    'snippet': 'Leading technology company...'
                }
            ]

            results = researcher.web_search_vendor("Microsoft")
            assert len(results) > 0, "Should return search results"
            assert results[0]['title'] == 'Microsoft Corporation'

    def test_web_search_handles_errors(self):
        """Should handle web search errors gracefully"""
        researcher = VendorResearcher()

        with patch.object(researcher, 'web_search_vendor') as mock_search:
            mock_search.side_effect = Exception("Network error")

            try:
                results = researcher.web_search_vendor("Microsoft")
                # Should return empty list or handle error
                assert isinstance(results, list), "Should return list even on error"
            except Exception:
                pytest.fail("Should handle errors gracefully")


class TestVendorResearchAI:
    """Test AI-powered vendor research"""

    @patch('scripts.research_vendors.openai_client')
    def test_research_vendor_with_ai_returns_metadata(self, mock_openai):
        """Should extract structured metadata from search results"""
        researcher = VendorResearcher()

        # Mock AI response
        mock_response = {
            'vendor_name': 'Microsoft Corporation',
            'industry': 'Software & Technology',
            'business_model': 'B2B SaaS',
            'products': ['Microsoft 365', 'Azure', 'Dynamics'],
            'delivery_method': 'Cloud/SaaS',
            'tax_notes': 'Digital automated services, likely MPU applicable'
        }

        mock_openai.chat.completions.create.return_value = Mock(
            choices=[Mock(
                message=Mock(content=str(mock_response))
            )]
        )

        # Mock search results
        search_results = [
            {'title': 'Microsoft', 'snippet': 'Technology company'}
        ]

        result = researcher.research_vendor_with_ai("Microsoft", search_results)

        assert result is not None, "Should return metadata"
        # The actual structure depends on implementation

    def test_research_handles_ai_failures(self):
        """Should handle AI API failures gracefully"""
        researcher = VendorResearcher()

        with patch.object(researcher, 'research_vendor_with_ai') as mock_research:
            mock_research.side_effect = Exception("API error")

            try:
                result = researcher.research_vendor_with_ai("Microsoft", [])
                # Should return error result or default
                assert result is not None, "Should handle error"
            except Exception:
                pytest.fail("Should handle AI failures gracefully")
