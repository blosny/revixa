# =========================================================
# Revixa FastAPI Backend — Multi-stage Production Dockerfile
# =========================================================

# ---------------------------------------------------------
# Evre 1: Builder (Bağımlılıkların ve derlemelerin hazırlanması)
# ---------------------------------------------------------
FROM python:3.13-slim AS builder

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ---------------------------------------------------------
# Evre 2: Runner (Hafifletilmiş ve Güvenli Çalışma Ortamı)
# ---------------------------------------------------------
FROM python:3.13-slim AS runner

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Builder evresinden sadece gerekli Python paketlerinin kopyalanması
COPY --from=builder /usr/local/lib/python3.13/site-packages /usr/local/lib/python3.13/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Uygulama kaynak kodlarının kopyalanması
COPY backend/ /app/backend/

# Güvenlik: Uygulamayı yetkisiz (non-root) sistem kullanıcısı ile çalıştırma
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

# Container Healthcheck (Sağlık Kontrolü)
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

# Web sunucusunun başlatılması
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
