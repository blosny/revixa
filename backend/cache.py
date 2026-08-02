"""
Revixa — SQLite Caching Engine
===============================
Aynı uygulama bağlantısı için tekrarlanan istekleri önbelleğe alır.
Yorum çekme ve AI analiz süresini 0.05 saniyeye düşürür.
İstenildiğinde veritabanı temizlenebilir.
"""

import os
import sqlite3
import json
import logging
from typing import Optional

logger = logging.getLogger("revixa.cache")

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "revixa_cache.db")


def init_cache_db():
    """SQLite önbellek veritabanını ilklendirir."""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS analysis_cache (
                cache_key TEXT PRIMARY KEY,
                result_json TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()


def get_cached_analysis(cache_key: str) -> Optional[dict]:
    """Önbellekten analiz sonucunu getirir (1 saatlik geçerlilik süresi)."""
    try:
        init_cache_db()
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT result_json FROM analysis_cache
                WHERE cache_key = ? AND created_at >= datetime('now', '-1 hour')
            """, (cache_key,))
            row = cursor.fetchone()
            if row:
                logger.info(f"ÖNBELLEKTEN DÖNÜLDÜ (Cache Hit): {cache_key}")
                data = json.loads(row[0])
                data["cached_response"] = True
                return data
    except Exception as e:
        logger.warning(f"Cache okuma hatası: {e}")
    return None


def save_cached_analysis(cache_key: str, result_dict: dict):
    """Analiz sonucunu önbelleğe kaydeder."""
    try:
        init_cache_db()
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO analysis_cache (cache_key, result_json, created_at)
                VALUES (?, ?, datetime('now'))
            """, (cache_key, json.dumps(result_dict, ensure_ascii=False)))
            conn.commit()
            logger.info(f"Önbelleğe kaydedildi: {cache_key}")
    except Exception as e:
        logger.warning(f"Cache yazma hatası: {e}")


def clear_cache_db() -> int:
    """Tüm önbellek veritabanını siler ve temizler."""
    try:
        init_cache_db()
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM analysis_cache")
            rows_deleted = cursor.rowcount
            conn.commit()
            logger.info(f"Önbellek veritabanı temizlendi! Silinen kayıt sayısı: {rows_deleted}")
            return rows_deleted
    except Exception as e:
        logger.error(f"Cache temizleme hatası: {e}")
        return 0
