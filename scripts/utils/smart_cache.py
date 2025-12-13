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
import threading
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

        # Thread lock for SQLite operations
        self._lock = threading.Lock()

        # Load vendor database
        self.vendor_db = self._load_vendor_database()

        # Initialize SQLite caches
        self.invoice_cache_db = self._init_invoice_cache()
        self.rag_cache_db = self._init_rag_cache()
        self.analysis_cache_db = self._init_analysis_cache()

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

    def _init_analysis_cache(self) -> sqlite3.Connection:
        """Initialize analysis results cache (vendor+category based)"""
        db_path = self.cache_dir / "analysis_cache.db"
        conn = sqlite3.connect(str(db_path), check_same_thread=False)

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS analysis_cache (
                cache_key TEXT PRIMARY KEY,
                vendor_name TEXT,
                category TEXT,
                state_code TEXT,
                tax_type TEXT,
                analysis_result TEXT,
                confidence REAL,
                hit_count INTEGER DEFAULT 1,
                cached_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP
            )
        """
        )

        conn.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_vendor_category
            ON analysis_cache(vendor_name, category, state_code)
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
        file_hash = self._hash_file(file_path)

        with self._lock:
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

    def set_invoice_data(self, file_path: str, invoice_data: Dict, ttl_days: int = 30):
        """
        Cache invoice extraction data

        Args:
            file_path: Path to invoice file
            invoice_data: Extracted invoice data
            ttl_days: Time to live in days (default: 30)
        """
        file_hash = self._hash_file(file_path)
        expires_at = datetime.now() + timedelta(days=ttl_days)

        with self._lock:
            self.invoice_cache_db.execute(
                """
                INSERT OR REPLACE INTO invoice_cache
                (file_hash, file_path, invoice_data, expires_at)
                VALUES (?, ?, ?, ?)
            """,
                (file_hash, file_path, json.dumps(invoice_data), expires_at.isoformat()),
            )

            self.invoice_cache_db.commit()

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
        with self._lock:
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

        with self._lock:
            self.rag_cache_db.execute(
                """
                INSERT OR REPLACE INTO rag_cache
                (category, state_code, results, expires_at)
                VALUES (?, ?, ?, ?)
            """,
                (category, state_code, json.dumps(results), expires_at.isoformat()),
            )

            self.rag_cache_db.commit()

    # ========== Analysis Cache (vendor+category based) ==========

    def _make_analysis_key(
        self,
        vendor_name: str,
        category: str,
        state_code: str = "WA",
        tax_type: str = "sales_tax"
    ) -> str:
        """Generate cache key from vendor+category+state+tax_type"""
        # Normalize vendor name (lowercase, strip whitespace)
        vendor_normalized = vendor_name.lower().strip()
        category_normalized = category.lower().strip()
        key = f"{vendor_normalized}|{category_normalized}|{state_code}|{tax_type}"
        return hashlib.md5(key.encode()).hexdigest()

    def get_analysis_result(
        self,
        vendor_name: str,
        category: str,
        state_code: str = "WA",
        tax_type: str = "sales_tax"
    ) -> Optional[Dict]:
        """
        Get cached analysis result for vendor+category combination.

        Args:
            vendor_name: Vendor name (e.g., 'Microsoft')
            category: Product category (e.g., 'cloud_saas')
            state_code: State code (default: 'WA')
            tax_type: Tax type (default: 'sales_tax')

        Returns:
            Cached analysis dict or None if not found/expired
        """
        cache_key = self._make_analysis_key(vendor_name, category, state_code, tax_type)

        with self._lock:
            cursor = self.analysis_cache_db.execute(
                """
                SELECT analysis_result, confidence, expires_at, hit_count
                FROM analysis_cache
                WHERE cache_key = ?
            """,
                (cache_key,),
            )

            row = cursor.fetchone()
            if not row:
                return None

            analysis_json, confidence, expires_at_str, hit_count = row

            # Check if expired
            expires_at = datetime.fromisoformat(expires_at_str)
            if datetime.now() > expires_at:
                self.analysis_cache_db.execute(
                    "DELETE FROM analysis_cache WHERE cache_key = ?", (cache_key,)
                )
                self.analysis_cache_db.commit()
                return None

            # Increment hit count
            self.analysis_cache_db.execute(
                "UPDATE analysis_cache SET hit_count = hit_count + 1 WHERE cache_key = ?",
                (cache_key,),
            )
            self.analysis_cache_db.commit()

        result = json.loads(analysis_json)
        result["_cache_hit"] = True
        result["_cache_confidence"] = confidence
        result["_cache_hits"] = hit_count + 1
        return result

    def set_analysis_result(
        self,
        vendor_name: str,
        category: str,
        analysis_result: Dict,
        confidence: float = 0.0,
        state_code: str = "WA",
        tax_type: str = "sales_tax",
        ttl_days: int = 30,
    ):
        """
        Cache analysis result for vendor+category combination.

        Args:
            vendor_name: Vendor name
            category: Product category
            analysis_result: Analysis result dict
            confidence: AI confidence score (0-1)
            state_code: State code
            tax_type: Tax type
            ttl_days: Time to live in days (default: 30)
        """
        cache_key = self._make_analysis_key(vendor_name, category, state_code, tax_type)
        expires_at = datetime.now() + timedelta(days=ttl_days)

        # Remove cache metadata before storing
        result_to_store = {k: v for k, v in analysis_result.items() if not k.startswith("_cache")}

        with self._lock:
            self.analysis_cache_db.execute(
                """
                INSERT OR REPLACE INTO analysis_cache
                (cache_key, vendor_name, category, state_code, tax_type,
                 analysis_result, confidence, expires_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    cache_key,
                    vendor_name.lower().strip(),
                    category.lower().strip(),
                    state_code,
                    tax_type,
                    json.dumps(result_to_store),
                    confidence,
                    expires_at.isoformat(),
                ),
            )
            self.analysis_cache_db.commit()

    def get_analysis_cache_stats(self) -> Dict[str, Any]:
        """Get analysis cache statistics"""
        with self._lock:
            # Overall stats
            cursor = self.analysis_cache_db.execute(
                """
                SELECT
                    COUNT(*) as total,
                    SUM(hit_count) as total_hits,
                    AVG(confidence) as avg_confidence
                FROM analysis_cache
                WHERE expires_at > datetime('now')
            """
            )
            stats = cursor.fetchone()

            # Top vendors by cache hits
            cursor = self.analysis_cache_db.execute(
                """
                SELECT vendor_name, SUM(hit_count) as hits
                FROM analysis_cache
                WHERE expires_at > datetime('now')
                GROUP BY vendor_name
                ORDER BY hits DESC
                LIMIT 10
            """
            )
            top_vendors = cursor.fetchall()

        return {
            "total_entries": stats[0] or 0,
            "total_hits": stats[1] or 0,
            "avg_confidence": round(stats[2] or 0, 2),
            "top_vendors": [{"vendor": v[0], "hits": v[1]} for v in top_vendors],
        }

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        with self._lock:
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
        with self._lock:
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

            # Clean analysis cache
            self.analysis_cache_db.execute(
                """
                DELETE FROM analysis_cache
                WHERE expires_at <= datetime('now')
            """
            )

            self.invoice_cache_db.commit()
            self.rag_cache_db.commit()
            self.analysis_cache_db.commit()

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
        self.analysis_cache_db.close()
