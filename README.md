# 🔭 Revixa

> **Mobil uygulama yorumlarını yapay zeka ile analiz et — pazar içgörüsünü anında elde et.**

Revixa, Google Play Store ve Apple App Store URL'lerinden uygulama yorumlarını otomatik olarak çekip, Gemini AI (veya yerel Ollama) ile analiz ederek üç kategoride detaylı rapor üreten bir otomasyon aracıdır.

---

## ✨ Özellikler

- 🕷️ **Otomatik Review Çekme** — Play Store & App Store URL'si gir, gerisini Revixa halleder
- 🧠 **AI Destekli Analiz** — Gemini 1.5 Flash ile akıllı kategorizasyon
- 🔄 **Otomatik Fallback** — Gemini limiti dolunca Ollama'ya geçer (kesintisiz çalışır)
- 📊 **3 Kategori Raporu** — Beğenilen / Geliştirilmesi Gereken / Kötü özellikler
- 📥 **Rapor İndirme** — Markdown formatında indirilebilir analiz
- 🎨 **Modern Web UI** — Glassmorphism dark mode arayüz

---

## 🚀 Hızlı Başlangıç

### Gereksinimler
- Python 3.10+
- Gemini API key → [aistudio.google.com/apikey](https://aistudio.google.com/apikey)
- *(İsteğe bağlı)* Ollama → [ollama.com/download](https://ollama.com/download)

### Kurulum

```bash
# 1. Repoyu klonla
git clone https://github.com/blosny/revixa.git
cd revixa

# 2. Sanal ortam oluştur
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux

# 3. Bağımlılıkları yükle
pip install -r backend/requirements.txt

# 4. API key ayarla
cp .env.example .env
# .env dosyasını aç ve GEMINI_API_KEY'i gir

# 5. Çalıştır
uvicorn backend.main:app --reload --port 8000
```

### Ollama Kurulumu (İsteğe Bağlı — Fallback için)

```bash
# 1. Ollama'yı indir: https://ollama.com/download
# 2. Modeli indir:
ollama pull llama3.2
# 3. Ollama'yı çalıştır (arka planda otomatik başlar)
```

---

## 📊 Nasıl Çalışır?

```
1. Web arayüzüne Play Store veya App Store URL'si gir
2. Revixa ilgili platformdan yorumları çeker (max 200)
3. Yorumlar AI'ya gönderilir (önce Gemini, yoksa Ollama)
4. AI yorumları 3 kategoriye ayırır:
   🟢 Beğenilen Özellikler
   🟡 Geliştirilmesi Gerekenler
   🔴 Kötü / Eksik Özellikler
5. Rapor web arayüzünde gösterilir ve indirilebilir
```

---

## 🤖 AI Fallback Mekanizması

```
İstek → Gemini API
            ↓
       Başarılı? ✅ → Gemini sonucu kullan
       Rate Limit? ❌ → Ollama'ya geç (localhost:11434)
                           ↓
                    Ollama kurulu mu? ✅ → Ollama sonucu kullan
                    Kurulu değil? ❌ → Kullanıcıya bildir
```

---

## 📁 Proje Yapısı

```
revixa/
├── backend/
│   ├── main.py          # FastAPI sunucu
│   ├── scraper.py       # Review çekme motoru
│   ├── analyzer.py      # AI Router (Gemini + Ollama)
│   ├── models.py        # Veri modelleri
│   └── requirements.txt
├── frontend/
│   ├── index.html       # Ana arayüz
│   ├── style.css        # Glassmorphism UI
│   └── app.js           # Frontend logic
├── .env.example         # API key şablonu
└── README.md
```

---

## 🛠️ Teknoloji Stack

| Katman | Teknoloji |
|--------|-----------|
| Backend | Python, FastAPI |
| Review Scraping | google-play-scraper, app-store-scraper |
| AI (Birincil) | Google Gemini 1.5 Flash |
| AI (Yedek) | Ollama (llama3.2 / mistral) |
| Frontend | HTML, CSS, Vanilla JS |

---

## 📄 Lisans

MIT License — Özgürce kullan, geliştir, paylaş.
