"""
Revixa v2 — AI Service Automated Unit Tests
============================================
AIService status kontrolleri, kural tabanlı dinamik fallback ve duygu dağılımı birim testleri.
"""

import sys
import os
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from services.ai_service import AIService, calculate_sentiment_distribution
from models import RawReview, Platform, AppMetadata, RatingDistribution, AIProvider


def test_calculate_sentiment_distribution():
    reviews = [
        RawReview(author="A", rating=5.0, content="Harika", platform=Platform.PLAY),  # Pos
        RawReview(author="B", rating=4.0, content="İyi", platform=Platform.PLAY),     # Pos
        RawReview(author="C", rating=3.0, content="Ortalama", platform=Platform.PLAY),# Neu
        RawReview(author="D", rating=1.0, content="Kötü", platform=Platform.PLAY),    # Neg
    ]

    senti = calculate_sentiment_distribution(reviews)

    assert senti.positive_pct == 50.0
    assert senti.neutral_pct == 25.0
    assert senti.negative_pct == 25.0


def test_ai_service_rule_based_fallback():
    service = AIService()

    reviews = [
        RawReview(author="User1", rating=5.0, content="Çok iyi harika tasarım", platform=Platform.PLAY),
        RawReview(author="User2", rating=1.0, content="Sürekli çöküyor donuyor", platform=Platform.PLAY),
    ]

    meta = AppMetadata(title="Örnek Oyun App", developer="DevStudio", category="Oyun")

    # Force AI fallback by passing None as provider response
    senti = calculate_sentiment_distribution(reviews)
    raw_fallback = service._rule_based_fallback(reviews, meta, senti, custom_prompt_extension="Donma şikayetlerini incele")

    assert "Örnek Oyun App" in raw_fallback["summary"]
    assert "Donma şikayetlerini incele" in raw_fallback["custom_focus_analysis"]
    assert raw_fallback["churn_risk_score"] == 50.0
    assert raw_fallback["satisfaction_score"] == 50.0
    assert len(raw_fallback["liked"]) > 0
    assert len(raw_fallback["bad"]) > 0


def test_ai_service_check_status():
    service = AIService()
    status_info = service.check_status()

    assert status_info.active_provider in [AIProvider.GEMINI, AIProvider.OLLAMA, AIProvider.NONE]
    assert isinstance(status_info.gemini_available, bool)
    assert isinstance(status_info.ollama_available, bool)
    assert status_info.ollama_model == "llama3.2"
