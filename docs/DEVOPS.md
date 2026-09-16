# REVIXA DEVOPS VE CI/CD REHBERİ

## 1. Containerization (Docker & Docker Compose)

- **Dockerfile**: Python 3.13 tabanlı, multi-stage build (Builder + Runner) yapısındadır. Non-root `appuser` kullanıcısı ile güvenlik sıkılaştırması yapılmış ve `HEALTHCHECK` eklenmiştir.
- **docker-compose.yml**: Backend sunucusu, Nginx reverse proxy ve SQLite veri kalıcılığını (`revixa-db-data`) orkestre eder.

---

## 2. CI/CD Pipeline (GitHub Actions)

`.github/workflows/ci.yml` dosyası her push ve pull request isteğinde otomatik tetiklenir:
1. Python 3.13 ortamını kurar.
2. Bağımlılıkları önbellekler (pip cache).
3. `pytest` test süitini koşturur.

---

## 3. Pre-Commit Hooks (`.pre-commit-config.yaml`)

Commit öncesinde kod kalitesini otomatikleştirmek için:
- Black formatlayıcı
- Trailing whitespace temizleyici
- Secret leak ve JSON/YAML doğrulaması

Çalıştırmak için:
```powershell
pip install pre-commit
pre-commit run --all-files
```
