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

from models import (
    AnalysisRequest, AnalysisResult, AIStatus, ErrorResponse,
    UserCreate, UserResponse, Token, SavedAppCreate, SavedAppResponse
)
from database import init_db, get_db, UserDB, SavedAppDB
from auth import hash_password, verify_password, create_access_token, get_current_user
from scraper import scrape_reviews_async
from analyzer import get_router
from cache import get_cached_analysis, save_cached_analysis, clear_cache_db
from fastapi import Depends
from sqlalchemy.orm import Session

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


@app.on_event("startup")
def on_startup():
    init_db()


@app.get("/health", tags=["System"])
async def health_check():
    return {"status": "ok", "service": "Revixa API v2.0"}


# ─────────────────────────────────────────────
#  Auth Endpoints (Kullanıcı Kayıt & Giriş)
# ─────────────────────────────────────────────

@app.post("/auth/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED, tags=["Auth"])
def register(user_in: UserCreate, db: Session = Depends(get_db)):
    """Yeni kullanıcı kaydı oluşturur."""
    existing_user = db.query(UserDB).filter(UserDB.email == user_in.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Bu e-posta adresi ile zaten kayıtlı bir hesap var."
        )
    
    hashed_pwd = hash_password(user_in.password)
    user = UserDB(email=user_in.email, password_hash=hashed_pwd)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@app.post("/auth/login", response_model=Token, tags=["Auth"])
def login(user_in: UserCreate, db: Session = Depends(get_db)):
    """Kullanıcı girişi yapar ve JWT Access Token döner."""
    user = db.query(UserDB).filter(UserDB.email == user_in.email).first()
    if not user or not verify_password(user_in.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="E-posta adresi veya parola hatalı."
        )
    
    access_token = create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/auth/me", response_model=UserResponse, tags=["Auth"])
def get_me(current_user: UserDB = Depends(get_current_user)):
    """Aktif giriş yapan kullanıcının bilgilerini döner."""
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Giriş yapmanız gerekmektedir."
        )
    return current_user


# ─────────────────────────────────────────────
#  Saved Apps Endpoints (Kullanıcı Uygulamaları)
# ─────────────────────────────────────────────

@app.post("/user/apps", response_model=SavedAppResponse, status_code=status.HTTP_201_CREATED, tags=["Saved Apps"])
def create_saved_app(app_in: SavedAppCreate, current_user: UserDB = Depends(get_current_user), db: Session = Depends(get_db)):
    """Giriş yapmış kullanıcının paneline yeni uygulama kaydeder."""
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Uygulama kaydetmek için giriş yapmanız gerekmektedir."
        )
    
    if app_in.play_url:
        validate_input_url(app_in.play_url)
    if app_in.appstore_url:
        validate_input_url(app_in.appstore_url)
        
    saved_app = SavedAppDB(
        user_id=current_user.id,
        title=app_in.title,
        play_url=app_in.play_url,
        appstore_url=app_in.appstore_url
    )
    db.add(saved_app)
    db.commit()
    db.refresh(saved_app)
    return saved_app


@app.get("/user/apps", response_model=list[SavedAppResponse], tags=["Saved Apps"])
def get_user_apps(current_user: UserDB = Depends(get_current_user), db: Session = Depends(get_db)):
    """Giriş yapmış kullanıcının kaydettiği tüm uygulamaları getirir."""
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Giriş yapmanız gerekmektedir."
        )
    return db.query(SavedAppDB).filter(SavedAppDB.user_id == current_user.id).all()


@app.delete("/user/apps/{app_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Saved Apps"])
def delete_saved_app(app_id: int, current_user: UserDB = Depends(get_current_user), db: Session = Depends(get_db)):
    """Kaydedilmiş bir uygulamayı siler."""
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Giriş yapmanız gerekmektedir."
        )
    
    app_obj = db.query(SavedAppDB).filter(SavedAppDB.id == app_id, SavedAppDB.user_id == current_user.id).first()
    if not app_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Silinecek uygulama bulunamadı veya bu uygulamaya erişim yetkiniz yok."
        )
    
    db.delete(app_obj)
    db.commit()
    return None


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
            custom_prompt_extension=body.custom_prompt_extension,
            language=body.language
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
