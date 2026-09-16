# REVIXA FRONTEND VE UI/UX TASARIM DOKÜMANI

## 1. Tasarım Felsefesi: Pure Black & White Minimalist

REVIXA ön yüzü, dikkat dağıtmayan, yüksek kontrastlı ve veri odaklı bir **Pure Black & White** tasarım sistemine sahiptir.

- **Renk Paleti**: `#000000` (Ana Arka Plan), `#09090b` (Kart Arka Planları), `#ffffff` (Metin ve Vurgular), `#27272a` (Kenarlıklar).
- **Tipografi**: 'Inter' (Ana Metin) ve 'JetBrains Mono' (Kod & Metrik Metinleri).

---

## 2. Arayüz Bileşenleri ve Render Akışı (`frontend/app.js`)

```
[ Kullanıcı URL Girdisi ]
         │
         ▼
[ Telemetri Yükleme Ekranı (ASCII Bar) ]
         │
         ▼
[ Rapor Render Yapısı (renderResults) ]
         ├──► Ortalama Puan & Duygu Dağılımı
         ├──► Churn Risk Skoru Kartı
         ├──► Güncelleme / Sürüm Uyarısı Alert Kartı
         ├──► Stratejik İçgörüler Izgarası (Özellik Sıralaması + Rakipler)
         ├──► Coğrafi Ülke Dağılımı ve Kelime Bulutu
         └──► İndirilebilir Markdown (.md) Raporu
```

---

## 3. Çoklu Dil Desteği (i18n)

Arayüz Türkçe (`TR`) ve İngilizce (`EN`) olmak üzere dinamik dil anahtarlamasına sahiptir. Kullanıcı dil değiştirdiğinde `app.js` içerisindeki sözlük yapısı tüm DOM etiketlerini anında günceller.
