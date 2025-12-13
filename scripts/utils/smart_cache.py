"""
Smart Caching Layer for Refund Engine

Provides multi-tier caching:
1. Vendor database (instant lookup)
2. Invoice extraction cache (persistent)
3. RAG results cache (category-based)
"""

import hashlib
import json
import os
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional


class SmartCache:
    """
    Multi-layer intelligent cache system
    """

    def __init__(self, cache_dir: str = "scripts/cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # Load vendor database
        self.vendor_db = self._load_vendor_database()

        # Initialize SQLite caches
        self.invoice_cache_db = self._init_invoice_cache()
        self.rag_cache_db = self._init_rag_cache()

    def _load_vendor_database(self) -> Dict:
        """Load vendor database from JSON"""
        vendor_db_path = Path("knowledge_base/vendors/vendor_database.json")

        if vendor_db_path.exists():
            with open(vendor_db_path, "r") as f:
                return json.load(f)
        else:
            print("⚠️  Vendor database not found, using empty database")
            return {}

    def _init_invoice_cache(self) -> sqlite3.Connection:
        """Initialize invoice extraction cache (SQLite)"""
        db_path = self.cache_dir / "invoice_cache.db"
        conn = sqlite3.connect(str(db_path), check_same_thread=False)

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS invoice_cache (
                file_hash TEXT PRIMARY KEY,
                file_path TEXT,
                invoice_data TEXT,
                cached_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP
            )
        """
        )

        conn.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_expires
            ON invoice_cache(expires_at)
        """
        )

        conn.commit()
        return conn

    def _init_rag_cache(self) -> sqlite3.Connection:
        """Initialize RAG results cache (SQLite)"""
        db_path = self.cache_dir / "rag_cache.db"
        conn = sqlite3.connect(str(db_path), check_same_thread=False)

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS rag_cache (
                category TEXT PRIMARY KEY,
                state_code TEXT,
                results TEXT,
                cached_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP
            )
        """
        )

        conn.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_state_category
            ON rag_cache(state_code, category)
        """
        )

        conn.commit()
        return conn

    def get_vendor_info(self, vendor_name: str) -> Optional[Dict]:
        """
        Get vendor information from database

        Returns None if vendor not found
        """
        # Exact match
        if vendor_name in self.vendor_db:
            return self.vendor_db[vendor_name]

        # Case-insensitive match
        vendor_lower = vendor_name.lower()
        for name, info in self.vendor_db.items():
            if name.lower() == vendor_lower:
                return info

        # Partial match (e.g., "Microsoft Corporation" matches "Microsoft")
        for name, info in self.vendor_db.items():
            if name.lower() in vendor_lower or vendor_lower in name.lower():
                return info

        return None

    def add_vendor(self, vendor_name: str, vendor_info: Dict):
        """Add a new vendor to the database"""
        self.vendor_db[vendor_name] = vendor_info

        # Save to file
        vendor_db_path = Path("knowledge_base/vendors/vendor_database.json")
        with open(vendor_db_path, "w") as f:
            json.dump(self.vendor_db, f, indent=2)

    def get_invoice_data(self, file_path: str) -> Optional[Dict]:
        """
        Get cached invoice extraction data

        Args:
            file_path: Path to invoice file

        Returns:
            Cached invoice data or None if not in cache/expired
        """
        try:
            file_hash = self._hash_file(file_path)

            cursor = self.invoice_cache_db.execute(
                """
                SELECT invoice_data, expires_at
                FROM invoice_cache
                WHERE file_hash = ?
            """,
                (file_hash,),
            )

            row = cursor.fetchone()
            if not row:
                return None

            invoice_data_json, expires_at_str = row

            # Check if expired
            expires_at = datetime.fromisoformat(expires_at_str)
            if datetime.now() > expires_at:
                # Clean up expired entry
                self.invoice_cache_db.execute(
                    "DELETE FROM invoice_cache WHERE file_hash = ?", (file_hash,)
                )
                self.invoice_cache_db.commit()
                return None

            return json.loads(invoice_data_json)
        except (sqlite3.Error, sqlite3.InterfaceError, ValueError, TypeError):
            # Thread safety or corrupted data issue - skip cache
            return None

    def set_invoice_data(self, file_path: str, invoice_data: Dict, ttl_days: int = 30):
        """
        Cache invoice extraction data

        Args:
            file_path: Path to invoice file
            invoice_data: Extracted invoice data
            ttl_days: Time to live in days (default: 30)
        """
        try:
            file_hash = self._hash_file(file_path)
            expires_at = datetime.now() + timedelta(days=ttl_days)

            self.invoice_cache_db.execute(
                """
                INSERT OR REPLACE INTO invoice_cache
                (file_hash, file_path, invoice_data, expires_at)
                VALUES (?, ?, ?, ?)
            """,
                (file_hash, file_path, json.dumps(invoice_data), expires_at.isoformat()),
            )

            self.invoice_cache_db.commit()
        except (sqlite3.Error, sqlite3.InterfaceError):
            # Thread safety issue - skip cache write
            pass

    def get_rag_results(
        self, category: str, state_code: str = "WA"
    ) -> Optional[List[Dict]]:
        """
        Get cached RAG search results for a product category

        Args:
            category: Product category (e.g., 'cloud_saas')
            state_code: State code (default: 'WA')

        Returns:
            Cached RAG results or None
        """
        cursor = self.rag_cache_db.execute(
            """
            SELECT results, expires_at
            FROM rag_cache
            WHERE category = ? AND state_code = ?
        """,
            (category, state_code),
        )

        row = cursor.fetchone()
        if not row:
            return None

        results_json, expires_at_str = row

        # Check if expired
        expires_at = datetime.fromisoformat(expires_at_str)
        if datetime.now() > expires_at:
            # Clean up expired entry
            self.rag_cache_db.execute(
                "DELETE FROM rag_cache WHERE category = ? AND state_code = ?",
                (category, state_code),
            )
            self.rag_cache_db.commit()
            return None

        return json.loads(results_json)

    def set_rag_results(
        self,
        category: str,
        results: List[Dict],
        state_code: str = "WA",
        ttl_days: int = 7,
    ):
        """
        Cache RAG search results

        Args:
            category: Product category
            results: RAG search results
            state_code: State code
            ttl_days: Time to live in days (default: 7)
        """
        expires_at = datetime.now() + timedelta(days=ttl_days)

        self.rag_cache_db.execute(
            """
            INSERT OR REPLACE INTO rag_cache
            (category, state_code, results, expires_at)
            VALUES (?, ?, ?, ?)
        """,
            (category, state_code, json.dumps(results), expires_at.isoformat()),
        )

        self.rag_cache_db.commit()

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        # Invoice cache stats
        cursor = self.invoice_cache_db.execute(
            """
            SELECT
                COUNT(*) as total,
                SUM(CASE WHEN expires_at > datetime('now') THEN 1 ELSE 0 END) as valid,
                SUM(CASE WHEN expires_at <= datetime('now') THEN 1 ELSE 0 END) as expired
            FROM invoice_cache
        """
        )
        invoice_stats = cursor.fetchone()

        # RAG cache stats
        cursor = self.rag_cache_db.execute(
            """
            SELECT
                COUNT(*) as total,
                SUM(CASE WHEN expires_at > datetime('now') THEN 1 ELSE 0 END) as valid,
                SUM(CASE WHEN expires_at <= datetime('now') THEN 1 ELSE 0 END) as expired
            FROM rag_cache
        """
        )
        rag_stats = cursor.fetchone()

        return {
            "vendor_database": {"total_vendors": len(self.vendor_db)},
            "invoice_cache": {
                "total": invoice_stats[0],
                "valid": invoice_stats[1],
                "expired": invoice_stats[2],
            },
            "rag_cache": {
                "total": rag_stats[0],
                "valid": rag_stats[1],
                "expired": rag_stats[2],
            },
        }

    def cleanup_expired(self):
        """Remove expired cache entries"""
        # Clean invoice cache
        self.invoice_cache_db.execute(
            """
            DELETE FROM invoice_cache
            WHERE expires_at <= datetime('now')
        """
        )

        # Clean RAG cache
        self.rag_cache_db.execute(
            """
            DELETE FROM rag_cache
            WHERE expires_at <= datetime('now')
        """
        )

        self.invoice_cache_db.commit()
        self.rag_cache_db.commit()

    def _hash_file(self, file_path: str) -> str:
        """Generate hash of file for caching"""
        # Use file path + modification time as hash
        # This is faster than hashing file contents
        file_stat = os.stat(file_path)
        hash_input = f"{file_path}_{file_stat.st_mtime}_{file_stat.st_size}"
        return hashlib.md5(hash_input.encode()).hexdigest()

    def close(self):
        """Close database connections"""
        self.invoice_cache_db.close()
        self.rag_cache_db.close()
