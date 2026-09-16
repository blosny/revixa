"""
Revixa — AI Analyzer & Enriched Report Generator (Facade)
==========================================================
Tüm AI analiz ve router mantığı `services.ai_service` katmanına aktarılmıştır.
Geriye dönük uyumluluk için AIRouter ve ilgili sınıflar dışa aktarılır.
"""

from services.ai_service import (
    AIService as AIRouter,
    AIService,
    GeminiAnalyzer,
    OllamaAnalyzer,
    calculate_sentiment_distribution,
    ANALYSIS_PROMPT,
    get_router,
)
