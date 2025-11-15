"""
Tests for basic module imports
"""
import pytest


def test_core_database_import():
    """Test that core.database module can be imported"""
    from core import database
    assert database is not None


def test_core_chunking_import():
    """Test that core.chunking module can be imported"""
    from core import chunking
    assert chunking is not None


def test_analysis_modules_exist():
    """Test that analysis modules can be imported"""
    import analysis
    assert analysis is not None


def test_chatbot_module_exists():
    """Test that chatbot module exists"""
    import chatbot
    assert chatbot is not None
