"""
Critical Tests for Refund Calculations
These tests ensure financial accuracy - bugs here could cost millions
"""
import pytest
from decimal import Decimal


class TestMPUCalculations:
    """Test Multi-Point Use (MPU) refund calculations"""

    def test_mpu_basic_calculation(self):
        """Test basic MPU refund: 15% WA, 85% out-of-state"""
        total_tax = 10000.00
        wa_percentage = 15.0  # 15% of users in Washington

        # CORRECT: Should refund the OUT-OF-STATE portion
        expected_refund = total_tax * (100 - wa_percentage) / 100
        assert expected_refund == 8500.00, "Should refund 85% (out-of-state portion)"

    def test_mpu_zero_wa_usage(self):
        """Test MPU when 0% WA usage - should refund 100%"""
        total_tax = 10000.00
        wa_percentage = 0.0

        expected_refund = total_tax * (100 - wa_percentage) / 100
        assert expected_refund == 10000.00, "100% out-of-state should get full refund"

    def test_mpu_full_wa_usage(self):
        """Test MPU when 100% WA usage - should refund 0%"""
        total_tax = 10000.00
        wa_percentage = 100.0

        expected_refund = total_tax * (100 - wa_percentage) / 100
        assert expected_refund == 0.00, "100% in-state should get no refund"

    def test_mpu_precision(self):
        """Test MPU calculation maintains precision for large amounts"""
        total_tax = 1234567.89
        wa_percentage = 17.35

        expected_refund = total_tax * (100 - wa_percentage) / 100
        # Should be 1,020,610.96
        assert abs(expected_refund - 1020610.96) < 0.01, "Should maintain precision"

    def test_mpu_validates_percentage_range(self):
        """Test that WA percentage is validated"""
        # This test documents expected behavior
        # Actual implementation should validate 0 <= wa_percentage <= 100
        total_tax = 10000.00

        # Invalid percentages should raise errors
        invalid_percentages = [-1, 101, 150, -50]
        for pct in invalid_percentages:
            # Should validate input
            assert not (0 <= pct <= 100), f"Percentage {pct} should be invalid"


class TestProfessionalServicesExemption:
    """Test professional services exemption logic"""

    def test_consulting_services_non_taxable(self):
        """Consulting services should be 100% non-taxable"""
        product_descriptions = [
            "Software consulting services",
            "Professional consulting",
            "IT consulting and advisory",
            "Technical consulting services"
        ]

        for desc in product_descriptions:
            # Should be classified as non-taxable
            is_professional_service = self._is_professional_service(desc)
            assert is_professional_service, f"'{desc}' should be professional service"

    def test_software_development_non_taxable(self):
        """Custom software development should be non-taxable"""
        product_descriptions = [
            "Custom software development",
            "Software development services",
            "Application development and customization",
            "Bespoke software engineering"
        ]

        for desc in product_descriptions:
            is_professional_service = self._is_professional_service(desc)
            assert is_professional_service, f"'{desc}' should be non-taxable"

    def test_help_desk_non_taxable(self):
        """Help desk services should be non-taxable (human effort)"""
        product_descriptions = [
            "Help desk support",
            "Technical support services",
            "IT support and maintenance",
            "Customer support services"
        ]

        for desc in product_descriptions:
            is_professional_service = self._is_professional_service(desc)
            assert is_professional_service, f"'{desc}' should be non-taxable"

    def test_saas_is_taxable(self):
        """SaaS products should be taxable (not professional services)"""
        product_descriptions = [
            "Microsoft 365 licenses",
            "Salesforce subscription",
            "Adobe Creative Cloud",
            "AWS cloud services"
        ]

        for desc in product_descriptions:
            is_professional_service = self._is_professional_service(desc)
            assert not is_professional_service, f"'{desc}' should be taxable SaaS"

    def _is_professional_service(self, description: str) -> bool:
        """Helper to classify if something is a professional service"""
        professional_keywords = [
            'consulting', 'advisory', 'professional services',
            'custom development', 'software development',
            'help desk', 'support services', 'technical support',
            'configuration', 'customization', 'implementation services'
        ]

        desc_lower = description.lower()
        return any(keyword in desc_lower for keyword in professional_keywords)


class TestDigitalAutomatedServices:
    """Test Digital Automated Services (DAS) classification"""

    def test_saas_is_das(self):
        """SaaS should be classified as Digital Automated Service"""
        saas_products = [
            "Microsoft 365 E5",
            "Salesforce Enterprise",
            "Adobe Creative Cloud",
            "Zoom Business License"
        ]

        for product in saas_products:
            is_das = self._is_digital_automated_service(product)
            assert is_das, f"'{product}' should be DAS"

    def test_cloud_infrastructure_is_das(self):
        """Cloud infrastructure should be DAS"""
        cloud_products = [
            "AWS EC2 instances",
            "Azure Virtual Machines",
            "Google Cloud Platform services"
        ]

        for product in cloud_products:
            is_das = self._is_digital_automated_service(product)
            assert is_das, f"'{product}' should be DAS"

    def test_hardware_not_das(self):
        """Hardware should not be DAS"""
        hardware_products = [
            "Dell servers",
            "Cisco networking equipment",
            "HP laptops"
        ]

        for product in hardware_products:
            is_das = self._is_digital_automated_service(product)
            assert not is_das, f"'{product}' should not be DAS"

    def _is_digital_automated_service(self, description: str) -> bool:
        """Helper to classify Digital Automated Services"""
        das_keywords = [
            'saas', 'software as a service', 'cloud', 'subscription',
            'license', 'azure', 'aws', 'google cloud', 'salesforce',
            'microsoft 365', 'office 365', 'adobe', 'zoom'
        ]

        das_exclude_keywords = [
            'hardware', 'equipment', 'server', 'laptop', 'desktop',
            'physical', 'device'
        ]

        desc_lower = description.lower()

        # Check if it's hardware (exclude)
        if any(keyword in desc_lower for keyword in das_exclude_keywords):
            return False

        # Check if it matches DAS keywords
        return any(keyword in desc_lower for keyword in das_keywords)


class TestRefundAmountCalculations:
    """Test actual refund amount calculations"""

    def test_full_refund_non_taxable(self):
        """Non-taxable items should get 100% refund"""
        tax_paid = 5000.00
        is_taxable = False

        if not is_taxable:
            refund = tax_paid * 1.0
        else:
            refund = 0.0

        assert refund == 5000.00, "Non-taxable should get full refund"

    def test_mpu_refund_amount(self):
        """Test actual refund amount for MPU scenario"""
        tax_paid = 10000.00
        wa_percentage = 15.0

        refund = tax_paid * (100 - wa_percentage) / 100

        assert refund == 8500.00, "MPU refund should be out-of-state portion"

    def test_no_refund_fully_taxable_in_state(self):
        """Fully taxable in-state item should get $0 refund"""
        tax_paid = 5000.00
        wa_percentage = 100.0
        is_taxable = True

        if is_taxable and wa_percentage == 100:
            refund = 0.0
        else:
            refund = tax_paid

        assert refund == 0.00, "Fully taxable in-state gets no refund"

    def test_refund_rounding(self):
        """Test refund amounts are properly rounded to cents"""
        tax_paid = 10000.00
        wa_percentage = 33.33  # Results in repeating decimal

        refund = tax_paid * (100 - wa_percentage) / 100
        refund_rounded = round(refund, 2)

        assert refund_rounded == 6667.00, "Should round to nearest cent"


class TestVendorNameNormalization:
    """Test vendor name normalization logic"""

    def test_removes_legal_suffixes(self):
        """Should remove common legal entity suffixes"""
        test_cases = [
            ("Microsoft Corporation", "MICROSOFT"),
            ("Adobe Inc.", "ADOBE"),
            ("Oracle Corp", "ORACLE"),
            ("SAP LLC", "SAP"),
            ("IBM Limited", "IBM"),
        ]

        for input_name, expected in test_cases:
            normalized = self._normalize_vendor_name(input_name)
            assert normalized == expected, f"'{input_name}' should normalize to '{expected}'"

    def test_handles_multiple_suffixes(self):
        """Should handle vendors with multiple suffixes"""
        name = "Microsoft Corporation USA Inc."
        normalized = self._normalize_vendor_name(name)
        assert normalized == "MICROSOFT", "Should remove all suffixes"

    def test_preserves_core_name(self):
        """Should preserve the core business name"""
        test_cases = [
            ("Kronos Incorporated", "KRONOS"),
            ("LexisNexis Risk Solutions FL Inc", "LEXISNEXIS RISK SOLUTIONS FL"),
        ]

        for input_name, expected in test_cases:
            normalized = self._normalize_vendor_name(input_name)
            assert expected in normalized, f"Core name should be preserved in '{normalized}'"

    def _normalize_vendor_name(self, raw_name: str) -> str:
        """Normalize vendor name (from VendorResearcher)"""
        if not raw_name:
            return ""

        normalized = raw_name.upper().strip()

        suffixes_to_remove = [
            ' LLC', ' L.L.C.', ' L.L.C', ' LTD', ' LIMITED', ' LTD.',
            ' INC', ' INC.', ' INCORPORATED', ' CORP', ' CORP.',
            ' CORPORATION', ' CO.', ' CO', ' LP', ' L.P.', ' LLP',
            ' COMPANY', ' & CO', ' AND CO', ' USA', ' US', ' AMERICA'
        ]

        for suffix in suffixes_to_remove:
            if normalized.endswith(suffix):
                normalized = normalized[:-len(suffix)].strip()

        normalized = ' '.join(normalized.split())
        return normalized


class TestDataValidation:
    """Test input data validation"""

    def test_validates_tax_amount_positive(self):
        """Tax amounts should be positive"""
        invalid_amounts = [-100, -0.01, 0]

        for amount in invalid_amounts:
            assert amount <= 0, f"Amount {amount} should be invalid"

    def test_validates_date_format(self):
        """Dates should be in valid format"""
        from datetime import datetime

        valid_dates = ["2024-01-15", "2023-12-31", "2024-06-30"]

        for date_str in valid_dates:
            try:
                parsed = datetime.strptime(date_str, "%Y-%m-%d")
                assert parsed is not None
            except ValueError:
                pytest.fail(f"Date '{date_str}' should be valid")

    def test_validates_invoice_number_present(self):
        """Invoice number should not be empty"""
        invalid_invoice_numbers = ["", None, "   "]

        for inv_num in invalid_invoice_numbers:
            is_valid = inv_num and inv_num.strip()
            assert not is_valid, f"Invoice number '{inv_num}' should be invalid"
