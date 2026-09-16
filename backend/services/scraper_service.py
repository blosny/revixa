"""
Revixa — Scraper Service Layer
================================
Google Play Store ve Apple App Store scraping, paralel async veri toplama,
metrik harmanlama ve coğrafi tekleştirme servis katmanı.
"""

import re
import random
import logging
import asyncio
from typing import Optional
from collections import Counter
from urllib.parse import urlparse, parse_qs, unquote
import httpx

from google_play_scraper import app as gplay_app, reviews as gplay_reviews, Sort

from models import (
    Platform, RawReview, AppMetadata, RatingDistribution,
    CountryDistribution, KeywordCount
)

logger = logging.getLogger("revixa.services.scraper")

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
]

SUPPORTED_COUNTRIES = [
    {"code": "TR", "lang": "tr", "country": "tr"},
    {"code": "US", "lang": "en", "country": "us"},
    {"code": "DE", "lang": "de", "country": "de"},
    {"code": "GB", "lang": "en", "country": "gb"},
    {"code": "FR", "lang": "fr", "country": "fr"},
    {"code": "BR", "lang": "pt", "country": "br"},
    {"code": "IN", "lang": "en", "country": "in"},
]


def get_random_headers() -> dict:
    return ScraperService.get_random_headers()


def detect_platform(url: str) -> Platform:
    return ScraperService.detect_platform(url)


def extract_play_app_id(url: str) -> str:
    return ScraperService.extract_play_app_id(url)


def extract_appstore_info(url: str) -> tuple[str, str, str]:
    return ScraperService.extract_appstore_info(url)


def fetch_play_metadata(app_id: str) -> tuple[AppMetadata, RatingDistribution]:
    return ScraperService.fetch_play_metadata(app_id)


async def scrape_play_store_async(url: str, max_reviews: int = 0) -> tuple[AppMetadata, RatingDistribution, list[RawReview]]:
    return await ScraperService.scrape_play_store_async(url, max_reviews)


async def scrape_app_store_async(url: str, max_reviews: int = 0) -> tuple[AppMetadata, RatingDistribution, list[RawReview]]:
    return await ScraperService.scrape_app_store_async(url, max_reviews)


def calculate_market_statistics(reviews: list[RawReview]) -> tuple[CountryDistribution, int, list[KeywordCount]]:
    return ScraperService.calculate_market_statistics(reviews)


async def scrape_reviews_async(
    url: Optional[str] = None,
    play_url: Optional[str] = None,
    appstore_url: Optional[str] = None,
    platform: Platform = Platform.AUTO,
    max_reviews: int = 0,
) -> tuple[AppMetadata, Platform, RatingDistribution, CountryDistribution, int, list[KeywordCount], list[RawReview]]:
    return await ScraperService.scrape_reviews_async(url, play_url, appstore_url, platform, max_reviews)


class ScraperService:
    """Mobil uygulama mağazaları için modüler async scraper servisi."""

    @staticmethod
    def get_random_headers() -> dict:
        return {
            "User-Agent": random.choice(USER_AGENTS),
            "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        }

    @staticmethod
    def detect_platform(url: str) -> Platform:
        if "play.google.com" in url:
            return Platform.PLAY
        elif "apps.apple.com" in url:
            return Platform.APPSTORE
        else:
            raise ValueError(f"Geçersiz mağaza adresi: {url}")

    @staticmethod
    def extract_play_app_id(url: str) -> str:
        parsed = urlparse(url)
        if parsed.hostname != "play.google.com":
            raise ValueError("Sadece resmi play.google.com bağlantılarına izin verilmektedir.")
        params = parse_qs(parsed.query)
        app_id = params.get("id", [None])[0]
        if not app_id or not re.match(r"^[a-zA-Z0-9_\.]+$", app_id):
            raise ValueError("Geçerli bir Google Play paket kimliği (id) bulunamadı.")
        return app_id.strip()

    @staticmethod
    def extract_appstore_info(url: str) -> tuple[str, str, str]:
        parsed = urlparse(url)
        if parsed.hostname != "apps.apple.com":
            raise ValueError("Sadece resmi apps.apple.com bağlantılarına izin verilmektedir.")
        parts = [p for p in parsed.path.split("/") if p]
        country = parts[0] if parts and len(parts[0]) == 2 else "us"
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
            raise ValueError("Geçerli bir Apple App Store ID kimliği (id...) bulunamadı.")
        return app_name, country, app_id

    @classmethod
    def fetch_play_metadata(cls, app_id: str) -> tuple[AppMetadata, RatingDistribution]:
        try:
            info = gplay_app(app_id, lang="tr", country="tr")
        except Exception:
            try:
                info = gplay_app(app_id, lang="en", country="us")
            except Exception as e:
                logger.error(f"Play Store metadata çekilemedi [{app_id}]: {e}")
                raise ValueError(f"Uygulama Google Play Store'da bulunamadı veya erişilemiyor [{app_id}].")

        histogram = info.get("histogram", [0, 0, 0, 0, 0])
        total_ratings = info.get("ratings") or sum(histogram) or 1

        meta = AppMetadata(
            title=info.get("title") or app_id,
            developer=info.get("developer") or "Bilinmiyor",
            category=info.get("genre") or "Genel",
            average_rating=round(float(info.get("score") or 0.0), 1),
            total_ratings=total_ratings,
            version=info.get("version") or "1.0.0",
            updated_date=str(info.get("updated") or "—"),
            price="Ücretsiz" if info.get("free") else f"{info.get('price', 0)} {info.get('currency', 'TRY')}",
            contains_ads=bool(info.get("containsAds", False)),
        )

        rating_dist = RatingDistribution(
            star_1=histogram[0] if len(histogram) > 0 else 0,
            star_2=histogram[1] if len(histogram) > 1 else 0,
            star_3=histogram[2] if len(histogram) > 2 else 0,
            star_4=histogram[3] if len(histogram) > 3 else 0,
            star_5=histogram[4] if len(histogram) > 4 else 0,
        )

        return meta, rating_dist

    @classmethod
    def _fetch_play_country_reviews(cls, app_id: str, c_info: dict, max_per_country: int = 100) -> list[RawReview]:
        try:
            result, _ = gplay_reviews(
                app_id,
                lang=c_info["lang"],
                country=c_info["country"],
                sort=Sort.NEWEST,
                count=max_per_country,
            )
            reviews = []
            for r in result:
                content = r.get("content", "").strip()
                if content:
                    reviews.append(
                        RawReview(
                            author=r.get("userName", "Anonim"),
                            rating=float(r.get("score", 0)),
                            content=content,
                            date=str(r.get("at", "")),
                            country=c_info["code"],
                            platform=Platform.PLAY,
                        )
                    )
            return reviews
        except Exception as e:
            logger.warning(f"Play Store yorum çekme hatası [{c_info['code']}]: {e}")
            return []

    @classmethod
    async def scrape_play_store_async(cls, url: str, max_reviews: int = 0) -> tuple[AppMetadata, RatingDistribution, list[RawReview]]:
        app_id = cls.extract_play_app_id(url)
        logger.info(f"Parallel Async Play Store scraping başlatıldı: {app_id}")

        meta, rating_dist = cls.fetch_play_metadata(app_id)

        loop = asyncio.get_running_loop()
        tasks = [
            loop.run_in_executor(None, cls._fetch_play_country_reviews, app_id, config, 100)
            for config in SUPPORTED_COUNTRIES
        ]
        results = await asyncio.gather(*tasks)

        all_reviews: list[RawReview] = []
        seen_keys: set[tuple[str, str]] = set()

        for country_revs in results:
            for r in country_revs:
                dedup_key = (r.country, r.content)
                if dedup_key not in seen_keys:
                    seen_keys.add(dedup_key)
                    all_reviews.append(r)

        if max_reviews > 0:
            all_reviews = all_reviews[:max_reviews]

        return meta, rating_dist, all_reviews

    @classmethod
    async def scrape_app_store_async(cls, url: str, max_reviews: int = 0) -> tuple[AppMetadata, RatingDistribution, list[RawReview]]:
        app_name_slug, country, app_id = cls.extract_appstore_info(url)
        logger.info(f"Parallel Async App Store scraping başlatıldı: {app_name_slug} id={app_id}")

        all_reviews: list[RawReview] = []
        seen_keys: set[tuple[str, str]] = set()

        async with httpx.AsyncClient(timeout=10, headers=cls.get_random_headers()) as client:
            async def fetch_rss(c_info, page):
                c_code = c_info["country"]
                rss_url = f"https://itunes.apple.com/{c_code}/rss/customerreviews/page={page}/id={app_id}/sortby=mostrecent/json"
                try:
                    resp = await client.get(rss_url, headers=cls.get_random_headers())
                    if resp.status_code != 200:
                        return []
                    data = resp.json()
                    entries = data.get("feed", {}).get("entry", [])
                    revs = []
                    for entry in entries:
                        if not isinstance(entry, dict):
                            continue
                        content = entry.get("content", {}).get("label", "")
                        author = entry.get("author", {}).get("name", {}).get("label", "Anonim")
                        rating_val = float(entry.get("im:rating", {}).get("label", 5.0))
                        if content:
                            revs.append(
                                RawReview(
                                    author=author,
                                    rating=rating_val,
                                    content=content,
                                    country=c_code,
                                    platform=Platform.APPSTORE,
                                )
                            )
                    return revs
                except Exception:
                    return []

            tasks = []
            for c_info in SUPPORTED_COUNTRIES[:4]:
                for page in range(1, 4):
                    tasks.append(fetch_rss(c_info, page))

            results = await asyncio.gather(*tasks)
            for page_revs in results:
                for r in page_revs:
                    dedup_key = (r.country, r.content)
                    if dedup_key not in seen_keys:
                        seen_keys.add(dedup_key)
                        all_reviews.append(r)

        clean_title = unquote(app_name_slug).replace("-", " ").title()

        star_counts = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
        total_score = 0.0
        valid_ratings_count = 0

        for r in all_reviews:
            star = int(round(r.rating))
            if 1 <= star <= 5:
                star_counts[star] += 1
                total_score += r.rating
                valid_ratings_count += 1

        avg_rating = round(total_score / valid_ratings_count, 1) if valid_ratings_count > 0 else 0.0

        meta = AppMetadata(
            title=clean_title,
            developer="App Store Developer",
            category="iOS App",
            average_rating=avg_rating,
            total_ratings=len(all_reviews),
        )

        rating_dist = RatingDistribution(
            star_1=star_counts[1],
            star_2=star_counts[2],
            star_3=star_counts[3],
            star_4=star_counts[4],
            star_5=star_counts[5],
        )

        if max_reviews > 0:
            all_reviews = all_reviews[:max_reviews]

        return meta, rating_dist, all_reviews

    @classmethod
    def calculate_market_statistics(cls, reviews: list[RawReview]) -> tuple[CountryDistribution, int, list[KeywordCount]]:
        if not reviews:
            return CountryDistribution(), 0, []

        country_counts: dict[str, int] = Counter(r.country for r in reviews)
        total = len(reviews)
        country_pcts: dict[str, float] = {
            c: round((cnt / total) * 100, 1) for c, cnt in country_counts.items()
        }
        country_dist = CountryDistribution(counts=country_counts, percentages=country_pcts)

        avg_len = int(sum(len(r.content) for r in reviews) / total)

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

    @classmethod
    async def scrape_reviews_async(
        cls,
        url: Optional[str] = None,
        play_url: Optional[str] = None,
        appstore_url: Optional[str] = None,
        platform: Platform = Platform.AUTO,
        max_reviews: int = 0,
    ) -> tuple[AppMetadata, Platform, RatingDistribution, CountryDistribution, int, list[KeywordCount], list[RawReview]]:

        target_play_url = play_url or (url if url and "play.google.com" in url else None)
        target_appstore_url = appstore_url or (url if url and "apps.apple.com" in url else None)

        if not target_play_url and not target_appstore_url and url:
            if "play.google.com" in url:
                target_play_url = url
            elif "apps.apple.com" in url:
                target_appstore_url = url

        if target_play_url and target_appstore_url:
            detected_platform = Platform.BOTH
            m1, r1, revs1 = await cls.scrape_play_store_async(target_play_url, max_reviews // 2 if max_reviews else 0)
            m2, r2, revs2 = await cls.scrape_app_store_async(target_appstore_url, max_reviews // 2 if max_reviews else 0)

            total_ratings = m1.total_ratings + m2.total_ratings
            if total_ratings > 0:
                weighted_avg = round(
                    ((m1.average_rating * m1.total_ratings) + (m2.average_rating * m2.total_ratings)) / total_ratings,
                    1,
                )
            else:
                weighted_avg = round((m1.average_rating + m2.average_rating) / 2, 1)

            meta = AppMetadata(
                title=f"{m1.title} (Play Store + App Store)",
                developer=f"{m1.developer} / {m2.developer}",
                category=f"{m1.category} & {m2.category}",
                average_rating=weighted_avg,
                total_ratings=total_ratings,
                version=m1.version or m2.version,
                price=m1.price or m2.price,
            )

            rating_dist = RatingDistribution(
                star_1=r1.star_1 + r2.star_1,
                star_2=r1.star_2 + r2.star_2,
                star_3=r1.star_3 + r2.star_3,
                star_4=r1.star_4 + r2.star_4,
                star_5=r1.star_5 + r2.star_5,
            )

            all_reviews = revs1 + revs2
        elif target_play_url:
            detected_platform = Platform.PLAY
            meta, rating_dist, all_reviews = await cls.scrape_play_store_async(target_play_url, max_reviews)
        elif target_appstore_url:
            detected_platform = Platform.APPSTORE
            meta, rating_dist, all_reviews = await cls.scrape_app_store_async(target_appstore_url, max_reviews)
        else:
            raise ValueError("Lütfen geçerli bir Google Play Store veya Apple App Store adresi girin.")

        country_dist, avg_len, keywords = cls.calculate_market_statistics(all_reviews)

        return meta, detected_platform, rating_dist, country_dist, avg_len, keywords, all_reviews
