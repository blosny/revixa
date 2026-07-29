"""
Revixa — FastAPI Backend Application
=====================================
REST API endpoints:
  - POST /analyze   : URL'leri alıp review çeker, pazar metriklerini ve AI analizini döner
  - GET  /ai-status : AI durumunu döner (Gemini & Ollama)
  - GET  /health    : Sistem sağlık kontrolü
"""

import sys
import os
import logging
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
load_dotenv()

from models import AnalysisRequest, AnalysisResult, AIStatus, ErrorResponse
from scraper import scrape_reviews
from analyzer import get_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("revixa.main")

app = FastAPI(
    title="Revixa API",
    description="Mobil Uygulama Yorum Analizi ve Pazar İçgörüsü Otomasyonu",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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


@app.post(
    "/analyze",
    response_model=AnalysisResult,
    responses={
        400: {"model": ErrorResponse, "description": "Geçersiz istek veya URL"},
        500: {"model": ErrorResponse, "description": "Scraping veya AI analizi hatası"},
    },
    tags=["Analysis"]
)
async def analyze_app(request: AnalysisRequest):
    logger.info(f"YENİ İSTEK → URL: {request.url} | Play: {request.play_url} | AppStore: {request.appstore_url} | Max: {request.max_reviews}")

    # 1. Review & Market Statistics Scraping
    try:
        meta, detected_platform, rating_dist, country_dist, avg_len, keywords, reviews = scrape_reviews(
            url=request.url,
            play_url=request.play_url,
            appstore_url=request.appstore_url,
            platform=request.platform,
            max_reviews=request.max_reviews
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

    # 2. AI Analysis
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
        return result

    except Exception as e:
        logger.error(f"AI Analiz Hatası: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Yorumlar analiz edilirken hata oluştu: {str(e)}"
        )
