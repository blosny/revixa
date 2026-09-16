"""
Revixa v2 — Scraper Service Automated Unit Tests
=================================================
ScraperService platform tespiti, URL ID ayıklama, pazar istatistikleri ve coğrafi tekleştirme birim testleri.
"""

import sys
import os
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from services.scraper_service import ScraperService
from models import Platform, RawReview


def test_detect_platform():
    assert ScraperService.detect_platform("https://play.google.com/store/apps/details?id=com.spotify.music") == Platform.PLAY
    assert ScraperService.detect_platform("https://apps.apple.com/tr/app/whatsapp-messenger/id310633997") == Platform.APPSTORE

    with pytest.raises(ValueError, match="Geçersiz mağaza adresi"):
        ScraperService.detect_platform("https://example.com/invalid-url")


def test_extract_play_app_id():
    valid_url = "https://play.google.com/store/apps/details?id=com.spotify.music&hl=tr"
    assert ScraperService.extract_play_app_id(valid_url) == "com.spotify.music"

    invalid_host = "https://google.com/store/apps/details?id=com.spotify.music"
    with pytest.raises(ValueError, match="Sadece resmi play.google.com"):
        ScraperService.extract_play_app_id(invalid_host)

    missing_id = "https://play.google.com/store/apps/details?hl=tr"
    with pytest.raises(ValueError, match="paket kimliği"):
        ScraperService.extract_play_app_id(missing_id)


def test_extract_appstore_info():
    appstore_url = "https://apps.apple.com/tr/app/foto%C4%9Fraf-d%C3%Bczenleyici/id123456789"
    name, country, app_id = ScraperService.extract_appstore_info(appstore_url)

    assert name == "foto%C4%9Fraf-d%C3%Bczenleyici"
    assert country == "tr"
    assert app_id == "123456789"

    invalid_host = "https://apple.com/tr/app/test/id123"
    with pytest.raises(ValueError, match="Sadece resmi apps.apple.com"):
        ScraperService.extract_appstore_info(invalid_host)


def test_calculate_market_statistics():
    reviews = [
        RawReview(author="K1", rating=5.0, content="Harika bir uygulama çok beğendim süper", country="TR", platform=Platform.PLAY),
        RawReview(author="K2", rating=4.0, content="Çok faydalı bir uygulama harika", country="TR", platform=Platform.PLAY),
        RawReview(author="K3", rating=1.0, content="Great app love it very good", country="US", platform=Platform.PLAY),
    ]

    country_dist, avg_len, keywords = ScraperService.calculate_market_statistics(reviews)

    assert country_dist.counts["TR"] == 2
    assert country_dist.counts["US"] == 1
    assert country_dist.percentages["TR"] == 66.7
    assert country_dist.percentages["US"] == 33.3
    assert avg_len > 0
    assert len(keywords) > 0
