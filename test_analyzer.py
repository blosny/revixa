"""
Revixa — Analyzer Testi
========================
Gerçek yorumları çekip Gemini ile analiz eder.
"""
import sys
import io
import os
sys.path.insert(0, "backend")
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from dotenv import load_dotenv
load_dotenv()

from scraper import scrape_reviews
from analyzer import get_router

APP_URL = "https://play.google.com/store/apps/details?id=com.acabaneyesem"

print("=" * 55)
print("Adim 1: Yorumlar cekiliyor...")
print("=" * 55)

app_name, platform, reviews = scrape_reviews(APP_URL, max_reviews=0)
print(f"Uygulama : {app_name}")
print(f"Platform : {platform.value}")
print(f"Yorum    : {len(reviews)} adet")
print()

print("=" * 55)
print("Adim 2: AI Analizi baslatiliyor...")
print("=" * 55)

router = get_router()
status = router.get_status()
print(f"Gemini: {'Hazir' if status.gemini_available else 'Yok'}")
print(f"Ollama: {'Hazir' if status.ollama_available else 'Yok'}")
print(f"Aktif : {status.active_provider.value}")
print()

result = router.analyze(reviews, app_name, platform)

print("=" * 55)
print("SONUC")
print("=" * 55)
print(f"AI     : {result.ai_provider.value}")
print(f"Ozet   : {result.summary[:200]}...")
print()

print(f"Begenilenler ({len(result.liked)}):")
for f in result.liked:
    print(f"  + {f.title} ({f.review_count} yorum)")

print(f"\nGelistirilmesi Gereken ({len(result.needs_improve)}):")
for f in result.needs_improve:
    print(f"  ~ {f.title} ({f.review_count} yorum)")

print(f"\nKotu/Eksik ({len(result.bad)}):")
for f in result.bad:
    print(f"  - {f.title} ({f.review_count} yorum)")

print()
print("Markdown rapor uzunlugu:", len(result.markdown_report), "karakter")
