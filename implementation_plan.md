# Revixa — Mobil Uygulama Pazar Analizi Otomasyonu

> "Review + Analytica" — Mobil uygulama yorumlarını yapay zeka ile analiz ederek pazar içgörüsü üretir.

## Proje Tanımı

Google Play Store ve Apple App Store URL'lerinden uygulama yorumlarını otomatik olarak çekip, yapay zeka ile analiz ederek güzel bir rapor üreten otomasyon sistemi.

**Temel Akış**: URL gir → Yorumlar çekilir → AI analiz eder → Kategorizasyon → Rapor 

---

## Çıktı Kategorileri

| Kategori | Açıklama |
|----------|----------|
| 🟢 Beğenilen Özellikler | Kullanıcıların övdüğü, sürekli tekrar eden olumlu yorumlar |
| 🟡 Geliştirilmesi Gerekenler | Beğenilen ama eksik/buggy bulunan özellikler |
| 🔴 Kötü / Eksik Özellikler | Şikayete konu olan, kötü deneyime yol açan özellikler |

---

## Teknoloji Stack

| Katman | Araç | Notlar |
|--------|------|--------|
| Backend | **Python (FastAPI)** | REST API sunucu |
| Review Çekme | `google-play-scraper` + `app-store-scraper` | Her iki mağaza için |
| AI — Birincil | **Google Gemini API** (gemini-1.5-flash) | Ücretsiz tier, önce bunu dene |
| AI — Yedek | **Ollama** (llama3.2 / mistral) | Gemini limit dolunca otomatik geçiş |
| Web UI | **HTML + CSS + Vanilla JS** | Modern, glassmorphism tasarım |
| Çıktı | JSON + Markdown rapor | İndirilebilir |

---

## AI Fallback Mekanizması (Önemli!)

> [!IMPORTANT]
> Gemini API limiti dolduğunda sistem **otomatik olarak Ollama'ya geçer**.
> Kullanıcıya bildirim gösterilir: "Gemini limiti doldu, Ollama kullanılıyor..."

### Fallback Akışı:

```
1. İstek gelir
       ↓
2. Gemini API'ye gönder
       ↓
3. Başarılı mı?
   ✅ EVET → Gemini sonuçları kullan
   ❌ HAYIR (429 Rate Limit) →
       ↓
4. Ollama kurulu mu? (localhost:11434 ping)
   ✅ EVET → Ollama'ya gönder (llama3.2 veya mistral)
   ❌ HAYIR → Kullanıcıya mesaj: "Ollama kurulumu gerekli"
       ↓
5. Hangi AI kullanıldı → UI'da göster
```

### Ollama Kurulumu (isteğe bağlı, sadece fallback için):
```bash
# Windows'ta Ollama kurulumu:
# https://ollama.com/download

ollama pull llama3.2   # ~2GB, hızlı
# veya
ollama pull mistral    # ~4GB, daha güçlü
```

---

## Mimari

```
[Kullanıcı URL girer]
       ↓
[Web UI (Frontend)]  ←→  [FastAPI Backend (Port 8000)]
                               ↓
                    [Scraper: Play Store / App Store]
                               ↓
                    [AI Router]
                    ├── Gemini 1.5 Flash (birincil)
                    └── Ollama llama3.2 (yedek)
                               ↓
                    [Yapılandırılmış Rapor]
                               ↓
                    [Web UI'da Göster + İndir]
```

---

## Proje Yapısı

```
revixa/
├── backend/
│   ├── main.py              # FastAPI app + endpoint'ler
│   ├── scraper.py           # Review çekme (Play + AppStore)
│   ├── analyzer.py          # AI Router: Gemini → Ollama fallback
│   ├── models.py            # Pydantic veri modelleri
│   └── requirements.txt     # Python bağımlılıkları
├── frontend/
│   ├── index.html           # Ana sayfa
│   ├── style.css            # Modern glassmorphism UI
│   └── app.js               # Frontend logic + API iletişimi
├── .env                     # API keys (git'e eklenmez!)
├── .env.example             # Örnek env dosyası
└── README.md
```

---

## Proposed Changes

### Backend

#### [NEW] backend/requirements.txt
```
fastapi
uvicorn[standard]
google-play-scraper
app-store-scraper
google-generativeai
httpx
python-dotenv
pydantic
```

#### [NEW] backend/models.py
- `AnalysisRequest`: url, platform (auto/play/appstore), max_reviews
- `FeatureItem`: title, description, sentiment_score, review_count
- `AnalysisResult`: app_name, total_reviews, liked/needs_improvement/bad lists, ai_provider

#### [NEW] backend/scraper.py
- `PlayStoreScraper`: URL'den app ID çıkar, max 200 yorum çek
- `AppStoreScraper`: URL'den app ID çıkar, max 200 yorum çek
- `auto_detect_platform()`: URL'e bakarak platform tespit et

#### [NEW] backend/analyzer.py
- `GeminiAnalyzer`: Gemini 1.5 Flash ile analiz
- `OllamaAnalyzer`: Ollama REST API ile analiz (localhost:11434)
- `AIRouter`: Önce Gemini dene → 429/hata → Ollama'ya geç
- Her iki analyzer da aynı prompt'u kullanır (tutarlılık için)

#### [NEW] backend/main.py
- `POST /analyze`: Ana analiz endpoint'i
- `GET /health`: Servis sağlık kontrolü + AI provider durumu
- `GET /ai-status`: Gemini ve Ollama'nın durumunu göster
- CORS ayarları

### Frontend

#### [NEW] frontend/index.html + style.css + app.js
- Dark mode glassmorphism tasarım
- URL input + "Analiz Et" butonu
- Hangi AI kullanıldığını gösteren badge (🌟 Gemini / 🦙 Ollama)
- Canlı loading animasyonu (scraping → analiz → rapor aşamaları)
- 3 kategori kartı (renkli, ikonlu)
- Her kategoride özellik listesi (review sayısı ile)
- Markdown rapor indirme butonu

---

## Gemini API Ücretsiz Limit

> [!NOTE]
> Gemini 1.5 Flash ücretsiz tier:
> - Dakikada 15 istek
> - Günde 1500 istek  
> - 1M token/gün
> 
> Günlük birkaç analiz için fazlasıyla yeterli. Yoğun kullanımda Ollama devreye girer.
> 
> API key: https://aistudio.google.com/apikey

---

## Verification Plan

### Otomatik Test
- `pytest backend/` → scraper ve analyzer unit testleri
- Gemini limit simülasyonu → Ollama fallback'in çalışması

### Manuel Doğrulama
- Instagram Play Store URL'si ile test
- WhatsApp App Store URL'si ile test
- Gemini limiti dolu iken Ollama fallback testi
- Rapor indirme testi
