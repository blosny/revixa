"""
Revixa — AI Analyzer & Structured Report Generator
===================================================
Yorumları analiz eder, duygu analizi hesaplar ve
profesyonel Markdown & PDF uyumlu raporlar üretir.
"""

import os
import json
import logging
import re
import httpx

from models import (
    AIProvider, AIStatus, AnalysisResult,
    FeatureItem, Platform, RawReview,
    AppMetadata, RatingDistribution, SentimentDistribution,
    CountryDistribution, KeywordCount
)

logger = logging.getLogger("revixa.analyzer")

# ─────────────────────────────────────────────
#  Prompt
# ─────────────────────────────────────────────

ANALYSIS_PROMPT = """Sen uzman bir mobil uygulama pazar analistisin. Sana verilen kullanıcı yorumlarını inceleyip pazar analizi raporu çıkaracaksın.

GÖREVİN:
Yorumları oku ve aşağıdaki 3 kategoride EN AZ 2-5 somut konu/özellik çıkar:
1. "liked": Kullanıcıların övdüğü ve beğendiği özellikler
2. "needs_improve": Kullanıcıların geliştirilmesini veya yeni eklenmesini istediği konular
3. "bad": Kullanıcıların şikayet ettiği, hata/bug olan veya beğenilmeyen konular

HER ZAMAN SADECE AŞAĞIDAKİ GEÇERLİ JSON FORMATINI DÖNDÜR (Başka hiçbir açıklama yazma):

{
  "summary": "Uygulama hakkında detaylı 2-3 cümlelik Türkçe genel pazar değerlendirme özeti.",
  "liked": [
    {
      "title": "Beğenilen Özellik Adı",
      "description": "Kullanıcıların bu özelliği neden beğendiğinin açıklaması",
      "review_count": 3,
      "example_quotes": ["Kullanıcı yorumu alıntısı 1"]
    }
  ],
  "needs_improve": [
    {
      "title": "Geliştirilmesi Gereken Konu",
      "description": "Kullanıcıların neyin eklenmesini istediğinin açıklaması",
      "review_count": 2,
      "example_quotes": ["Kullanıcı yorumu alıntısı 2"]
    }
  ],
  "bad": [
    {
      "title": "Hata veya Şikayet Konusu",
      "description": "Kullanıcıların yaşadığı sorunun açıklaması",
      "review_count": 2,
      "example_quotes": ["Kullanıcı yorumu alıntısı 3"]
    }
  ]
}

ANALİZ EDİLECEK YORUMLAR:
"""


def _build_reviews_text(reviews: list[RawReview], max_chars: int = 6000) -> str:
    lines = []
    total = 0
    for i, r in enumerate(reviews, 1):
        line = f"[{i}] Puan:{r.rating}/5 | {r.content}"
        if total + len(line) > max_chars:
            break
        lines.append(line)
        total += len(line)
    return "\n".join(lines)


def calculate_sentiment_distribution(reviews: list[RawReview]) -> SentimentDistribution:
    """Yorum puanlarına göre pozitif, nötr ve negatif duygu oranlarını hesaplar."""
    if not reviews:
        return SentimentDistribution()

    total = len(reviews)
    pos = sum(1 for r in reviews if r.rating >= 4.0)
    neu = sum(1 for r in reviews if r.rating == 3.0)
    neg = sum(1 for r in reviews if r.rating <= 2.0)

    return SentimentDistribution(
        positive_pct=round((pos / total) * 100, 1),
        neutral_pct=round((neu / total) * 100, 1),
        negative_pct=round((neg / total) * 100, 1),
    )


def _parse_ai_response(raw: str, app_name: str, platform: Platform,
                       total_reviews: int, provider: AIProvider,
                       metadata: AppMetadata, rating_dist: RatingDistribution,
                       country_dist: CountryDistribution, avg_len: int,
                       keywords: list[KeywordCount], reviews: list[RawReview]) -> AnalysisResult:
    text = raw.strip()
    match = re.search(r"\{.*\}", text, re.DOTALL)
    json_str = match.group(0) if match else text

    try:
        data = json.loads(json_str)
    except json.JSONDecodeError as e:
        logger.error(f"JSON Parse Hatası. Ham metin:\n{text[:300]}...")
        data = {"summary": "Analiz tamamlandı.", "liked": [], "needs_improve": [], "bad": []}

    def parse_features(items: list) -> list[FeatureItem]:
        result = []
        for item in (items or []):
            result.append(FeatureItem(
                title=item.get("title", "Genel Özellik"),
                description=item.get("description", ""),
                review_count=int(item.get("review_count", 1)),
                example_quotes=item.get("example_quotes", []),
            ))
        return result

    sentiment = calculate_sentiment_distribution(reviews)

    res = AnalysisResult(
        app_name=app_name,
        platform=platform,
        total_reviews=total_reviews,
        ai_provider=provider,
        metadata=metadata,
        rating_dist=rating_dist,
        sentiment_dist=sentiment,
        country_dist=country_dist,
        top_keywords=keywords,
        avg_review_length=avg_len,
        summary=data.get("summary", "Pazar analizi özeti hazırlandı."),
        liked=parse_features(data.get("liked", [])),
        needs_improve=parse_features(data.get("needs_improve", [])),
        bad=parse_features(data.get("bad", [])),
    )

    res.markdown_report = _build_markdown_report(res)
    return res


# ─────────────────────────────────────────────
#  Gemini Analyzer
# ─────────────────────────────────────────────

class GeminiAnalyzer:
    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY", "").strip()
        if not api_key:
            raise ValueError("GEMINI_API_KEY bulunamadı.")
        try:
            from google import genai
            self.client = genai.Client(api_key=api_key)
            self.model_name = "gemini-2.0-flash"
        except ImportError:
            raise RuntimeError("google-genai paketi bulunamadı.")

    def analyze(self, reviews: list[RawReview], app_name: str, platform: Platform,
                metadata: AppMetadata, rating_dist: RatingDistribution,
                country_dist: CountryDistribution, avg_len: int,
                keywords: list[KeywordCount]) -> AnalysisResult:
        reviews_text = _build_reviews_text(reviews)
        prompt = ANALYSIS_PROMPT + reviews_text

        logger.info(f"Gemini analizi başlatılıyor ({len(reviews)} yorum)...")
        response = self.client.models.generate_content(
            model=self.model_name,
            contents=prompt,
        )
        raw = response.text

        return _parse_ai_response(
            raw, app_name, platform, len(reviews), AIProvider.GEMINI,
            metadata, rating_dist, country_dist, avg_len, keywords, reviews
        )


# ─────────────────────────────────────────────
#  Ollama Analyzer
# ─────────────────────────────────────────────

class OllamaAnalyzer:
    def __init__(self):
        self.base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        self.model    = os.getenv("OLLAMA_MODEL", "llama3.2")

    def is_available(self) -> bool:
        try:
            with httpx.Client(timeout=3) as client:
                r = client.get(f"{self.base_url}/api/tags")
                if r.status_code == 200:
                    models = [m.get("name", "").split(":")[0] for m in r.json().get("models", [])]
                    return any(self.model in m or m in self.model for m in models) or len(models) > 0
                return False
        except Exception:
            return False

    def analyze(self, reviews: list[RawReview], app_name: str, platform: Platform,
                metadata: AppMetadata, rating_dist: RatingDistribution,
                country_dist: CountryDistribution, avg_len: int,
                keywords: list[KeywordCount]) -> AnalysisResult:
        reviews_text = _build_reviews_text(reviews, max_chars=6000)
        prompt = ANALYSIS_PROMPT + reviews_text

        logger.info(f"Ollama analizi başlatılıyor ({len(reviews)} yorum)...")

        with httpx.Client(timeout=600.0) as client:
            response = client.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "system": "Sen uzman bir mobil uygulama pazar analistisin. Yanıtını SADECE geçerli JSON formatında döndür. Hiçbir ekstra açıklama yazma.",
                    "format": "json",
                    "stream": False,
                    "options": {
                        "temperature": 0.2,
                        "num_predict": 4096,
                    },
                },
            )
            response.raise_for_status()
            raw = response.json().get("response", "")

        return _parse_ai_response(
            raw, app_name, platform, len(reviews), AIProvider.OLLAMA,
            metadata, rating_dist, country_dist, avg_len, keywords, reviews
        )


# ─────────────────────────────────────────────
#  AI Router — Gemini → Ollama Fallback
# ─────────────────────────────────────────────

class AIRouter:
    def __init__(self):
        self._gemini = None
        self._ollama = OllamaAnalyzer()
        try:
            self._gemini = GeminiAnalyzer()
        except Exception as e:
            logger.warning(f"Gemini başlatılamadı: {e}")

    def analyze(self, reviews: list[RawReview], app_name: str, platform: Platform,
                metadata: AppMetadata, rating_dist: RatingDistribution,
                country_dist: CountryDistribution, avg_len: int,
                keywords: list[KeywordCount]) -> AnalysisResult:
        if self._gemini:
            try:
                return self._gemini.analyze(reviews, app_name, platform, metadata, rating_dist, country_dist, avg_len, keywords)
            except Exception as e:
                logger.warning(f"Gemini hatası: {e} → Ollama'ya geçiliyor...")

        if self._ollama.is_available():
            return self._ollama.analyze(reviews, app_name, platform, metadata, rating_dist, country_dist, avg_len, keywords)

        raise RuntimeError("Hiçbir AI servisi kullanılamıyor.")

    def get_status(self) -> AIStatus:
        gemini_ok = self._gemini is not None
        ollama_ok = self._ollama.is_available()
        return AIStatus(
            gemini_available=gemini_ok,
            ollama_available=ollama_ok,
            ollama_model=self._ollama.model if ollama_ok else "",
            active_provider=AIProvider.GEMINI if gemini_ok else (AIProvider.OLLAMA if ollama_ok else AIProvider.NONE),
        )


# ─────────────────────────────────────────────
#  Structured Markdown & PDF Report Generator
# ─────────────────────────────────────────────

def _build_markdown_report(result: AnalysisResult) -> str:
    from datetime import datetime

    lines = [
        f"# REVIXA PAZAR VE KULLANICI ANALİZ RAPORU",
        f"## {result.app_name.upper()}",
        "",
        "---",
        "",
        "### 📌 1. UYGULAMA VE PAZAR KİMLİĞİ",
        f"- **Platform:** {result.platform.value.upper()}",
        f"- **Geliştirici:** {result.metadata.developer}",
        f"- **Kategori:** {result.metadata.category}",
        f"- **Ortalama Puan:** ⭐ {result.metadata.average_rating} / 5.0 ({result.metadata.total_ratings:,} toplam değerlendirme)",
        f"- **Sürüm Versiyonu:** {result.metadata.version}",
        f"- **İşlenen Metinli Yorum:** {result.total_reviews} adet",
        f"- **Ortalama Yorum Uzunluğu:** {result.avg_review_length} karakter",
        f"- **AI Analiz Motoru:** {result.ai_provider.value.upper()}",
        f"- **Rapor Tarihi:** {datetime.now().strftime('%d.%m.%Y %H:%M')}",
        "",
        "---",
        "",
        "### 📊 2. DUYGU VE ÜLKE DAĞILIM İSTATİSTİKLERİ",
        "",
        "#### Duygu Analizi Oranları:",
        f"- 🟢 **Pozitif Yorumlar:** %{result.sentiment_dist.positive_pct}",
        f"- 🟡 **Nötr Yorumlar:** %{result.sentiment_dist.neutral_pct}",
        f"- 🔴 **Negatif Yorumlar:** %{result.sentiment_dist.negative_pct}",
        "",
        "#### Coğrafi Ülke Dağılımı (%):",
    ]

    for c_code, pct in result.country_dist.percentages.items():
        cnt = result.country_dist.counts.get(c_code, 0)
        lines.append(f"- **{c_code}:** %{pct} ({cnt} yorum)")

    if result.top_keywords:
        lines += [
            "",
            "#### En Çok Tekrarlanan Anahtar Kelimeler:",
            ", ".join(f"`{k.keyword}` ({k.count})" for k in result.top_keywords)
        ]

    lines += [
        "",
        "---",
        "",
        "### 📝 3. GENEL PAZAR ANALİZ ÖZETİ",
        "",
        result.summary or "_Özet oluşturulamadı._",
        "",
        "---",
        "",
        "### 🟢 4. BEĞENİLEN VE ÖNE ÇIKAN ÖZELLİKLER",
        "",
    ]

    def fmt_features(features: list[FeatureItem]) -> list[str]:
        if not features:
            return ["_Özellik kaydı bulunamadı_", ""]
        out = []
        for f in features:
            out.append(f"#### • {f.title} _({f.review_count} Yorum)_")
            out.append(f"{f.description}")
            if f.example_quotes:
                out.append("")
                for q in f.example_quotes:
                    out.append(f'> "{q}"')
            out.append("")
        return out

    lines += fmt_features(result.liked)
    lines += ["### 🟡 5. GELİŞTİRİLMESİ GEREKEN KONULAR", ""]
    lines += fmt_features(result.needs_improve)
    lines += ["### 🔴 6. KÖTÜ VE EKSİK BULDUTAN BÖLÜMLER / ŞİKAYETLER", ""]
    lines += fmt_features(result.bad)

    lines += [
        "---",
        "",
        "_Revixa Pazar İntibak Otomasyonu tarafından otomatik oluşturulmuştur._"
    ]

    return "\n".join(lines)


_router_instance: AIRouter | None = None

def get_router() -> AIRouter:
    global _router_instance
    if _router_instance is None:
        _router_instance = AIRouter()
    return _router_instance
