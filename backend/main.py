"""
Revixa — FastAPI Backend Application
=====================================
REST API endpoints:
  - POST   /analyze    : URL'leri alıp review çeker, pazar metriklerini ve AI analizini döner (Cache + Rate Limited)
  - DELETE /cache      : Önbellek veritabanını temizler
  - GET    /ai-status  : AI durumunu döner (Gemini & Ollama)
  - GET    /health     : Sistem sağlık kontrolü
"""

import sys
import os
import re
import logging
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
load_dotenv()

from models import AnalysisRequest, AnalysisResult, AIStatus, ErrorResponse
from scraper import scrape_reviews_async
from analyzer import get_router
from cache import get_cached_analysis, save_cached_analysis, clear_cache_db

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("revixa.main")

# Rate Limiter setup (IP başına dakikada maksimum 10 analiz)
limiter = Limiter(key_func=get_remote_address)

app = FastAPI(
    title="Revixa API",
    description="Mobil Uygulama Yorum Analizi ve Pazar İçgörüsü Otomasyonu",
    version="2.0.0",
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def validate_input_url(url: str):
    """SSRF ve Zararlı URL Enjeksiyon Koruması."""
    if not url:
        return
    url_str = str(url).strip()
    if not (url_str.startswith("https://play.google.com") or url_str.startswith("https://apps.apple.com")):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Güvenlik Engeli: Sadece resmi 'https://play.google.com' veya 'https://apps.apple.com' adreslerine izin verilmektedir."
        )


@app.get("/health", tags=["System"])
async def health_check():
    return {"status": "ok", "service": "Revixa API v2.0"}


@app.get("/ai-status", response_model=AIStatus, tags=["AI"])
async def get_ai_status():
    try:
        router = get_router()
        return router.get_status()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AI durumu alınamadı: {str(e)}"
        )


@app.delete("/cache", tags=["System"])
async def clear_cache():
    """Önbellek veritabanını temizler."""
    deleted_count = clear_cache_db()
    return {"message": "Önbellek başarıyla temizlendi", "deleted_entries": deleted_count}


@app.post(
    "/analyze",
    response_model=AnalysisResult,
    responses={
        400: {"model": ErrorResponse, "description": "Geçersiz istek veya URL"},
        429: {"model": ErrorResponse, "description": "Çok fazla istek atıldı"},
        500: {"model": ErrorResponse, "description": "Scraping veya AI analizi hatası"},
    },
    tags=["Analysis"]
)
@limiter.limit("10/minute")
async def analyze_app(request: Request, body: AnalysisRequest):
    # 1. SSRF & URL Validation
    validate_input_url(body.url)
    validate_input_url(body.play_url)
    validate_input_url(body.appstore_url)

    cache_key = f"{body.play_url or ''}_{body.appstore_url or ''}_{body.url or ''}_{body.max_reviews}"
    
    # 2. Check Cache
    cached_data = get_cached_analysis(cache_key)
    if cached_data:
        return AnalysisResult(**cached_data)

    logger.info(f"YENİ İSTEK → URL: {body.url} | Play: {body.play_url} | AppStore: {body.appstore_url} | Max: {body.max_reviews}")

    # 3. Async Scraping
    try:
        meta, detected_platform, rating_dist, country_dist, avg_len, keywords, reviews = await scrape_reviews_async(
            url=body.url,
            play_url=body.play_url,
            appstore_url=body.appstore_url,
            platform=body.platform,
            max_reviews=body.max_reviews
        )
    except ValueError as e:
        logger.warning(f"URL Doğrulama Hatası: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Scraping Hatası: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Yorumlar ve metrikler çekilirken hata oluştu: {str(e)}"
        )

    # 4. AI Analysis
    try:
        router = get_router()
        result = router.analyze(
            reviews=reviews,
            app_name=meta.title,
            platform=detected_platform,
            metadata=meta,
            rating_dist=rating_dist,
            country_dist=country_dist,
            avg_len=avg_len,
            keywords=keywords,
        )
        
        # Önbelleğe kaydet
        save_cached_analysis(cache_key, result.model_dump())
        return result

    except Exception as e:
        logger.error(f"AI Analiz Hatası: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Yorumlar analiz edilirken hata oluştu: {str(e)}"
        )
