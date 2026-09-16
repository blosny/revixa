# REVIXA TEST MİMARİSİ VE OTOMASYON REHBERİ

## 1. Test Stratejisi

REVIXA test paketleri Pytest çatısı kullanılarak yazılmıştır. Testler 3 ana katmandan oluşur:

1. **Birim Testleri (Unit Tests)**: Scraper yardımcı fonksiyonları, URL doğrulama, URL unquoting, weighted average metrik birleştirme.
2. **Kimlik Doğrulama Testleri (`tests/test_auth.py`)**: Kullanıcı kaydı, giriş yapma, JWT token üretimi ve production modunda zorunlu JWT secret key doğrulaması.
3. **Kayıtlı Uygulamalar CRUD Testleri (`tests/test_saved_apps.py`)**: Kullanıcı panelindeki uygulama kaydetme ve silme API'lerinin doğrulanması.

---

## 2. Testleri Çalıştırma

Tüm test paketini çalıştırmak için:

```powershell
.\venv\Scripts\pytest tests/ -v
```

Hızlı birim testlerini koşturmak için (Canlı scraping isteklerini atlayarak):

```powershell
.\venv\Scripts\pytest tests/ -k "not scraping" -v
```
