"""
Revixa — Multi-Country Scraper & Market Statistics Engine
=========================================================
Google Play Store ve Apple App Store'dan yorumları ve pazar metriklerini çeker.
Çoklu Ülke (TR, US, DE, GB, FR, BR, IN) desteği sunar.
"""

import re
import time
import logging
import asyncio
from typing import Optional
from collections import Counter
from urllib.parse import urlparse, parse_qs
import httpx

from google_play_scraper import app as gplay_app, reviews as gplay_reviews, Sort

from models import (
    Platform, RawReview, AppMetadata, RatingDistribution,
    CountryDistribution, KeywordCount
)

logger = logging.getLogger("revixa.scraper")

SUPPORTED_COUNTRIES = [
    {"code": "TR", "lang": "tr", "country": "tr"},
    {"code": "US", "lang": "en", "country": "us"},
    {"code": "DE", "lang": "de", "country": "de"},
    {"code": "GB", "lang": "en", "country": "gb"},
    {"code": "FR", "lang": "fr", "country": "fr"},
    {"code": "BR", "lang": "pt", "country": "br"},
    {"code": "IN", "lang": "en", "country": "in"},
]


def detect_platform(url: str) -> Platform:
    if "play.google.com" in url:
        return Platform.PLAY
    elif "apps.apple.com" in url:
        return Platform.APPSTORE
    else:
        raise ValueError(f"Geçersiz URL: {url}")


def extract_play_app_id(url: str) -> str:
    parsed = urlparse(url)
    params = parse_qs(parsed.query)
    app_id = params.get("id", [None])[0]
    if not app_id:
        raise ValueError(f"Play Store URL'sinde '?id=...' bulunamadı: {url}")
    return app_id.strip()


def extract_appstore_info(url: str) -> tuple[str, str, str]:
    parsed = urlparse(url)
    parts = [p for p in parsed.path.split("/") if p]
    country = parts[0] if parts else "us"
    app_name = "App"
    for p in parts:
        if p not in [country, "app"] and not p.startswith("id"):
            app_name = p
            break
    app_id = None
    for p in parts:
        m = re.match(r"^id(\d+)$", p)
        if m:
            app_id = m.group(1)
            break
    if not app_id:
        raise ValueError(f"App Store URL'sinde 'id...' bulunamadı: {url}")
    return app_name, country, app_id


def fetch_play_metadata(app_id: str) -> tuple[AppMetadata, RatingDistribution]:
    """Play Store uygulama detay verilerini ve yıldız dağılımını alır."""
    try:
        info = gplay_app(app_id, lang="tr", country="tr")
    except Exception:
        try:
            info = gplay_app(app_id, lang="en", country="us")
        except Exception:
            info = {}

    title = info.get("title") or app_id
    developer = info.get("developer") or "Bilinmiyor"
    category = info.get("genre") or "Genel"
    score = float(info.get("score") or 0.0)
    ratings = int(info.get("ratings") or 0)
    version = info.get("version") or "v1.0"
    updated = str(info.get("updated") or "—")
    price = "Ücretsiz" if info.get("free", True) else f"{info.get('price', 0)} TL"
    offers_inapp = bool(info.get("offersIAP", False))

    meta = AppMetadata(
        title=title,
        developer=developer,
        category=category,
        average_rating=round(score, 1),
        total_ratings=ratings,
        version=version,
        updated_date=updated,
        price=price,
        contains_ads=offers_inapp,
    )

    # Yıldız dağılımı tahmini (gplay-scraper histogram dönerse)
    histogram = info.get("histogram") or [0, 0, 0, 0, 0]
    rating_dist = RatingDistribution(
        star_1=histogram[0] if len(histogram) > 0 else 0,
        star_2=histogram[1] if len(histogram) > 1 else 0,
        star_3=histogram[2] if len(histogram) > 2 else 0,
        star_4=histogram[3] if len(histogram) > 3 else 0,
        star_5=histogram[4] if len(histogram) > 4 else 0,
    )

    return meta, rating_dist


def scrape_play_store(url: str, max_reviews: int = 0) -> tuple[AppMetadata, RatingDistribution, list[RawReview]]:
    app_id = extract_play_app_id(url)
    logger.info(f"Play Store scraping başlatıldı: {app_id}")

    meta, rating_dist = fetch_play_metadata(app_id)
    all_reviews: list[RawReview] = []
    seen_contents: set[str] = set()

    for config in SUPPORTED_COUNTRIES:
        if max_reviews > 0 and len(all_reviews) >= max_reviews:
            break

        continuation_token = None
        for sort_type in [Sort.MOST_RELEVANT, Sort.NEWEST]:
            if max_reviews > 0 and len(all_reviews) >= max_reviews:
                break
            try:
                result, continuation_token = gplay_reviews(
                    app_id,
                    lang=config["lang"],
                    country=config["country"],
                    sort=sort_type,
                    count=100,
                    continuation_token=continuation_token,
                )
                if not result:
                    continue

                for r in result:
                    content = (r.get("content") or "").strip()
                    if not content or content in seen_contents or len(content) < 3:
                        continue
                    seen_contents.add(content)
                    all_reviews.append(RawReview(
                        author=r.get("userName") or "Anonim",
                        rating=float(r.get("score") or 0),
                        content=content,
                        date=str(r.get("at", "")),
                        country=config["code"],
                        platform=Platform.PLAY,
                    ))
            except Exception:
                continue

    return meta, rating_dist, all_reviews if max_reviews == 0 else all_reviews[:max_reviews]


def scrape_app_store(url: str, max_reviews: int = 0) -> tuple[AppMetadata, RatingDistribution, list[RawReview]]:
    app_name_slug, country, app_id = extract_appstore_info(url)
    logger.info(f"App Store scraping başlatıldı: {app_name_slug} ({country}) id={app_id}")

    all_reviews: list[RawReview] = []
    seen_contents: set[str] = set()
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

    # RSS API ile yorum çekme
    for c_info in SUPPORTED_COUNTRIES[:3]:  # TR, US, DE
        c_code = c_info["country"]
        for page in range(1, 6):
            if max_reviews > 0 and len(all_reviews) >= max_reviews:
                break
            rss_url = f"https://itunes.apple.com/{c_code}/rss/customerreviews/page={page}/id={app_id}/sortby=mostrecent/json"
            try:
                with httpx.Client(timeout=10, headers=headers) as client:
                    resp = client.get(rss_url)
                    if resp.status_code != 200:
                        break
                    data = resp.json()

                feed = data.get("feed", {})
                entries = feed.get("entry", [])
                if not entries:
                    break

                for entry in entries:
                    content_obj = entry.get("content", {})
                    content = content_obj.get("label", "").strip() if isinstance(content_obj, dict) else str(content_obj).strip()
                    if not content or content in seen_contents or len(content) < 3:
                        continue
                    seen_contents.add(content)

                    rating_obj = entry.get("im:rating", {})
                    rating_str = rating_obj.get("label", "0") if isinstance(rating_obj, dict) else "0"

                    all_reviews.append(RawReview(
                        author="App Store Kullanıcısı",
                        rating=float(rating_str),
                        content=content,
                        date="",
                        country=c_code.upper(),
                        platform=Platform.APPSTORE,
                    ))
            except Exception:
                break

    meta = AppMetadata(
        title=app_name_slug.replace("-", " ").title(),
        developer="App Store Developer",
        category="iOS App",
        average_rating=4.2,
        total_ratings=len(all_reviews),
    )
    rating_dist = RatingDistribution(star_5=len(all_reviews))

    return meta, rating_dist, all_reviews if max_reviews == 0 else all_reviews[:max_reviews]


def calculate_market_statistics(reviews: list[RawReview]) -> tuple[CountryDistribution, int, list[KeywordCount]]:
    """Ülke dağılımı, ortalama karakter uzunluğu ve sık geçen anahtar kelimeleri hesaplar."""
    if not reviews:
        return CountryDistribution(), 0, []

    # Ülke dağılımı
    country_counts: dict[str, int] = Counter(r.country for r in reviews)
    total = len(reviews)
    country_pcts: dict[str, float] = {
        c: round((cnt / total) * 100, 1) for c, cnt in country_counts.items()
    }
    country_dist = CountryDistribution(counts=country_counts, percentages=country_pcts)

    # Ortalama yorum uzunluğu (karakter)
    avg_len = int(sum(len(r.content) for r in reviews) / total)

    # En çok tekrarlanan anahtar kelimeler
    stopwords = {"ve", "bu", "bir", "cok", "çok", "için", "icin", "de", "da", "ama", "fakat", "gibi", "ile", "daha", "her", "ben", "the", "and", "is", "it", "to", "in", "app", "uygulama"}
    words = []
    for r in reviews:
        clean_words = re.findall(r"\w+", r.content.lower())
        for w in clean_words:
            if len(w) > 3 and w not in stopwords:
                words.append(w)

    top_words = Counter(words).most_common(8)
    keywords = [KeywordCount(keyword=kw, count=cnt) for kw, cnt in top_words]

    return country_dist, avg_len, keywords


def scrape_reviews(
    url: Optional[str] = None,
    play_url: Optional[str] = None,
    appstore_url: Optional[str] = None,
    platform: Platform = Platform.AUTO,
    max_reviews: int = 0,
) -> tuple[AppMetadata, Platform, RatingDistribution, CountryDistribution, int, list[KeywordCount], list[RawReview]]:
    
    all_reviews: list[RawReview] = []
    meta = AppMetadata(title="Uygulama Analizi")
    rating_dist = RatingDistribution()
    detected_platform = Platform.PLAY

    # Tekil URL mi Çift URL mi?
    target_play_url = play_url or (url if url and "play.google.com" in url else None)
    target_appstore_url = appstore_url or (url if url and "apps.apple.com" in url else None)

    if not target_play_url and not target_appstore_url and url:
        if "play.google.com" in url:
            target_play_url = url
        elif "apps.apple.com" in url:
            target_appstore_url = url

    if target_play_url and target_appstore_url:
        detected_platform = Platform.BOTH
        m1, r1, revs1 = scrape_play_store(target_play_url, max_reviews // 2 if max_reviews else 0)
        m2, r2, revs2 = scrape_app_store(target_appstore_url, max_reviews // 2 if max_reviews else 0)
        meta = m1
        meta.title = f"{m1.title} (Play Store + App Store)"
        all_reviews = revs1 + revs2
    elif target_play_url:
        detected_platform = Platform.PLAY
        meta, rating_dist, all_reviews = scrape_play_store(target_play_url, max_reviews)
    elif target_appstore_url:
        detected_platform = Platform.APPSTORE
        meta, rating_dist, all_reviews = scrape_app_store(target_appstore_url, max_reviews)
    else:
        raise ValueError("Lütfen geçerli bir Google Play Store veya App Store URL'si girin.")

    if not all_reviews:
        raise RuntimeError("Yorumlar çekilemedi. Bağlantıyı kontrol edin.")

    country_dist, avg_len, keywords = calculate_market_statistics(all_reviews)

    return meta, detected_platform, rating_dist, country_dist, avg_len, keywords, all_reviews
