"""
Revixa — Review Scraper
========================
Google Play Store ve Apple App Store'dan uygulama yorumlarını çeker.

Desteklenen URL formatları:
  Play Store : https://play.google.com/store/apps/details?id=com.instagram.android
  App Store  : https://apps.apple.com/us/app/instagram/id389801252
"""

import re
import time
import logging
import httpx
from urllib.parse import urlparse, parse_qs

from google_play_scraper import app as gplay_app, reviews as gplay_reviews, Sort

from models import Platform, RawReview

logger = logging.getLogger("revixa.scraper")


# ─────────────────────────────────────────────
#  Platform Tespiti
# ─────────────────────────────────────────────

def detect_platform(url: str) -> Platform:
    """URL'ye bakarak platformu otomatik belirle."""
    if "play.google.com" in url:
        return Platform.PLAY
    elif "apps.apple.com" in url:
        return Platform.APPSTORE
    else:
        raise ValueError(
            f"Desteklenmeyen URL: {url}\n"
            "Lütfen Google Play Store veya Apple App Store URL'si girin."
        )


# ─────────────────────────────────────────────
#  Play Store — App ID Çıkarma
# ─────────────────────────────────────────────

def extract_play_app_id(url: str) -> str:
    """
    Play Store URL'sinden app ID çıkar.

    Örnek:
        https://play.google.com/store/apps/details?id=com.instagram.android
        → "com.instagram.android"
    """
    parsed = urlparse(url)
    params = parse_qs(parsed.query)
    app_id = params.get("id", [None])[0]

    if not app_id:
        raise ValueError(
            f"Geçersiz Play Store URL'si: {url}\n"
            "URL'de '?id=...' parametresi bulunamadı."
        )

    return app_id.strip()


# ─────────────────────────────────────────────
#  App Store — App ID ve Ülke Çıkarma
# ─────────────────────────────────────────────

def extract_appstore_info(url: str) -> tuple[str, str, str]:
    """
    App Store URL'sinden app adı, ülke ve ID çıkar.

    Örnek:
        https://apps.apple.com/us/app/instagram/id389801252
        → ("instagram", "us", "389801252")
    """
    parsed = urlparse(url)
    path = parsed.path  # /us/app/instagram/id389801252

    parts = [p for p in path.split("/") if p]
    country = parts[0] if parts else "us"

    app_name = "app"
    for part in parts:
        if part not in [country, "app"] and not part.startswith("id"):
            app_name = part
            break

    app_id = None
    for part in parts:
        match = re.match(r"^id(\d+)$", part)
        if match:
            app_id = match.group(1)
            break

    if not app_id:
        raise ValueError(
            f"Geçersiz App Store URL'si: {url}\n"
            "URL'de 'id...' segmenti bulunamadı."
        )

    return app_name, country, app_id


# ─────────────────────────────────────────────
#  Play Store Scraper
# ─────────────────────────────────────────────

def scrape_play_store(url: str, max_reviews: int = 150) -> tuple[str, list[RawReview]]:
    """
    Google Play Store'dan yorumları çeker.

    Returns:
        (app_name, reviews_list)
    """
    app_id = extract_play_app_id(url)
    logger.info(f"Play Store scraping başlatıldı: {app_id}")

    # Uygulama adını al
    app_name = app_id
    for lang, country in [("tr", "tr"), ("en", "us")]:
        try:
            info = gplay_app(app_id, lang=lang, country=country)
            app_name = info.get("title", app_id)
            break
        except Exception:
            continue

    # gplay_app başarısız olduysa sayfayı doğrudan çekip title'ı al
    if app_name == app_id:
        try:
            import re as _re
            import httpx as _httpx
            _url = f"https://play.google.com/store/apps/details?id={app_id}&hl=tr"
            with _httpx.Client(timeout=10, follow_redirects=True,
                               headers={"User-Agent": "Mozilla/5.0"}) as _client:
                _resp = _client.get(_url)
                _match = _re.search(r'<title>(.+?)\s*[-|].*?</title>', _resp.text, _re.IGNORECASE)
                if _match:
                    app_name = _match.group(1).strip()
        except Exception:
            pass  # Adı bulamazsak app_id ile devam et


    all_reviews: list[RawReview] = []
    seen_contents: set[str] = set()

    # Her dil için pagination ile TÜM yorumları çek
    fetch_configs = [
        {"lang": "tr", "country": "tr"},
        {"lang": "en", "country": "us"},
    ]

    for config in fetch_configs:
        continuation_token = None
        page = 0
        lang_count = 0

        while True:
            # max_reviews=0 ise sınırsız çek, değilse sınırla
            if max_reviews > 0 and len(all_reviews) >= max_reviews:
                break
            try:
                batch_size = 200  # Her seferinde 200 yorum iste
                result, continuation_token = gplay_reviews(
                    app_id,
                    lang=config["lang"],
                    country=config["country"],
                    sort=Sort.MOST_RELEVANT,
                    count=batch_size,
                    continuation_token=continuation_token,
                    filter_score_with=None,
                )

                if not result:
                    break  # Bu dilde başka yorum yok

                added = 0
                for r in result:
                    content = (r.get("content") or "").strip()
                    if not content or content in seen_contents or len(content) < 5:
                        continue
                    seen_contents.add(content)
                    all_reviews.append(RawReview(
                        author=r.get("userName") or "Anonim",
                        rating=float(r.get("score") or 0),
                        content=content,
                        date=str(r.get("at", "")),
                    ))
                    added += 1

                lang_count += added
                page += 1
                logger.info(f"  {config['lang'].upper()} sayfa {page}: {added} yorum eklendi (toplam: {len(all_reviews)})")

                if continuation_token is None:
                    break  # Daha fazla sayfa yok

                time.sleep(0.3)  # Rate limiting

            except Exception as e:
                logger.warning(f"  {config['lang'].upper()} sayfa {page+1} hatası: {e}")
                break

        logger.info(f"  {config['lang'].upper()} toplam: {lang_count} yorum")

    logger.info(f"Toplam Play Store yorumu: {len(all_reviews)}")
    return app_name, all_reviews if max_reviews == 0 else all_reviews[:max_reviews]


# ─────────────────────────────────────────────
#  App Store Scraper (iTunes RSS API)
# ─────────────────────────────────────────────

def scrape_app_store(url: str, max_reviews: int = 150) -> tuple[str, list[RawReview]]:
    """
    Apple App Store'dan yorumları çeker.
    Apple'ın ücretsiz iTunes RSS API'sini kullanır — kütüphane gerektirmez.

    Returns:
        (app_name, reviews_list)
    """
    app_name_slug, country, app_id = extract_appstore_info(url)
    logger.info(f"App Store scraping başlatıldı: {app_name_slug} ({country}) id={app_id}")

    all_reviews: list[RawReview] = []
    seen_contents: set[str] = set()
    app_name = app_name_slug

    # Apple RSS API: maksimum 10 sayfa × 50 = 500 yorum
    pages_needed = min((max_reviews // 50) + 1, 10)
    countries = [country]
    if country != "us":
        countries.append("us")

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    }

    for c in countries:
        if len(all_reviews) >= max_reviews:
            break
        for page in range(1, pages_needed + 1):
            if len(all_reviews) >= max_reviews:
                break
            rss_url = (
                f"https://itunes.apple.com/{c}/rss/customerreviews/"
                f"page={page}/id={app_id}/sortby=mostrecent/json"
            )
            try:
                with httpx.Client(timeout=15, headers=headers) as client:
                    resp = client.get(rss_url)
                    resp.raise_for_status()
                    data = resp.json()

                feed = data.get("feed", {})

                # Uygulama adını al — feed title'dan
                if app_name == app_name_slug:
                    title_obj = feed.get("title", {})
                    feed_title = title_obj.get("label", "") if isinstance(title_obj, dict) else ""
                    # "iTunes Store: Customer Reviews" gibi genel başlıkları atla
                    if feed_title and "iTunes" not in feed_title and "Apple" not in feed_title:
                        app_name = feed_title

                entries = feed.get("entry", [])
                if not entries:
                    break  # Bu sayfada veri yok

                # İlk entry genellikle app info'dur, yorum değil
                for entry in entries:
                    content_obj = entry.get("content", {})
                    content = ""
                    if isinstance(content_obj, dict):
                        content = content_obj.get("label", "").strip()
                    elif isinstance(content_obj, str):
                        content = content_obj.strip()

                    if not content or content in seen_contents or len(content) < 10:
                        continue

                    title_obj = entry.get("title", {})
                    title = title_obj.get("label", "") if isinstance(title_obj, dict) else str(title_obj)

                    rating_obj = entry.get("im:rating", {})
                    rating_str = rating_obj.get("label", "0") if isinstance(rating_obj, dict) else "0"
                    try:
                        rating = float(rating_str)
                    except ValueError:
                        rating = 0.0

                    author_obj = entry.get("author", {})
                    author_name_obj = author_obj.get("name", {}) if isinstance(author_obj, dict) else {}
                    author = author_name_obj.get("label", "Anonim") if isinstance(author_name_obj, dict) else "Anonim"

                    date_obj = entry.get("updated", {})
                    date = date_obj.get("label", "") if isinstance(date_obj, dict) else ""

                    # Title'ı içeriğe ekle (daha zengin analiz için)
                    full_content = f"{title}: {content}" if title and title != content else content
                    seen_contents.add(content)

                    all_reviews.append(RawReview(
                        author=author,
                        rating=rating,
                        content=full_content,
                        date=date,
                    ))

                logger.info(f"  {c.upper()} sayfa {page}: {len(entries)} yorum çekildi")
                time.sleep(0.3)

            except httpx.HTTPStatusError as e:
                logger.warning(f"  {c.upper()} sayfa {page} HTTP hatası: {e.response.status_code}")
                break
            except Exception as e:
                logger.warning(f"  {c.upper()} sayfa {page} hatası: {e}")
                break

    logger.info(f"Toplam App Store yorumu: {len(all_reviews)}")
    return app_name, all_reviews[:max_reviews]


# ─────────────────────────────────────────────
#  Ana Fonksiyon — Otomatik Platform Tespiti
# ─────────────────────────────────────────────

def scrape_reviews(
    url: str,
    platform: Platform = Platform.AUTO,
    max_reviews: int = 150,
) -> tuple[str, Platform, list[RawReview]]:
    """
    URL'ye göre uygun scraper'ı seçer ve yorumları döner.

    Returns:
        (app_name, detected_platform, reviews)

    Raises:
        ValueError: Geçersiz URL veya desteklenmeyen platform
        RuntimeError: Scraping başarısız
    """
    if platform == Platform.AUTO:
        platform = detect_platform(url)

    logger.info(f"Scraping → Platform: {platform.value} | URL: {url}")

    if platform == Platform.PLAY:
        app_name, reviews = scrape_play_store(url, max_reviews)
    elif platform == Platform.APPSTORE:
        app_name, reviews = scrape_app_store(url, max_reviews)
    else:
        raise ValueError(f"Bilinmeyen platform: {platform}")

    if not reviews:
        raise RuntimeError(
            "Hiç yorum çekilemedi. URL'yi kontrol edin veya daha sonra tekrar deneyin."
        )

    logger.info(f"✅ Scraping tamamlandı: '{app_name}' — {len(reviews)} yorum")
    return app_name, platform, reviews
