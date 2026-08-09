"""
Revixa v2 — Custom Prompt Extension Automated Tests
==================================================
Kullanıcı tanımlı özel istem (custom prompt extension) testleri.
"""

import sys
import os
import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from main import app
from database import init_db
from models import RawReview, Platform, AppMetadata, RatingDistribution, CountryDistribution, AnalysisResult, AIProvider

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_db():
    init_db()


def test_custom_prompt_extension_passed_to_router():
    custom_instruction = "Sadece abonelik iptali ve fiyat artisi sikayetlerine odaklan."

    from analyzer import get_router
    router = get_router()

    with patch('main.get_cached_analysis', return_value=None), \
         patch.object(router, 'analyze') as mock_analyze:
        
        mock_analyze.return_value = AnalysisResult(
            app_name="Test App",
            platform=Platform.PLAY,
            total_reviews=1,
            ai_provider=AIProvider.GEMINI,
            metadata=AppMetadata(title="Test App"),
            summary="Abonelik ve fiyat artisi elestirileri one cikmaktadir."
        )

        response = client.post(
            "/analyze",
            json={
                "url": "https://play.google.com/store/apps/details?id=com.spotify.music&hl=tr",
                "custom_prompt_extension": custom_instruction
            }
        )

        assert response.status_code == 200
        assert mock_analyze.called
        kwargs = mock_analyze.call_args.kwargs
        assert kwargs.get("custom_prompt_extension") == custom_instruction
