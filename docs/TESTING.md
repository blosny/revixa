# REVIXA TEST MİMARİSİ VE OTOMASYON REHBERİ

## 1. Test Stratejisi ve Yapısı

REVIXA test süiti, Python `pytest` ve `httpx` (FastAPI TestClient) araçları kullanılarak modüler yapıda geliştirilmiştir. Sistemdeki tüm bağımlılıklar izole edilmiş ve dış ağ bağımlılıkları mock'lanmıştır.

### 1.1 Test Dosyaları Haritası

| Test Dosyası | Test Edilen Bileşen / Modül | Kapsam ve Senaryolar |
| :--- | :--- | :--- |
| `tests/test_main.py` | FastAPI Core Router (`main.py`) | URL doğrulama, SSRF koruması, `/api/analyze` endpoint, liveness & readiness probları. |
| `tests/test_auth.py` | Kimlik Doğrulama (`auth.py`) | Kullanıcı kaydı (`/api/auth/register`), giriş (`/api/auth/login`), JWT token üretimi, prod modunda JWT secret key kontrolü. |
| `tests/test_saved_apps.py` | Uygulama Kaydetme API (`main.py`, `database.py`) | Kullanıcının takip ettiği uygulamaları listeleme, ekleme, silme ve yetkisiz erişim engellemesi. |
| `tests/test_scraper_service.py` | Mağaza Scraper Servisi (`backend/services/scraper_service.py`) | Platform tespiti, Play Store ID / iTunes App ID ayıklaması, App Store metadata çekme, weighted average rating hesabı. |
| `tests/test_ai_service.py` | AI Analiz Servisi (`backend/services/ai_service.py`) | Rule-based fallback duygu dağılımı, Gemini/Ollama durum kontrolü, AI status nesnesi. |
| `tests/test_custom_prompt.py` | Kullanıcı Ek Prompt Yapısı (`main.py`, `ai_service.py`) | Özel kullanıcı talimatlarının AI prompt'una sorunsuz enjekte edilmesi ve şema uyumluluğu. |

---

## 2. Izolasyon ve Mocking Stratejisi

Testlerin dış servislerden (Google Play Store, iTunes RSS, Gemini API, Ollama) bağımsız ve hızlı koşması için `unittest.mock.patch` kullanılır.

### 2.1 AIService Mocklama Örneği
```python
from unittest.mock import patch
from backend.services.ai_service import AIInsightResponse, ChurnRisk, VersionWarning

@patch("backend.services.ai_service.AIService.analyze")
def test_analyze_with_mocked_ai(mock_ai_analyze, client):
    # Mock yanıtı tanımlanır
    mock_ai_analyze.return_value = AIInsightResponse(
        sentiment_breakdown={"positive": 80.0, "neutral": 10.0, "negative": 10.0},
        churn_risk=ChurnRisk(score=15.0, level="LOW", reasons=["Good app stability"]),
        version_warning=VersionWarning(has_warning=false, version="1.0.0", issues=[]),
        competitor_radar=[],
        feature_rankings=[],
        key_insights=["Great app overall"]
    )
    
    response = client.post("/api/analyze", json={"url": "https://play.google.com/store/apps/details?id=com.spotify.music"})
    assert response.status_code == 200
    assert response.json()["ai_analysis"]["sentiment_breakdown"]["positive"] == 80.0
```

---

## 3. Test Komutları ve Kapsayıcılık (Coverage)

### 3.1 Tüm Test Süitini Çalıştırma
```powershell
.\venv\Scripts\pytest tests/ -v
```

### 3.2 Hızlı Birim Testlerini Çalıştırma (Canlı Ağ İsteklerini Atlayarak)
```powershell
.\venv\Scripts\pytest tests/ -k "not test_valid_play_store_url_scraping" -v
```

### 3.3 Kod Kapsayıcılığı (Code Coverage) Raporu Üretme
Tüm projenin test kapsayıcılığını ölçmek ve HTML raporu oluşturmak için:

```powershell
.\venv\Scripts\pytest --cov=backend --cov=backend/services --cov-report=term-missing --cov-report=html tests/
```

Rapor oluşturulduktan sonra `htmlcov/index.html` dosyası taranarak eksik test satırları tespit edilebilir.

---

## 4. CI/CD Otomasyon Kuralları

- **Sıfır Hata Politikası**: GitHub Actions CI (`.github/workflows/ci.yml`) üzerinde tek bir testin dahi başarısız olması PR birleştirmesini (Merge) engeller.
- **Performans Eşiği**: Tüm birim test süiti 10 saniyenin altında tamamlanmalıdır.

