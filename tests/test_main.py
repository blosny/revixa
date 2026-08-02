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
