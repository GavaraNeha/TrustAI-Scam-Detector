"""
Tiny sqlite cache so the same company/URL isn't re-researched (and
re-billed against free-tier quota) every time it comes up. Keyed by
a lowercased string (company name or URL) plus a "kind" tag so a
company-name cache entry and a URL cache entry never collide.
"""
import json
import sqlite3
import time
import os

import config


def _connect():
    os.makedirs(os.path.dirname(config.CACHE_DB_PATH), exist_ok=True)
    conn = sqlite3.connect(config.CACHE_DB_PATH)
    conn.execute(
        """CREATE TABLE IF NOT EXISTS cache (
            kind TEXT NOT NULL,
            key TEXT NOT NULL,
            value TEXT NOT NULL,
            cached_at REAL NOT NULL,
            PRIMARY KEY (kind, key)
        )"""
    )
    return conn


def get(kind, key):
    key = key.strip().lower()
    conn = _connect()
    row = conn.execute(
        "SELECT value, cached_at FROM cache WHERE kind = ? AND key = ?", (kind, key)
    ).fetchone()
    conn.close()

    if not row:
        return None

    value, cached_at = row
    age_hours = (time.time() - cached_at) / 3600
    if age_hours > config.CACHE_TTL_HOURS:
        return None

    return json.loads(value)


def set(kind, key, value):
    key = key.strip().lower()
    conn = _connect()
    conn.execute(
        "INSERT OR REPLACE INTO cache (kind, key, value, cached_at) VALUES (?, ?, ?, ?)",
        (kind, key, json.dumps(value), time.time()),
    )
    conn.commit()
    conn.close()
