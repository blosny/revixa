"""
Revixa — Fast & Safe Multi-Country Async Scraper Engine (Facade)
===================================================================
Tüm scraping fonksiyonları `services.scraper_service.ScraperService` katmanına aktarılmıştır.
Geriye dönük uyumluluk için modül seviyesi fonksiyonlar dışa aktarılır.
"""

from services.scraper_service import (
    ScraperService,
    USER_AGENTS,
    SUPPORTED_COUNTRIES,
    get_random_headers,
    detect_platform,
    extract_play_app_id,
    extract_appstore_info,
    fetch_play_metadata,
    scrape_play_store_async,
    scrape_app_store_async,
    calculate_market_statistics,
    scrape_reviews_async,
)
