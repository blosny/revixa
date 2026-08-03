"""
Revixa — AI Analyzer & Enriched Report Generator
=================================================
Yorumları analiz eder; Duygu analizi, Churn Riski, Güncelleme Hata Uyarısı,
Rakip Bahisleri ve Özellik Sıralaması içeren profesyonel raporlar üretir.
"""

import os
import json
import logging
import re
import httpx

from models import (
    AIProvider, AIStatus, AnalysisResult,
    FeatureItem, CompetitorMention, Platform, RawReview,
    AppMetadata, RatingDistribution, SentimentDistribution,
    CountryDistribution, KeywordCount
)

logger = logging.getLogger("revixa.analyzer")

ANALYSIS_PROMPT = """Sen uzman bir mobil uygulama pazar analistisin. Sana verilen kullanıcı yorumlarını inceleyip pazar analizi raporu çıkaracaksın.

GÖREVİN VE KESİN KURALLARIN:
1. Yorumları dikkatle incele ve aşağıdaki 3 kategoride EN AZ 2-5 somut konu/özellik çıkar.
2. "summary": Yorumlardan yola çıkarak uygulamanın genel durumunu anlatan ÖZGÜN ve GERÇEK 2-3 cümlelik Türkçe değerlendirme özeti yaz.
3. "example_quotes": Özellik hakkındaki GERÇEK kullanıcı yorumlarının TAM CÜMLELERİNİ kesmeden tırnak içinde alıntıla. Kesinlikle sahte metinler YAZMA!
4. "churn_risk_score": 0 ile 100 arasında uygulamanın müşteri kaybetme riski yüzdesi (Örn: Sildim, üyelik iptali diyenlerin oranına göre).
5. "version_issue_warning": "Güncellemeden sonra bozuldu/donuyor" diyenler varsa 1 cümlelik güncelleme uyarısı yaz, yoksa "".
6. "competitor_mentions": Yorumlarda geçen rakip uygulama isimleri varsa çıkar (Örn: {"competitor_name": "Adobe", "mention_count": 3, "context": "Adobe'dan daha pratik"}).
7. "feature_rankings": Kullanıcıların en çok talep ettiği 3-5 özelliği talep sırasına göre Türkçe liste ver.

HER ZAMAN SADECE AŞAĞIDAKİ GEÇERLİ JSON YAPISINI DÖNDÜR:

{
  "summary": "",
  "churn_risk_score": 15.0,
  "version_issue_warning": "",
  "competitor_mentions": [],
  "feature_rankings": [],
  "liked": [
    {
      "title": "",
      "description": "",
      "review_count": 0,
      "example_quotes": []
    }
  ],
  "needs_improve": [
    {
      "title": "",
      "description": "",
      "review_count": 0,
      "example_quotes": []
    }
  ],
  "bad": [
    {
      "title": "",
      "description": "",
      "review_count": 0,
      "example_quotes": []
    }
  ]
}

ANALİZ EDİLECEK GERÇEK KULLANICI YORUMLARI:
"""


def _build_reviews_text(reviews: list[RawReview], max_chars: int = 15000) -> str:
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
        logger.error(f"JSON Parse Hatası: {e}. Ham metin:\n{text[:300]}...")
        data = {}

    def parse_features(items: list) -> list[FeatureItem]:
        result = []
        for item in (items or []):
            title = item.get("title", "").strip()
            if not title or "başlık" in title.lower():
                continue
            quotes = [q for q in item.get("example_quotes", []) if isinstance(q, str) and len(q) > 3 and "alıntı" not in q.lower()]
            result.append(FeatureItem(
                title=title,
                description=item.get("description", ""),
                review_count=int(item.get("review_count", 1)),
                example_quotes=quotes,
            ))
        return result

    def parse_competitors(items: list) -> list[CompetitorMention]:
        res = []
        for item in (items or []):
            if isinstance(item, dict) and item.get("competitor_name"):
                res.append(CompetitorMention(
                    competitor_name=str(item.get("competitor_name")),
                    mention_count=int(item.get("mention_count", 1)),
                    context=str(item.get("context", "")),
                ))
        return res

    summary = (data.get("summary") or "").strip()
    if not summary or "özeti" in summary.lower() and len(summary) < 80:
        pos_cnt = sum(1 for r in reviews if r.rating >= 4)
        summary = f"Kullanıcılar uygulamayı genel olarak değerlendirdi. Toplam {total_reviews} metinli yorum içinden {pos_cnt} kullanıcı olumlu geri bildirimde bulundu."

    churn_keywords = ["sildim", "siliyorum", "iptal", "berbat", "bok", "çöp", "kötü", "uninstall", "delete"]
    churn_count = sum(1 for r in reviews if any(k in r.content.lower() for k in churn_keywords))
    calculated_churn_score = round((churn_count / len(reviews)) * 100, 1) if reviews else 0.0
    churn_risk = float(data.get("churn_risk_score") or calculated_churn_score)

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
        churn_risk_score=churn_risk,
        version_issue_warning=str(data.get("version_issue_warning", "")),
        competitor_mentions=parse_competitors(data.get("competitor_mentions", [])),
        feature_rankings=list(data.get("feature_rankings", [])),
        summary=summary,
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
        reviews_text = _build_reviews_text(reviews, max_chars=25000)
        prompt = ANALYSIS_PROMPT + reviews_text

        models_to_try = [self.model_name, "gemini-1.5-flash", "gemini-flash-latest"]
        raw = None
        last_err = None

        for model in models_to_try:
            logger.info(f"Gemini analizi başlatılıyor ({len(reviews)} yorum, model: {model})...")
            for attempt in range(1, 4):
                try:
                    response = self.client.models.generate_content(
                        model=model,
                        contents=prompt,
                    )
                    raw = response.text
                    break
                except Exception as e:
                    last_err = e
                    err_msg = str(e)
                    if "RESOURCE_EXHAUSTED" in err_msg or "429" in err_msg:
                        logger.warning(f"Gemini {model} 429 Rate Limit (Deneme {attempt}/3). 3 saniye bekleniyor...")
                        import time
                        time.sleep(3)
                    elif "NOT_FOUND" in err_msg or "404" in err_msg:
                        logger.warning(f"Gemini model {model} bulunamadı, sonraki modele geçiliyor...")
                        break
                    else:
                        break
            if raw:
                break

        if not raw:
            raise last_err or RuntimeError("Gemini modellerinden yanıt alınamadı.")

        logger.info("Gemini yanıtı alındı, parse ediliyor...")

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
        reviews_text = _build_reviews_text(reviews, max_chars=8000)
        prompt = ANALYSIS_PROMPT + reviews_text

        logger.info(f"Ollama analizi başlatılıyor ({len(reviews)} yorum)...")

        with httpx.Client(timeout=600.0) as client:
            response = client.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "system": "Sen uzman bir mobil uygulama pazar analistisin. Kullanıcı yorumlarındaki GERÇEK alıntı cümlelerini eksiksiz koy. Yanıtını SADECE geçerli JSON formatında döndür.",
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
#  AI Router
# ─────────────────────────────────────────────

class AIRouter:
    def __init__(self):
        self._gemini = None
        self._ollama = OllamaAnalyzer()
        try:
            self._gemini = GeminiAnalyzer()
            logger.info("Gemini Analyzer başarıyla yüklendi.")
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
                logger.warning(f"Gemini hatası: {e} -> Ollama servisine geçiliyor...")

        if self._ollama.is_available():
            logger.info("Ollama kullanılıyor...")
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
#  Structured Markdown Report Generator (Sıfır Emoji!)
# ─────────────────────────────────────────────

def _build_markdown_report(result: AnalysisResult) -> str:
    from datetime import datetime

    lines = [
        f"# REVIXA PAZAR VE KULLANICI ANALİZ RAPORU",
        f"## {result.app_name.upper()}",
        "",
        "---",
        "",
        "### 1. UYGULAMA VE PAZAR KİMLİĞİ",
        f"- **Platform:** {result.platform.value.upper()}",
        f"- **Geliştirici:** {result.metadata.developer}",
        f"- **Kategori:** {result.metadata.category}",
        f"- **Ortalama Puan:** {result.metadata.average_rating} / 5.0 ({result.metadata.total_ratings:,} toplam değerlendirme)",
        f"- **Sürüm Versiyonu:** {result.metadata.version}",
        f"- **İşlenen Metinli Yorum:** {result.total_reviews} adet",
        f"- **Ortalama Yorum Uzunluğu:** {result.avg_review_length} karakter",
        f"- **AI Analiz Motoru:** {result.ai_provider.value.upper()}",
        f"- **Rapor Tarihi:** {datetime.now().strftime('%d.%m.%Y %H:%M')}",
        "",
        "---",
        "",
        "### 2. DUYGU, CHURN VE ÜLKE İSTATİSTİKLERİ",
        "",
        "#### Duygu Analizi Oranları:",
        f"- **Pozitif Yorumlar:** %{result.sentiment_dist.positive_pct}",
        f"- **Nötr Yorumlar:** %{result.sentiment_dist.neutral_pct}",
        f"- **Negatif Yorumlar:** %{result.sentiment_dist.negative_pct}",
        f"- **Müşteri Kaybetme (Churn) Riski:** %{result.churn_risk_score}",
    ]

    if result.version_issue_warning:
        lines.append(f"- **Güncelleme Uyarısı:** {result.version_issue_warning}")

    lines += [
        "",
        "#### Coğrafi Ülke Dağılımı (%):",
    ]

    for c_code, pct in result.country_dist.percentages.items():
        cnt = result.country_dist.counts.get(c_code, 0)
        lines.append(f"- **{c_code}:** %{pct} ({cnt} yorum / {result.total_reviews} toplam)")

    if result.top_keywords:
        lines += [
            "",
            "#### En Çok Tekrarlanan Anahtar Kelimeler:",
            ", ".join(f"`{k.keyword}` ({k.count})" for k in result.top_keywords)
        ]

    if result.feature_rankings:
        lines += [
            "",
            "#### En Çok Talep Edilen Özellik Sıralaması:",
            "\n".join(f"{i+1}. {feat}" for i, feat in enumerate(result.feature_rankings))
        ]

    lines += [
        "",
        "---",
        "",
        "### 3. GENEL PAZAR ANALİZ ÖZETİ",
        "",
        result.summary or "_Özet oluşturulamadı._",
        "",
        "---",
        "",
        "### 4. BEĞENİLEN VE ÖNE ÇIKAN ÖZELLİKLER",
        "",
    ]

    def fmt_features(features: list[FeatureItem]) -> list[str]:
        if not features:
            return ["_Özellik kaydı bulunamadı_", ""]
        out = []
        for f in features:
            out.append(f"#### [+] {f.title} _({f.review_count} Yorum)_")
            out.append(f"{f.description}")
            if f.example_quotes:
                out.append("")
                out.append("**Gerçek Kullanıcı Yorum Alıntıları:**")
                for q in f.example_quotes:
                    out.append(f'> "{q}"')
            out.append("")
        return out

    lines += fmt_features(result.liked)
    lines += ["### 5. GELİŞTİRİLMESİ GEREKEN KONULAR", ""]
    lines += fmt_features(result.needs_improve)
    lines += ["### 6. KÖTÜ VE EKSİK BULUNAN BÖLÜMLER / ŞİKAYETLER", ""]
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
