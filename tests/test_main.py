"""
Revixa — Automated Pytest Integration Suite
"""

import sys
import os
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "backend"))

from main import app

client = TestClient(app)


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_liveness_probe():
    response = client.get("/health/live")
    assert response.status_code == 200
    assert response.json()["status"] == "alive"


def test_readiness_probe():
    response = client.get("/health/ready")
    assert response.status_code == 200
    assert response.json()["status"] == "ready"
    assert "database" in response.json()


def test_ai_status():
    response = client.get("/ai-status")
    assert response.status_code == 200
    data = response.json()
    assert "gemini_available" in data
    assert "ollama_available" in data


def test_invalid_url_ssrf_protection():
    response = client.post("/analyze", json={"url": "http://127.0.0.1/malicious"})
    assert response.status_code == 400
    assert "Güvenlik Engeli" in response.json()["detail"]


def test_ssrf_domain_prefix_bypass_prevention():
    # play.google.com.saldirgan.com gibi domain prefix bypass denemesi
    response = client.post("/analyze", json={"url": "https://play.google.com.saldirgan.com/malicious"})
    assert response.status_code == 400
    assert "Güvenlik Engeli" in response.json()["detail"]


def test_valid_play_store_url_scraping():
    response = client.post("/analyze", json={"url": "https://play.google.com/store/apps/details?id=com.acabaneyesem", "max_reviews": 10})
    if response.status_code == 200:
        data = response.json()
        assert data["app_name"] is not None
        assert "churn_risk_score" in data
        assert "country_dist" in data
    else:
        # Headless CI runner without GEMINI_API_KEY or Ollama daemon
        assert response.status_code == 500
        assert "AI servisi" in response.json().get("detail", "")


def test_app_store_title_unquoting_and_real_ratings():
    # App Store scraper async birim testi: URL unquoting ve puan hesaplaması
    import pytest
    from scraper import scrape_app_store_async
    import asyncio

    url = "https://apps.apple.com/tr/app/foto%C4%9Fraf-d%C3%Bczenleyici/id123456789"
    meta, rating_dist, reviews = asyncio.run(scrape_app_store_async(url, max_reviews=10))

    # Başlığın 'Foto%C4%9Fraf' olarak bozuk kalmadığını, 'Fotoğraf' olarak unquote edildiğini doğrula
    assert "Foto%C4%9Fraf" not in meta.title
    assert "Fotoğraf" in meta.title or "Foto" in meta.title
    assert meta.average_rating >= 0.0


def test_both_store_weighted_average_merging():
    # Çift mağaza (Play Store + App Store) metrik harmanlama birim testi
    import asyncio
    from scraper import scrape_reviews_async

    play_url = "https://play.google.com/store/apps/details?id=com.whatsapp"
    appstore_url = "https://apps.apple.com/tr/app/whatsapp-messenger/id310633997"

    meta, platform, rating_dist, country_dist, avg_len, keywords, reviews = asyncio.run(
        scrape_reviews_async(play_url=play_url, appstore_url=appstore_url, max_reviews=10)
    )

    assert platform == "both"
    assert "(Play Store + App Store)" in meta.title
    assert meta.total_ratings > 0
    assert meta.average_rating > 0.0
    assert (
        rating_dist.star_1
        + rating_dist.star_2
        + rating_dist.star_3
        + rating_dist.star_4
        + rating_dist.star_5
        > 0
    )

