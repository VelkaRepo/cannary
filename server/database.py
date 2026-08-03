"""
Database handler for CanaryFile Engine using SQLite.
Stores token registries, trigger hit telemetry logs, and GeoIP enrichment details.
"""

import sqlite3
import json
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
import os


class DatabaseHandler:
    """Manages SQLite database operations for canary tokens and trigger logs."""

    def __init__(self, db_path: str = "canary_tokens.db"):
        self.db_path = db_path
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        """Returns a database connection with dict-like row access."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        """Initialize SQLite database tables and apply automatic migrations."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Table for registered canary tokens
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS tokens (
                    token_id TEXT PRIMARY KEY,
                    label TEXT,
                    file_type TEXT,
                    created_at TEXT NOT NULL,
                    is_active INTEGER DEFAULT 1
                )
            """)

            # Table for recorded canary trigger hits
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS hits (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    token_id TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    src_ip TEXT,
                    user_agent TEXT,
                    headers_json TEXT,
                    request_method TEXT,
                    query_params TEXT,
                    country TEXT DEFAULT 'Unknown',
                    city TEXT DEFAULT 'Unknown',
                    isp TEXT DEFAULT 'Unknown',
                    asn TEXT DEFAULT 'Unknown',
                    FOREIGN KEY (token_id) REFERENCES tokens (token_id)
                )
            """)

            # Migration check: Add GeoIP columns if upgrading from earlier version
            cursor.execute("PRAGMA table_info(hits)")
            existing_columns = {row["name"] for row in cursor.fetchall()}
            for col in ("country", "city", "isp", "asn"):
                if col not in existing_columns:
                    cursor.execute(f"ALTER TABLE hits ADD COLUMN {col} TEXT DEFAULT 'Unknown'")

            conn.commit()

    def register_token(self, token_id: str, label: str = "", file_type: str = "pdf") -> Dict[str, Any]:
        """Register a new canary token in the database."""
        created_at = datetime.now(timezone.utc).isoformat()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT OR REPLACE INTO tokens (token_id, label, file_type, created_at, is_active)
                VALUES (?, ?, ?, ?, 1)
                """,
                (token_id, label, file_type, created_at)
            )
            conn.commit()
        return {
            "token_id": token_id,
            "label": label,
            "file_type": file_type,
            "created_at": created_at,
            "is_active": True
        }

    def get_token(self, token_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve token details by ID."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM tokens WHERE token_id = ?", (token_id,))
            row = cursor.fetchone()
            if row:
                return dict(row)
        return None

    def log_hit(
        self,
        token_id: str,
        src_ip: str,
        user_agent: str,
        headers: Dict[str, str],
        method: str = "GET",
        query_params: str = "",
        country: str = "Unknown",
        city: str = "Unknown",
        isp: str = "Unknown",
        asn: str = "Unknown"
    ) -> Dict[str, Any]:
        """Record a trigger event hit with GeoIP enrichment details."""
        timestamp = datetime.now(timezone.utc).isoformat()
        headers_json = json.dumps(headers)
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO hits (token_id, timestamp, src_ip, user_agent, headers_json, request_method, query_params, country, city, isp, asn)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (token_id, timestamp, src_ip, user_agent, headers_json, method, query_params, country, city, isp, asn)
            )
            hit_id = cursor.lastrowid
            conn.commit()

        return {
            "hit_id": hit_id,
            "token_id": token_id,
            "timestamp": timestamp,
            "src_ip": src_ip,
            "user_agent": user_agent,
            "request_method": method,
            "query_params": query_params,
            "country": country,
            "city": city,
            "isp": isp,
            "asn": asn
        }

    def update_hit_enrichment(self, hit_id: int, geo_data: Dict[str, Any]) -> None:
        """Update GeoIP enrichment fields for an existing hit."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE hits
                SET country = ?, city = ?, isp = ?, asn = ?
                WHERE id = ?
                """,
                (
                    geo_data.get("country", "Unknown"),
                    geo_data.get("city", "Unknown"),
                    geo_data.get("isp", "Unknown"),
                    geo_data.get("asn", "Unknown"),
                    hit_id
                )
            )
            conn.commit()

    def list_tokens(self) -> List[Dict[str, Any]]:
        """List all registered canary tokens."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM tokens ORDER BY created_at DESC")
            return [dict(row) for row in cursor.fetchall()]

    def list_hits(self, token_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """List recorded hits, optionally filtered by token ID."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            if token_id:
                cursor.execute("SELECT * FROM hits WHERE token_id = ? ORDER BY id DESC", (token_id,))
            else:
                cursor.execute("SELECT * FROM hits ORDER BY id DESC")
            
            hits = []
            for row in cursor.fetchall():
                hit = dict(row)
                if hit.get("headers_json"):
                    hit["headers"] = json.loads(hit["headers_json"])
                hits.append(hit)
            return hits

    def get_analytics_stats(self) -> Dict[str, Any]:
        """Get aggregate telemetry stats for Web Dashboard."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) as total_tokens FROM tokens")
            total_tokens = cursor.fetchone()["total_tokens"]

            cursor.execute("SELECT COUNT(*) as total_hits FROM hits")
            total_hits = cursor.fetchone()["total_hits"]

            cursor.execute("SELECT COUNT(DISTINCT src_ip) as unique_ips FROM hits")
            unique_ips = cursor.fetchone()["unique_ips"]

            cursor.execute("SELECT country, COUNT(*) as count FROM hits WHERE country != 'Unknown' GROUP BY country ORDER BY count DESC LIMIT 5")
            top_countries = [dict(row) for row in cursor.fetchall()]

            return {
                "total_tokens": total_tokens,
                "total_hits": total_hits,
                "unique_ips": unique_ips,
                "top_countries": top_countries
            }
