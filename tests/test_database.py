"""
Tests for database connection and basic operations
"""
import pytest
from unittest.mock import Mock, patch
from core.database import get_supabase_client


def test_get_supabase_client_returns_client():
    """Test that get_supabase_client returns a client object"""
    with patch.dict('os.environ', {
        'SUPABASE_URL': 'https://test.supabase.co',
        'SUPABASE_KEY': 'test-key'
    }):
        client = get_supabase_client()
        assert client is not None


def test_get_supabase_client_singleton():
    """Test that get_supabase_client returns the same instance"""
    with patch.dict('os.environ', {
        'SUPABASE_URL': 'https://test.supabase.co',
        'SUPABASE_KEY': 'test-key'
    }):
        client1 = get_supabase_client()
        client2 = get_supabase_client()
        assert client1 is client2
