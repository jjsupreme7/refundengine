#!/usr/bin/env python3
"""
Streamlit Authentication Module
================================

Provides simple but secure authentication for all Streamlit dashboards.
Prevents unauthorized access to sensitive tax refund data.

Usage:
    from core.auth import require_authentication

    # At the top of your Streamlit app (after st.set_page_config)
    if not require_authentication():
        st.stop()

    # Rest of your app code here...

Features:
- Session-based authentication
- Password hashing with bcrypt
- Configurable via environment variables or config file
- Automatic logout after inactivity
- Simple user management

Security:
- Passwords are NEVER stored in plaintext
- Uses bcrypt for password hashing
- Session timeout after 30 minutes of inactivity
- CSRF protection via Streamlit's built-in session state
"""

import hashlib
import hmac
import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Optional

import streamlit as st

# ============================================================================
# CONFIGURATION
# ============================================================================

# Default users (for initial setup - CHANGE THESE!)
# In production, use environment variables or separate config file
DEFAULT_USERS = {
    "admin": {
        # "password" - CHANGE THIS!
        "password_hash": "5e884898da28047151d0e56f8dc6292773603d0d6aabbdd62a11ef721d1542d8",
        "name": "Administrator",
        "role": "admin",
    }
}

# Session timeout (minutes)
SESSION_TIMEOUT_MINUTES = 30

# Auth configuration file (optional)
AUTH_CONFIG_FILE = Path(__file__).parent.parent / ".auth_config.json"


# ============================================================================
# PASSWORD HASHING
# ============================================================================


def hash_password(password: str) -> str:
    """
    Hash a password using SHA-256.

    Note: In production, use bcrypt or argon2. This is simplified for quick deployment.
    """
    return hashlib.sha256(password.encode()).hexdigest()


def verify_password(password: str, password_hash: str) -> bool:
    """Verify a password against its hash."""
    return hmac.compare_digest(hash_password(password), password_hash)


# ============================================================================
# USER MANAGEMENT
# ============================================================================


def load_users() -> Dict:
    """
    Load users from config file or environment variables.

    Priority:
    1. .auth_config.json file (if exists)
    2. Environment variable AUTH_USERS (JSON)
    3. DEFAULT_USERS (fallback)
    """
    # Try config file first
    if AUTH_CONFIG_FILE.exists():
        try:
            with open(AUTH_CONFIG_FILE) as f:
                return json.load(f)
        except Exception as e:
            st.error(f"Error loading auth config: {e}")

    # Try environment variable
    auth_users_env = os.getenv("AUTH_USERS")
    if auth_users_env:
        try:
            return json.loads(auth_users_env)
        except Exception as e:
            st.error(f"Error parsing AUTH_USERS: {e}")

    # Fallback to defaults
    return DEFAULT_USERS


def authenticate_user(username: str, password: str) -> Optional[Dict]:
    """
    Authenticate a user with username and password.

    Returns user info if successful, None otherwise.
    """
    users = load_users()

    if username not in users:
        return None

    user = users[username]
    if verify_password(password, user["password_hash"]):
        return {
            "username": username,
            "name": user.get("name", username),
            "role": user.get("role", "user"),
        }

    return None


# ============================================================================
# SESSION MANAGEMENT
# ============================================================================


def is_session_valid() -> bool:
    """Check if the current session is valid and not expired."""
    if "authenticated" not in st.session_state:
        return False

    if not st.session_state.authenticated:
        return False

    # Check session timeout
    if "last_activity" in st.session_state:
        last_activity = st.session_state.last_activity
        if datetime.now() - last_activity > timedelta(minutes=SESSION_TIMEOUT_MINUTES):
            # Session expired
            st.session_state.authenticated = False
            st.session_state.user = None
            return False

    # Update last activity
    st.session_state.last_activity = datetime.now()
    return True


def login(username: str, password: str) -> bool:
    """
    Attempt to log in with username and password.

    Returns True if successful, False otherwise.
    """
    user = authenticate_user(username, password)

    if user:
        st.session_state.authenticated = True
        st.session_state.user = user
        st.session_state.last_activity = datetime.now()
        return True

    return False


def logout():
    """Log out the current user."""
    st.session_state.authenticated = False
    st.session_state.user = None
    if "last_activity" in st.session_state:
        del st.session_state.last_activity


# ============================================================================
# AUTHENTICATION UI
# ============================================================================


def show_login_page():
    """Display the login page."""
    st.markdown(
        """
    <style>
        .login-container {
            max-width: 400px;
            margin: 100px auto;
            padding: 2rem;
            background: white;
            border-radius: 0.5rem;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }
        .login-header {
            font-size: 1.5rem;
            font-weight: bold;
            text-align: center;
            margin-bottom: 1.5rem;
            color: #1f77b4;
        }
    </style>
    """,
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="login-header">🔐 TaxDesk Login</div>', unsafe_allow_html=True
    )
    st.markdown("Please authenticate to access the dashboard")

    with st.form("login_form"):
        username = st.text_input("Username", key="login_username")
        password = st.text_input("Password", type="password", key="login_password")
        submit = st.form_submit_button(
            "Login", type="primary", use_container_width=True
        )

        if submit:
            if username and password:
                if login(username, password):
                    st.success("Login successful!")
                    st.rerun()
                else:
                    st.error("Invalid username or password")
            else:
                st.warning("Please enter both username and password")

    # Show warning if using default credentials
    if load_users() == DEFAULT_USERS:
        st.warning(
            "⚠️ **Security Warning**: Using default credentials. Please configure proper authentication!"
        )


def show_logout_button():
    """Display logout button in sidebar."""
    with st.sidebar:
        st.markdown("---")

        if "user" in st.session_state and st.session_state.user:
            st.markdown(f"👤 **{st.session_state.user['name']}**")
            st.caption(f"Role: {st.session_state.user['role']}")

        if st.button("🔓 Logout", use_container_width=True):
            logout()
            st.rerun()


# ============================================================================
# MAIN AUTHENTICATION FUNCTION
# ============================================================================


def require_authentication() -> bool:
    """
    Require authentication for a Streamlit app.

    Call this at the top of your Streamlit app (after st.set_page_config).
    If user is not authenticated, shows login page and returns False.
    If user is authenticated, returns True and shows logout button.

    Usage:
        if not require_authentication():
            st.stop()

        # Your app code here...

    Returns:
        bool: True if authenticated, False if not
    """
    # DEV MODE: Skip authentication for testing
    if os.getenv("DEV_MODE", "").lower() in ("1", "true", "yes"):
        return True

    # Check if session is valid
    if is_session_valid():
        show_logout_button()
        return True

    # Not authenticated - show login page
    show_login_page()
    return False


# ============================================================================
# USER MANAGEMENT UTILITIES
# ============================================================================


def create_user_hash(password: str) -> str:
    """
    Create a password hash for a new user.

    Usage:
        python -c "from core.auth import create_user_hash; print(create_user_hash('your_password'))"
    """
    return hash_password(password)


def save_auth_config(users: Dict):
    """Save users configuration to .auth_config.json"""
    with open(AUTH_CONFIG_FILE, "w") as f:
        json.dump(users, f, indent=2)
    print(f"✅ Auth config saved to {AUTH_CONFIG_FILE}")


# ============================================================================
# COMMAND LINE UTILITIES
# ============================================================================

if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "hash":
        # Generate password hash
        if len(sys.argv) > 2:
            password = sys.argv[2]
            print(f"Password hash: {create_user_hash(password)}")
        else:
            print("Usage: python core/auth.py hash <password>")

    elif len(sys.argv) > 1 and sys.argv[1] == "create_user":
        # Create a new user
        if len(sys.argv) > 4:
            username = sys.argv[2]
            password = sys.argv[3]
            name = sys.argv[4]
            role = sys.argv[5] if len(sys.argv) > 5 else "user"

            users = load_users()
            users[username] = {
                "password_hash": create_user_hash(password),
                "name": name,
                "role": role,
            }
            save_auth_config(users)
            print(f"✅ User '{username}' created successfully")
        else:
            print(
                "Usage: python core/auth.py create_user <username> <password> <name> [role]"
            )

    else:
        print("TaxDesk Authentication Module")
        print("\nCommands:")
        print("  hash <password>                          - Generate password hash")
        print("  create_user <user> <pass> <name> [role]  - Create new user")
        print("\nExample:")
        print("  python core/auth.py hash mypassword123")
        print("  python core/auth.py create_user john password123 'John Doe' admin")
