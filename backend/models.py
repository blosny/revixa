"""
Revixa — Pydantic Data Models & Market Metrics
===============================================
Tüm API veri yapıları, Zenginleştirilmiş Pazar Analizi Şemaları ve Güvenlik Modelleri.
"""

from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class Platform(str, Enum):
    PLAY = "play"
    APPSTORE = "appstore"
    BOTH = "both"
    AUTO = "auto"


class AIProvider(str, Enum):
    GEMINI = "gemini"
    OLLAMA = "ollama"
    NONE = "none"


class RawReview(BaseModel):
    author: str = "Anonim"
    rating: float = 0.0
    content: str
    date: str = ""
    country: str = "TR"
    platform: Platform = Platform.PLAY


class FeatureItem(BaseModel):
    title: str
    description: str
    review_count: int = 0
    example_quotes: list[str] = Field(default_factory=list)


class CompetitorMention(BaseModel):
    competitor_name: str
    mention_count: int = 0
    context: str = ""


class AppMetadata(BaseModel):
    title: str
    developer: str = "Bilinmiyor"
    category: str = "Genel"
    average_rating: float = 0.0
    total_ratings: int = 0
    version: str = "v1.0"
    updated_date: str = "—"
    price: str = "Ücretsiz"
    contains_ads: bool = False


class RatingDistribution(BaseModel):
    star_5: int = 0
    star_4: int = 0
    star_3: int = 0
    star_2: int = 0
    star_1: int = 0


class SentimentDistribution(BaseModel):
    positive_pct: float = 0.0
    neutral_pct: float = 0.0
    negative_pct: float = 0.0


class CountryDistribution(BaseModel):
    counts: dict[str, int] = Field(default_factory=dict)
    percentages: dict[str, float] = Field(default_factory=dict)


class KeywordCount(BaseModel):
    keyword: str
    count: int


class AnalysisRequest(BaseModel):
    url: Optional[str] = None
    play_url: Optional[str] = None
    appstore_url: Optional[str] = None
    platform: Platform = Platform.AUTO
    max_reviews: int = Field(default=0, ge=0)


class AnalysisResult(BaseModel):
    app_name: str
    platform: Platform
    total_reviews: int
    ai_provider: AIProvider
    
    # Detaylı Pazar İstatistikleri
    metadata: AppMetadata = Field(default_factory=AppMetadata)
    rating_dist: RatingDistribution = Field(default_factory=RatingDistribution)
    sentiment_dist: SentimentDistribution = Field(default_factory=SentimentDistribution)
    country_dist: CountryDistribution = Field(default_factory=CountryDistribution)
    top_keywords: list[KeywordCount] = Field(default_factory=list)
    avg_review_length: int = 0
    
    # 🚀 ZENGİNLEŞTİRİLMİŞ YENİ PAZAR İÇGÖRÜLERİ
    churn_risk_score: float = 0.0          # 0 - 100 Arası Müşteri Kayıp Riski Skoru
    version_issue_warning: str = ""       # Güncelleme Sonrası Hata Uyarısı
    competitor_mentions: list[CompetitorMention] = Field(default_factory=list) # Rakip Bahisleri
    feature_rankings: list[str] = Field(default_factory=list)                   # En Çok İstenen Özellik Sıralaması
    
    # AI Kategorizasyonu
    summary: str
    liked: list[FeatureItem] = Field(default_factory=list)
    needs_improve: list[FeatureItem] = Field(default_factory=list)
    bad: list[FeatureItem] = Field(default_factory=list)
    
    # Markdown Raporu
    markdown_report: str = ""
    cached_response: bool = False


class AIStatus(BaseModel):
    gemini_available: bool
    ollama_available: bool
    ollama_model: str
    active_provider: AIProvider


class ErrorResponse(BaseModel):
    error: str
    detail: str
