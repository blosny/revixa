# REVIXA DEVOPS, CONTAINERIZATION VE OPERASYONEL RUNBOOK

## 1. Konteyner Mimarisi (Docker & Docker Compose)

REVIXA v2.0, üretim ortamına hazır, güvenliği sıkılaştırılmış ve ölçeklenebilir multi-stage Docker mimarisi üzerine inşa edilmiştir.

### 1.1 Multi-Stage Dockerfile Mimarisi (`Dockerfile`)

```dockerfile
# Stage 1: Builder
FROM python:3.13-slim AS builder
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends gcc && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# Stage 2: Runner
FROM python:3.13-slim AS runner
WORKDIR /app
RUN useradd -m -u 1000 appuser
COPY --from=builder /root/.local /home/appuser/.local
COPY --chown=appuser:appuser . .
ENV PATH=/home/appuser/.local/bin:$PATH \
    PYTHONUNBUFFERED=1 \
    ENVIRONMENT=production

USER appuser
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/health/live || exit 1

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### Öne Çıkan Güvenlik ve Performans Özellikleri:
- **Root-less Çalışma**: `appuser` (UID 1000) ile çalışarak yetki yükseltme (privilege escalation) saldırılarına karşı korunur.
- **İnce İmaj Boyutu**: Multi-stage build sayesinde derleme bağımlılıkları (gcc, build-essential) nihai runner imajına dahil edilmez.
- **Entegre Healthcheck**: Docker Daemon `/health/live` probe endpoint'ini 30 saniyede bir sorgulayarak konteynerin durumunu izler.

---

### 1.2 Docker Compose Orkestrasyonu (`docker-compose.yml`)

```yaml
version: '3.8'

services:
  revixa-backend:
    build: .
    container_name: revixa_app
    restart: always
    ports:
      - "8000:8000"
    environment:
      - ENVIRONMENT=production
      - JWT_SECRET_KEY=${JWT_SECRET_KEY}
      - GEMINI_API_KEY=${GEMINI_API_KEY}
    volumes:
      - revixa-db-data:/app/backend/data
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health/live"]
      interval: 10s
      timeout: 5s
      retries: 3

volumes:
  revixa-db-data:
    driver: local
```

---

## 2. Production Nginx Reverse Proxy Konfigürasyonu

Üretim ortamında SSL/TLS sonlandırma ve Rate Limiting işlemleri Nginx reverse proxy ile gerçekleştirilir:

```nginx
events { worker_connections 1024; }

http {
    limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/s;

    server {
        listen 80;
        server_name revixa.yourdomain.com;

        # Static Frontend Files
        location / {
            root /usr/share/nginx/html;
            index index.html;
            try_files $uri $uri/ /index.html;
        }

        # FastAPI Backend Proxy
        location /api/ {
            limit_req zone=api_limit burst=20 nodelay;
            proxy_pass http://revixa_app:8000;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }
    }
}
```

---

## 3. CI/CD Otomasyon Pipeline'ı (GitHub Actions)

`.github/workflows/ci.yml` dosyası her commit ve PR tetiklemesinde otomatik çalışır.

### Pipeline Adımları:
1. **Checkout & Environment Setup**: Proje reposu çekilir ve Python 3.13 kurulur.
2. **Dependency Caching**: `pip` bağımlılıkları rehber hash ile önbelleğe alınır.
3. **Automated Test Suite Execution**: `pytest` ile tüm birim ve entegrasyon testleri koşturulur.
4. **Security & Code Linting**: Secret leak, syntax ve Pydantic validasyon kontrolleri gerçekleştirilir.

---

## 4. Pre-Commit Hook Süiti (`.pre-commit-config.yaml`)

Yerel geliştirmede hatalı kodun commitlemesini engellemek için pre-commit yapılandırması:

```yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files

  - repo: https://github.com/psf/black
    rev: 24.1.1
    hooks:
      - id: black
        language_version: python3.13
```

Kurulum için:
```powershell
pip install pre-commit
pre-commit install
pre-commit run --all-files
```

---

## 5. Operasyonel Sorun Giderme Runbook'u (Troubleshooting)

### Senaryo A: Gemini API 429 Rate Limit (Quota Exceeded)
- **Belirti**: Sistem günlüklerinde `Gemini API quota exceeded` uyarısı ve Ollama fallback mesajı.
- **Çözüm**: Sistem otomatik olarak yerel Ollama modeline düşer. Kota yenilendiğinde Gemini API'ye geri döner. Manuel müdahale gerekmez.

### Senaryo B: SQLite `database is locked` Hatalı Erişimi
- **Belirti**: Eşzamanlı yazma isteklerinde 500 Internal Server Error.
- **Çözüm**: `database.py` içerisindeki SQLite WAL (Write-Ahead Logging) modunun aktif olduğundan emin olun:
  ```python
  connection.execute("PRAGMA journal_mode=WAL;")
  ```

### Senaryo C: Production JWT_SECRET_KEY Eksikliği
- **Belirti**: Prod modunda uygulama başlarken `ValueError: Production mode requires a strict JWT_SECRET_KEY` hatası vererek çöker.
- **Çözüm**: `.env` dosyasına veya Docker ortam değişkenlerine en az 32 karakterlik rastgele karmaşık bir secret key ekleyin:
  ```env
  ENVIRONMENT=production
  JWT_SECRET_KEY=9a8b7c6d5e4f3a2b1c0d9e8f7a6b5c4d
  ```

