"""
Revixa — Pydantic Veri Modelleri
=================================
Tüm API istek/yanıt yapıları burada tanımlanır.
"""

from pydantic import BaseModel, HttpUrl, field_validator
from typing import Literal
from enum import Enum


# ─────────────────────────────────────────────
#  Enum: Platform ve AI Provider
# ─────────────────────────────────────────────

class Platform(str, Enum):
    """Hangi mağazadan yorum çekileceği."""
    AUTO      = "auto"       # URL'ye bakarak otomatik tespit et
    PLAY      = "play"       # Google Play Store
    APPSTORE  = "appstore"   # Apple App Store


class AIProvider(str, Enum):
    """Analizi yapan AI servisi."""
    GEMINI = "gemini"
    OLLAMA = "ollama"
    NONE   = "none"          # Hiçbiri mevcut değil


# ─────────────────────────────────────────────
#  İstek Modeli
# ─────────────────────────────────────────────

class AnalysisRequest(BaseModel):
    """
    Kullanıcının gönderdiği analiz isteği.

    Örnek:
        {
            "url": "https://play.google.com/store/apps/details?id=com.instagram.android",
            "platform": "auto",
            "max_reviews": 150
        }
    """
    url: str
    platform: Platform = Platform.AUTO
    max_reviews: int = 0  # 0 = sınırsız (tüm yorumlar)

    @field_validator("max_reviews")
    @classmethod
    def clamp_reviews(cls, v: int) -> int:
        """0 = sınırsız, pozitif sayı = maksimum yorum sayısı."""
        return max(0, v)

    @field_validator("url")
    @classmethod
    def validate_url(cls, v: str) -> str:
        """URL'nin Play Store veya App Store olduğunu kontrol et."""
        allowed = ["play.google.com", "apps.apple.com"]
        if not any(domain in v for domain in allowed):
            raise ValueError(
                "URL Google Play Store veya Apple App Store'a ait olmalıdır."
            )
        return v.strip()


# ─────────────────────────────────────────────
#  Ham Yorum Modeli (Scraper çıktısı)
# ─────────────────────────────────────────────

class RawReview(BaseModel):
    """Scraper'dan gelen ham yorum verisi."""
    author: str = "Anonim"
    rating: float = 0.0       # 1.0 – 5.0 arası
    content: str
    date: str = ""


# ─────────────────────────────────────────────
#  Analiz Sonuç Modelleri
# ─────────────────────────────────────────────

class FeatureItem(BaseModel):
    """
    Tek bir özellik/bulgu.

    Örnek:
        {
            "title": "Kullanıcı arayüzü",
            "description": "Kullanıcılar arayüzün sade ve kolay olduğunu vurguluyor.",
            "review_count": 42,
            "example_quotes": ["Çok kullanışlı!", "Arayüz mükemmel."]
        }
    """
    title: str
    description: str
    review_count: int = 0
    example_quotes: list[str] = []


class AnalysisResult(BaseModel):
    """
    Tam analiz sonucu — API'den dönen yanıt.

    Alanlar:
        app_name        : Uygulamanın adı
        platform        : Analiz edilen platform
        total_reviews   : İşlenen toplam yorum sayısı
        ai_provider     : Analizi yapan AI (gemini veya ollama)
        liked           : Beğenilen özellikler listesi
        needs_improve   : Geliştirilmesi gereken özellikler
        bad             : Kötü / eksik özellikler
        summary         : Genel özet (1-2 paragraf)
        markdown_report : İndirilebilir Markdown rapor metni
    """
    app_name: str
    platform: Platform
    total_reviews: int
    ai_provider: AIProvider

    liked: list[FeatureItem] = []
    needs_improve: list[FeatureItem] = []
    bad: list[FeatureItem] = []

    summary: str = ""
    markdown_report: str = ""


# ─────────────────────────────────────────────
#  AI Durum Modeli  (GET /ai-status için)
# ─────────────────────────────────────────────

class AIStatus(BaseModel):
    """Gemini ve Ollama'nın anlık durumu."""
    gemini_available: bool
    ollama_available: bool
    ollama_model: str = ""
    active_provider: AIProvider


# ─────────────────────────────────────────────
#  Hata Modeli
# ─────────────────────────────────────────────

class ErrorResponse(BaseModel):
    """API hata yanıtı."""
    error: str
    detail: str = ""
