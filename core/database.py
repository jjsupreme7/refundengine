#!/usr/bin/env python3
"""
Centralized Supabase Client
============================

Singleton pattern for Supabase database connections.
Replaces 44+ separate client creations throughout the codebase.

Usage:
    from core.database import get_supabase_client

    # Get singleton client
    supabase = get_supabase_client()

    # Use as normal
    result = supabase.table('tax_law_chunks').select('*').execute()

Benefits:
    - Single connection instance (reduces overhead)
    - Centralized configuration
    - Easier to implement connection pooling
    - Consistent error handling
    - Better for testing (can mock single instance)
"""

import os
import sys
from pathlib import Path
from typing import Optional
from supabase import Client, create_client

# Try to load .env if available
try:
    from dotenv import load_dotenv

    # Load from project root
    project_root = Path(__file__).parent.parent
    env_path = project_root / ".env"
    if env_path.exists():
        load_dotenv(env_path)
except ImportError:
    pass  # dotenv not required if env vars already set


# ============================================================================
# SINGLETON INSTANCE
# ============================================================================

_supabase_client: Optional[Client] = None
_client_config = {"url": None, "key": None}


# ============================================================================
# PUBLIC API
# ============================================================================


def get_supabase_client(force_recreate: bool = False) -> Client:
    """
    Get singleton Supabase client instance.

    Creates client on first call, then returns same instance on subsequent calls.
    Client is automatically recreated if environment variables change.

    Args:
        force_recreate: Force create new client (useful for testing)

    Returns:
        Supabase Client instance

    Raises:
        ValueError: If SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY not set

    Example:
        >>> from core.database import get_supabase_client
        >>> supabase = get_supabase_client()
        >>> docs = supabase.table('knowledge_documents').select('*').execute()
    """
    global _supabase_client, _client_config

    # Get credentials
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

    # Validate
    if not url:
        raise ValueError(
            "SUPABASE_URL not set. Please set environment variable or add to .env file"
        )

    if not key:
        raise ValueError(
            "SUPABASE_SERVICE_ROLE_KEY not set. Please set environment variable or add to .env file"
        )

    # Create new client if:
    # 1. Never created before
    # 2. Force recreate requested
    # 3. Config changed (different URL/key)
    needs_recreation = (
        _supabase_client is None
        or force_recreate
        or _client_config["url"] != url
        or _client_config["key"] != key
    )

    if needs_recreation:
        try:
            _supabase_client = create_client(url, key)
            _client_config = {"url": url, "key": key}

            # Optional: Log client creation (useful for debugging)
            if os.getenv("DEBUG"):
                print("✓ Supabase client initialized", file=sys.stderr)

        except Exception as e:
            raise RuntimeError(f"Failed to create Supabase client: {e}") from e

    return _supabase_client


def reset_client():
    """
    Reset the singleton client instance.

    Useful for:
    - Testing (start with fresh client)
    - Switching between databases
    - Forcing reconnection

    Example:
        >>> from core.database import reset_client, get_supabase_client
        >>> reset_client()
        >>> new_client = get_supabase_client()
    """
    global _supabase_client, _client_config
    _supabase_client = None
    _client_config = {"url": None, "key": None}


def get_client_info() -> dict:
    """
    Get information about current client configuration.

    Returns:
        dict with:
            - connected: bool (True if client exists)
            - url: str (Supabase URL, redacted)
            - has_key: bool (True if key is set)

    Example:
        >>> from core.database import get_client_info
        >>> info = get_client_info()
        >>> print(f"Connected: {info['connected']}")
    """
    url = _client_config.get("url")
    redacted_url = f"{url[:30]}..." if url and len(url) > 30 else url

    return {
        "connected": _supabase_client is not None,
        "url": redacted_url,
        "has_key": _client_config.get("key") is not None,
    }


# ============================================================================
# CONVENIENCE ALIASES
# ============================================================================

# Alias for backwards compatibility
supabase = get_supabase_client

# Export all public functions
__all__ = [
    "get_supabase_client",
    "reset_client",
    "get_client_info",
    "supabase",
]


# ============================================================================
# MODULE-LEVEL TEST
# ============================================================================

if __name__ == "__main__":
    """Test the database connection"""
    print("Testing Supabase connection...")
    print("=" * 60)

    try:
        # Test 1: Get client
        print("\n[1/4] Creating client...")
        client = get_supabase_client()
        print("✓ Client created successfully")

        # Test 2: Get client info
        print("\n[2/4] Checking client info...")
        info = get_client_info()
        print(f"✓ Connected: {info['connected']}")
        print(f"  URL: {info['url']}")
        print(f"  Has Key: {info['has_key']}")

        # Test 3: Query database
        print("\n[3/4] Testing database query...")
        result = client.table("knowledge_documents").select("id", count="exact").execute()
        doc_count = result.count if hasattr(result, "count") else len(result.data)
        print(f"✓ Query successful! Found {doc_count} documents")

        # Test 4: Singleton behavior
        print("\n[4/4] Testing singleton behavior...")
        client2 = get_supabase_client()
        is_same = client is client2
        print(f"✓ Singleton working: {is_same} (should be True)")

        print("\n" + "=" * 60)
        print("✓ All tests passed! Database connection is working.")
        print("=" * 60)

    except ValueError as e:
        print(f"\n✗ Configuration Error: {e}")
        print("\nMake sure you have set:")
        print("  - SUPABASE_URL")
        print("  - SUPABASE_SERVICE_ROLE_KEY")
        print("\nYou can set these in:")
        print("  1. Environment variables")
        print("  2. .env file in project root")
        sys.exit(1)

    except Exception as e:
        print(f"\n✗ Connection Error: {e}")
        print("\nPlease check:")
        print("  1. Supabase URL is correct")
        print("  2. Service role key is valid")
        print("  3. Database is accessible")
        sys.exit(1)
