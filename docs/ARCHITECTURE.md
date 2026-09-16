# REVIXA v2.0 — SİSTEM MİMARİSİ VE VERİ AKIŞ REHBERİ

## 1. Mimari Genel Bakış

REVIXA, mobil uygulama mağazalarından (Google Play Store ve Apple App Store) kullanıcı yorumlarını ve pazarlama metadatalarını toplayan, AI destekli duygu (sentiment), terk etme riski (churn risk) ve stratejik rakip analizi gerçekleştiren bir **Pazar Zekası Otomasyonu**dur.

```
[ Frontend (HTML/JS/CSS) ] 
       │ (REST API)
       ▼
[ FastAPI Backend Router (main.py) ]
       │
       ├──► [ Scraper Module (scraper.py) ] ──► Play Store / iTunes RSS
       ├──► [ AI Router (analyzer.py) ]    ──► Gemini 2.0 Flash / Ollama
       └──► [ Auth & DB (auth.py, database.py) ] ──► SQLite (User Apps & Auth)
```

---

## 2. Modül Detayları

### 2.1 Backend Router (`backend/main.py`)
- **FastAPI Core**: Uygulamanın HTTP API katmanıdır.
- **SSRF Güvenlik Katmanı**: `validate_input_url` fonksiyonu `urllib.parse.urlparse` kullanarak katı domain doğrulaması yapar (`play.google.com` ve `apps.apple.com`).
- **Async Event Loop Unblocking**: Senkron AI ve scraping istekleri `asyncio.to_thread` ile thread havuzuna aktarılarak FastAPI'nin kilitlenmesi engellenir.
- **Observability**: `/health/live` (Liveness) ve `/health/ready` (Readiness) probe endpoint'leri barındırır.

### 2.2 Scraper Motoru (`backend/scraper.py`)
- **Çoklu Ülke Paralel Gathering**: `TR`, `US`, `DE`, `GB` vb. desteklenen ülkelerden paralel async scraping yapar.
- **Ağırlıklı Ortalama (Weighted Average)**: Çift mağaza isteklerinde (`Platform.BOTH`) indirme/oylama sayılarına oranla ağırlıklı puan ortalaması hesaplar.
- **Coğrafi İzole Tekleştirme**: Yorum tekleştirmesi `(country, review_content)` çifti ile yapılır; böylece farklı ülkelerdeki geçerli yorumlar elenmez.

### 2.3 AI Analiz Motoru (`backend/analyzer.py`)
- **Cascade Fallback Motoru**: Öncelikli olarak Google Gemini API'ye istek atar; kota aşımı (429) veya hata durumunda lokal Ollama LLM motoruna otomatik düşer.
- **Zenginleştirilmiş Pydantic Şemaları**: Churn risk skoru, güncelleme hatası uyarısı, rakip bahsetmeleri ve özellik sıralamalarını Pydantic ile doğrular.
