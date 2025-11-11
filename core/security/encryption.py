"""
Encryption Service Module

Provides field-level encryption for sensitive data in database storage.
Uses Fernet (symmetric encryption) for performance and simplicity.
"""

import os
import base64
from typing import Optional, Union
from cryptography.fernet import Fernet, InvalidToken


class EncryptionService:
    """
    Handles encryption and decryption of sensitive fields.

    Uses Fernet (AES-128 in CBC mode) for symmetric encryption.
    Key must be stored in environment variable: ENCRYPTION_KEY
    """

    def __init__(self, key: Optional[bytes] = None):
        """
        Initialize encryption service.

        Args:
            key: Encryption key (bytes). If None, loads from ENCRYPTION_KEY env var.

        Raises:
            ValueError: If no key provided and ENCRYPTION_KEY not set
        """
        if key is None:
            key_str = os.getenv("ENCRYPTION_KEY")
            if not key_str:
                raise ValueError(
                    "ENCRYPTION_KEY environment variable not set. "
                    "Generate one with: python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())'"
                )
            key = key_str.encode()

        try:
            self.cipher = Fernet(key)
        except Exception as e:
            raise ValueError(f"Invalid encryption key: {e}")

    def encrypt(self, value: str) -> str:
        """
        Encrypt a string value.

        Args:
            value: Plain text string to encrypt

        Returns:
            Base64-encoded encrypted string (safe for database storage)
        """
        if not value:
            return value

        try:
            encrypted_bytes = self.cipher.encrypt(value.encode("utf-8"))
            return encrypted_bytes.decode("utf-8")
        except Exception as e:
            raise ValueError(f"Encryption failed: {e}")

    def decrypt(self, encrypted_value: str) -> str:
        """
        Decrypt an encrypted string.

        Args:
            encrypted_value: Base64-encoded encrypted string

        Returns:
            Decrypted plain text string

        Raises:
            ValueError: If decryption fails (wrong key, corrupted data)
        """
        if not encrypted_value:
            return encrypted_value

        try:
            decrypted_bytes = self.cipher.decrypt(encrypted_value.encode("utf-8"))
            return decrypted_bytes.decode("utf-8")
        except InvalidToken:
            raise ValueError(
                "Decryption failed: Invalid encryption key or corrupted data"
            )
        except Exception as e:
            raise ValueError(f"Decryption failed: {e}")

    def encrypt_dict(self, data: dict, fields_to_encrypt: list) -> dict:
        """
        Encrypt specified fields in a dictionary.

        Args:
            data: Dictionary with data
            fields_to_encrypt: List of field names to encrypt

        Returns:
            Dictionary with specified fields encrypted
        """
        encrypted_data = data.copy()

        for field in fields_to_encrypt:
            if field in encrypted_data and encrypted_data[field]:
                if isinstance(encrypted_data[field], str):
                    encrypted_data[field] = self.encrypt(encrypted_data[field])

        return encrypted_data

    def decrypt_dict(self, data: dict, fields_to_decrypt: list) -> dict:
        """
        Decrypt specified fields in a dictionary.

        Args:
            data: Dictionary with encrypted data
            fields_to_decrypt: List of field names to decrypt

        Returns:
            Dictionary with specified fields decrypted
        """
        decrypted_data = data.copy()

        for field in fields_to_decrypt:
            if field in decrypted_data and decrypted_data[field]:
                if isinstance(decrypted_data[field], str):
                    try:
                        decrypted_data[field] = self.decrypt(decrypted_data[field])
                    except ValueError:
                        # Field might not be encrypted, leave as-is
                        pass

        return decrypted_data

    @staticmethod
    def generate_key() -> str:
        """
        Generate a new encryption key.

        Returns:
            Base64-encoded encryption key (store in ENCRYPTION_KEY env var)
        """
        return Fernet.generate_key().decode("utf-8")

    @staticmethod
    def mask_value(value: str, mask_type: str = "email") -> str:
        """
        Mask a value for display (alternative to encryption for non-sensitive display).

        Args:
            value: Value to mask
            mask_type: Type of masking ("email", "account", "phone", "name")

        Returns:
            Masked value
        """
        if not value:
            return value

        if mask_type == "email":
            # john.smith@company.com → john.s***@company.com
            if "@" in value:
                local, domain = value.split("@", 1)
                if len(local) > 3:
                    masked_local = local[: min(6, len(local))] + "***"
                else:
                    masked_local = local[0] + "***"
                return f"{masked_local}@{domain}"
            return value

        elif mask_type == "account":
            # 123456789 → ****6789
            if len(value) > 4:
                return "****" + value[-4:]
            return "****"

        elif mask_type == "phone":
            # (425) 555-1234 → (***) ***-1234
            # Remove non-digits first
            digits = "".join(c for c in value if c.isdigit())
            if len(digits) >= 4:
                return "(***) ***-" + digits[-4:]
            return "***-****"

        elif mask_type == "name":
            # John Smith → J*** S***
            parts = value.split()
            if len(parts) > 1:
                masked = " ".join(part[0] + "***" for part in parts)
                return masked
            elif len(value) > 1:
                return value[0] + "***"
            return "***"

        elif mask_type == "tax_id":
            # 12-3456789 → **-****789
            if "-" in value:
                parts = value.split("-")
                if len(parts) == 2 and len(parts[1]) >= 3:
                    return "**-****" + parts[1][-3:]
            return "**-*******"

        else:
            # Generic masking: show first 2 and last 2 characters
            if len(value) > 6:
                return value[:2] + "***" + value[-2:]
            return "***"


class PIIFieldMapper:
    """
    Maps database fields to PII encryption/masking strategies.
    """

    # Fields that should be encrypted in database
    ENCRYPTED_FIELDS = [
        "contact_email",
        "contact_phone",
        "approver_email",
        "bank_account",
        "routing_number",
        "tax_id",
    ]

    # Fields that should be masked in Excel exports (field → mask_type)
    MASKED_FIELDS = {
        "contact_email": "email",
        "contact_phone": "phone",
        "approver_email": "email",
        "approver_name": "name",
        "bank_account": "account",
        "routing_number": "account",
        "tax_id": "tax_id",
        "account_number": "account",
    }

    @classmethod
    def should_encrypt(cls, field_name: str) -> bool:
        """Check if field should be encrypted"""
        return field_name in cls.ENCRYPTED_FIELDS

    @classmethod
    def should_mask(cls, field_name: str) -> bool:
        """Check if field should be masked in exports"""
        return field_name in cls.MASKED_FIELDS

    @classmethod
    def get_mask_type(cls, field_name: str) -> Optional[str]:
        """Get masking type for field"""
        return cls.MASKED_FIELDS.get(field_name)
