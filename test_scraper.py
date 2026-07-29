"""
Revixa — Tam Yorum Çekme Testi
================================
max_reviews=0 → Sınırsız (tüm yorumlar)
"""
import sys
import io
sys.path.insert(0, "backend")
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from scraper import scrape_reviews
from models import Platform

APP_URL = "https://play.google.com/store/apps/details?id=com.acabaneyesem"

print("=" * 55)
print("TEST: Acaba Ne Yesem? — SINIRIRSIZ yorum (max=0)")
print("=" * 55)

try:
    app_name, platform, reviews = scrape_reviews(
        APP_URL,
        platform=Platform.AUTO,
        max_reviews=0  # 0 = tüm yorumlar
    )
    print(f"Uygulama  : {app_name}")
    print(f"Platform  : {platform.value}")
    print(f"Toplam    : {len(reviews)} yorum")
    print()

    # Puan dağılımı
    from collections import Counter
    ratings = Counter(int(r.rating) for r in reviews)
    print("Puan dagilimi:")
    for star in range(5, 0, -1):
        count = ratings.get(star, 0)
        bar = "#" * count
        print(f"  {star} yildiz: {count:3d}  {bar}")
    print()

    print("--- Tum yorumlar ---")
    for i, r in enumerate(reviews, 1):
        print(f"[{i}] {r.rating}/5 | {r.author}")
        print(f"    {r.content}")
        print()

except Exception as e:
    print(f"HATA: {type(e).__name__}: {e}")
