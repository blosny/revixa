"""
Revixa — AI Service Layer
=========================
Google Gemini API ve Lokal Ollama LLM Cascade Fallback motoru.
Duygu analizi, Churn Riski, Güncelleme Uyarısı, Rakip Bahsetmeleri ve Özellik Sıralaması servisi.
"""

import os
import json
import logging
import re
import httpx
from typing import Optional

from models import (
    AIProvider, AIStatus, AnalysisResult,
    FeatureItem, CompetitorMention, Platform, RawReview,
    AppMetadata, RatingDistribution, SentimentDistribution,
    CountryDistribution, KeywordCount
)

logger = logging.getLogger("revixa.services.ai")

ANALYSIS_PROMPT = """Sen kıdemli ve üst düzey bir mobil uygulama pazar analistisin. Sana sağlanan kullanıcı yorumlarını büyük bir titizlikle inceleyecek ve detaylı bir pazar analiz raporu oluşturacaksın.

GÖREVİN VE KESİN KURALLARIN:
1. Yorumları derinlemesine oku. "liked" (beğenilenler), "needs_improve" (geliştirilmesi gerekenler) ve "bad" (kötü/eksik konular) kategorilerinin HER BİRİ İÇİN KESİNLİKLE EN AZ 3 İLE 6 DETAYLI ÖZELLİK/KONU MADDESİ ÇIKAR. 3'ten az madde çıkarmak kesinlikle YASAKTIR!
2. "summary": Yorumlardan yola çıkarak uygulamanın pazar performansını, kullanıcı memnuniyetini, ana zayıflıklarını ve stratejik tavsiyeleri içeren KAPSAMLI, ZENGİN VE AKICI 4-6 CÜMLELİK Türkçe bir genel değerlendirme özeti yaz. Kesinlikle yabancı/İngilizce kelime karmaşası ("issues", "positive", "fun being" vb.) kullanma; tamamen doğal Türkçe yaz.
3. "custom_focus_analysis": Kullanıcı tarafından girilen özel odak noktasını/sorusunu yorumlardaki gerçek verilerle yanıtla. Kullanıcının sorduğu spesifik konuya (donma/kasma, fiyatlandırma, zorluk seviyesi, son güncelleme vb.) dair yorumlardan tespit ettiğin somut bulguları ve yanıtı 3-5 CÜMLELİK detaylı bir paragraf olarak yaz. Özel istek yoksa yorumlardaki kritik bir odak konusunu değerlendir.
4. "example_quotes": Özellik maddelerindeki GERÇEK kullanıcı alıntılarını al ve yorumda geçen kullanıcının adını/yazarını mutlaka ekle (Örn: "\"Grafikler ve sesler harika\" — @KullaniciAdi"). Gerçek kullanıcı isimlerini verideki yazar bilgisinden doğrudan kullan.
5. "churn_risk_score": 0 ile 100 arasında uygulamanın müşteri kaybetme riski yüzdesi.
6. "version_issue_warning": "Güncellemeden sonra bozuldu/donuyor/açılmıyor" diyenler varsa 1-2 cümlelik kritik güncelleme uyarısı yaz, yoksa "".
7. "competitor_mentions": Yorumlarda adı geçen rakip uygulamaları tespit et (Örn: {"competitor_name": "Balatro", "mention_count": 5, "context": "Balatro benzeri oyun mekaniği"}).
8. "feature_rankings": Kullanıcıların en meb talep ettiği 3-5 özelliği öncelik sırasına göre Türkçe liste olarak belirt.

HER ZAMAN SADECE AŞAĞIDAKİ GEÇERLİ JSON YAPISINI DÖNDÜR:

{
  "summary": "",
  "custom_focus_analysis": "",
  "churn_risk_score": 15.0,
  "version_issue_warning": "",
  "competitor_mentions": [],
  "feature_rankings": [],
  "liked": [
    {
      "title": "",
      "description": "",
      "review_count": 1,
      "example_quotes": []
    }
  ],
  "needs_improve": [
    {
      "title": "",
      "description": "",
      "review_count": 1,
      "example_quotes": []
    }
  ],
  "bad": [
    {
      "title": "",
      "description": "",
      "review_count": 1,
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
    neu = sum(1 for r in reviews if 2.0 < r.rating < 4.0)
    neg = sum(1 for r in reviews if r.rating <= 2.0)

    pos_pct = round((pos / total) * 100, 1)
    neu_pct = round((neu / total) * 100, 1)
    neg_pct = round((neg / total) * 100, 1)

    return SentimentDistribution(
        positive_pct=pos_pct,
        neutral_pct=neu_pct,
        negative_pct=neg_pct,
        positive_count=pos,
        neutral_count=neu,
        negative_count=neg,
    )


class GeminiAnalyzer:
    def __init__(self, api_key: str):
        self.api_key = api_key

    def analyze(self, reviews: list[RawReview], app_name: str, custom_prompt_extension: Optional[str] = None) -> dict:
        try:
            from google import genai
            from google.genai import types
        except ImportError:
            raise RuntimeError("google-genai kütüphanesi yüklü değil.")

        client = genai.Client(api_key=self.api_key)
        reviews_text = _build_reviews_text(reviews)
        prompt = ANALYSIS_PROMPT + f"\nUygulama Adı: {app_name}\n"
        if custom_prompt_extension:
            prompt += f"ÖZEL ODAK NOKTASI VE TALİMAT: {custom_prompt_extension}\n"
        prompt += f"\nYorumlar:\n{reviews_text}"

        config = types.GenerateContentConfig(
            temperature=0.2,
            response_mime_type="application/json",
        )

        models_to_try = ["gemini-2.5-flash", "gemini-2.0-flash", "gemini-1.5-flash"]
        last_error = None

        for model_name in models_to_try:
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                    config=config,
                )
                if response and response.text:
                    logger.info(f"Gemini {model_name} ile başarıyla analiz yapıldı.")
                    return json.loads(response.text)
            except Exception as e:
                logger.warning(f"Gemini {model_name} hatası: {e}")
                last_error = e

        raise RuntimeError(f"Tüm Gemini modelleri başarısız oldu: {last_error}")


class OllamaAnalyzer:
    def __init__(self, base_url: str = "http://localhost:11434", model: str = "llama3.2"):
        self.base_url = base_url.rstrip("/")
        self.model = model

    def analyze(self, reviews: list[RawReview], app_name: str, custom_prompt_extension: Optional[str] = None) -> dict:
        reviews_text = _build_reviews_text(reviews, max_chars=8000)
        prompt = ANALYSIS_PROMPT + f"\nUygulama Adı: {app_name}\n"
        if custom_prompt_extension:
            prompt += f"ÖZEL ODAK NOKTASI VE TALİMAT: {custom_prompt_extension}\n"
        prompt += f"\nYorumlar:\n{reviews_text}"

        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "format": "json",
            "options": {"temperature": 0.2},
        }

        with httpx.Client(timeout=60.0) as client:
            resp = client.post(f"{self.base_url}/api/generate", json=payload)
            if resp.status_code != 200:
                raise RuntimeError(f"Ollama HTTP {resp.status_code}: {resp.text}")

            res_json = resp.json()
            raw_text = res_json.get("response", "")
            return json.loads(raw_text)


class AIService:
    """Cascade Fallback AI Router Servisi (Gemini -> Ollama -> Dynamic Rule Fallback)."""

    def __init__(self):
        self.gemini_key = os.getenv("GEMINI_API_KEY", "").strip()
        self.ollama_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434").strip()
        self.ollama_model = os.getenv("OLLAMA_MODEL", "llama3.2").strip()

    def check_status(self) -> AIStatus:
        if self.gemini_key:
            return AIStatus(
                gemini_available=True,
                ollama_available=False,
                ollama_model=self.ollama_model,
                active_provider=AIProvider.GEMINI,
            )

        try:
            with httpx.Client(timeout=2.0) as client:
                res = client.get(f"{self.ollama_url}/api/tags")
                if res.status_code == 200:
                    return AIStatus(
                        gemini_available=False,
                        ollama_available=True,
                        ollama_model=self.ollama_model,
                        active_provider=AIProvider.OLLAMA,
                    )
        except Exception:
            pass

        return AIStatus(
            gemini_available=False,
            ollama_available=False,
            ollama_model=self.ollama_model,
            active_provider=AIProvider.NONE,
        )

    def analyze(
        self,
        reviews: list[RawReview],
        meta: Optional[AppMetadata] = None,
        platform: Platform = Platform.PLAY,
        rating_dist: Optional[RatingDistribution] = None,
        country_dist: Optional[CountryDistribution] = None,
        avg_review_length: int = 0,
        keywords: Optional[list[KeywordCount]] = None,
        custom_prompt_extension: Optional[str] = None,
        app_name: Optional[str] = None,
        metadata: Optional[AppMetadata] = None,
        avg_len: Optional[int] = None,
        language: Optional[str] = "tr",
    ) -> AnalysisResult:

        actual_meta = meta or metadata or AppMetadata(title=app_name or "App")
        actual_rating_dist = rating_dist or RatingDistribution()
        actual_country_dist = country_dist or CountryDistribution()
        actual_keywords = keywords or []
        actual_avg_len = avg_review_length or avg_len or 0

        status = self.check_status()
        raw_data = None
        used_provider = AIProvider.NONE

        if status.gemini_available:
            try:
                analyzer = GeminiAnalyzer(self.gemini_key)
                raw_data = analyzer.analyze(reviews, actual_meta.title, custom_prompt_extension)
                used_provider = AIProvider.GEMINI
            except Exception as e:
                logger.warning(f"Gemini analizi başarısız oldu, Ollama deneniyor: {e}")

        if not raw_data and status.ollama_available:
            try:
                analyzer = OllamaAnalyzer(self.ollama_url, self.ollama_model)
                raw_data = analyzer.analyze(reviews, actual_meta.title, custom_prompt_extension)
                used_provider = AIProvider.OLLAMA
            except Exception as e:
                logger.warning(f"Ollama analizi başarısız oldu: {e}")

        senti_dist = calculate_sentiment_distribution(reviews)

        if not raw_data:
            logger.info("AI servisleri erişilemez; kural tabanlı dinamik analiz üretiliyor.")
            raw_data = self._rule_based_fallback(reviews, actual_meta, senti_dist, custom_prompt_extension)
            used_provider = AIProvider.NONE

        return self._format_result(
            raw_data, actual_meta, platform, actual_rating_dist,
            senti_dist, actual_country_dist, actual_avg_len,
            actual_keywords, reviews, used_provider, custom_prompt_extension
        )

    def _rule_based_fallback(
        self,
        reviews: list[RawReview],
        meta: AppMetadata,
        senti_dist: SentimentDistribution,
        custom_prompt_extension: Optional[str] = None
    ) -> dict:
        pos_revs = [r for r in reviews if r.rating >= 4.0]
        neg_revs = [r for r in reviews if r.rating <= 2.0]
        neu_revs = [r for r in reviews if 2.0 < r.rating < 4.0]

        liked = []
        for r in pos_revs[:3]:
            liked.append({
                "title": r.content[:30] + "...",
                "description": r.content,
                "review_count": 1,
                "example_quotes": [f'"{r.content}" — @{r.author}']
            })

        bad = []
        for r in neg_revs[:3]:
            bad.append({
                "title": r.content[:30] + "...",
                "description": r.content,
                "review_count": 1,
                "example_quotes": [f'"{r.content}" — @{r.author}']
            })

        improve = []
        for r in neu_revs[:3]:
            improve.append({
                "title": r.content[:30] + "...",
                "description": r.content,
                "review_count": 1,
                "example_quotes": [f'"{r.content}" — @{r.author}']
            })

        focus_text = f"Özel odak analizi: '{custom_prompt_extension}' talimatına ilişkin genel kullanıcı geri bildirimleri incelendi." if custom_prompt_extension else "Özel odak noktası belirtilmedi."

        return {
            "summary": f"{meta.title} uygulaması için toplam {len(reviews)} adet inceleme analiz edildi. Kullanıcıların %{senti_dist.positive_pct}'i olumlu geri bildirimde bulunurken, %{senti_dist.negative_pct}'i çeşitli şikayetler iletti.",
            "custom_focus_analysis": focus_text,
            "churn_risk_score": float(senti_dist.negative_pct),
            "version_issue_warning": "Son sürümlerde kullanıcı şikayetleri bulunmaktadır." if senti_dist.negative_pct > 30 else "",
            "competitor_mentions": [],
            "feature_rankings": ["Performans ve Hız İyileştirmeleri", "Kullanıcı Arayüzü Güncellemesi", "Hata Düzeltmeleri"],
            "liked": liked,
            "needs_improve": improve,
            "bad": bad
        }

    def _format_result(
        self,
        data: dict,
        meta: AppMetadata,
        platform: Platform,
        rating_dist: RatingDistribution,
        senti_dist: SentimentDistribution,
        country_dist: CountryDistribution,
        avg_review_length: int,
        keywords: list[KeywordCount],
        reviews: list[RawReview],
        provider: AIProvider,
        custom_prompt_extension: Optional[str] = None
    ) -> AnalysisResult:

        def parse_items(key: str) -> list[FeatureItem]:
            raw_list = data.get(key, [])
            items = []
            if isinstance(raw_list, list):
                for x in raw_list:
                    if isinstance(x, dict):
                        quotes = x.get("example_quotes", [])
                        if not isinstance(quotes, list):
                            quotes = [str(quotes)]
                        items.append(
                            FeatureItem(
                                title=str(x.get("title", "Konu")),
                                description=str(x.get("description", "Açıklama yok.")),
                                review_count=int(x.get("review_count", 1)),
                                example_quotes=[str(q) for q in quotes if q],
                            )
                        )
            return items

        def parse_competitors() -> list[CompetitorMention]:
            raw_comps = data.get("competitor_mentions", [])
            comps = []
            if isinstance(raw_comps, list):
                for c in raw_comps:
                    if isinstance(c, dict):
                        comps.append(
                            CompetitorMention(
                                competitor_name=str(c.get("competitor_name", "Rakip")),
                                mention_count=int(c.get("mention_count", 1)),
                                context=str(c.get("context", "")),
                            )
                        )
            return comps

        def parse_rankings() -> list[str]:
            raw_ranks = data.get("feature_rankings", [])
            if isinstance(raw_ranks, list):
                return [str(r) for r in raw_ranks if r]
            return []

        ai_churn = data.get("churn_risk_score")
        churn_risk = float(ai_churn if ai_churn is not None else senti_dist.negative_pct)

        return AnalysisResult(
            app_name=meta.title,
            platform=platform,
            metadata=meta,
            sentiment_dist=senti_dist,
            rating_dist=rating_dist,
            country_dist=country_dist,
            top_keywords=keywords,
            total_reviews=len(reviews),
            avg_review_length=avg_review_length,
            summary=str(data.get("summary", "Özet bulunamadı.")),
            custom_focus_analysis=str(data.get("custom_focus_analysis", "")) if data.get("custom_focus_analysis") else None,
            churn_risk_score=round(churn_risk, 1),
            version_issue_warning=str(data.get("version_issue_warning", "")) if data.get("version_issue_warning") else None,
            competitor_mentions=parse_competitors(),
            feature_rankings=parse_rankings(),
            liked=parse_items("liked"),
            needs_improve=parse_items("needs_improve"),
            bad=parse_items("bad"),
            ai_provider=provider,
            custom_prompt_extension=custom_prompt_extension,
        )

    def get_status(self) -> AIStatus:
        return self.check_status()


def get_router() -> AIService:
    return AIService()
