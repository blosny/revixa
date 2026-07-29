# REVIXA — Mobile Application Market Intelligence

REVIXA is an automated market research and sentiment analysis engine designed to extract, analyze, and structure user feedback from Google Play Store and Apple App Store.

It utilizes an AI Router mechanism combining Google Gemini Flash with local Ollama fallback to categorize user sentiment, geographic telemetry, rating distributions, and product feature requests without service interruption.

---

## // Purpose

The primary goal of REVIXA is to provide developers, product managers, and market researchers with instant, actionable product insights derived directly from end-user reviews across global application stores.

---

## // Core Capabilities

- **Multi-Store & Dual Link Support**: Simultaneously ingests user reviews from Google Play Store and Apple App Store.
- **Geographic Telemetry**: Tracks country distribution percentages across international markets (TR, US, DE, GB, FR, BR, IN).
- **AI Fallback Router**: Primary analysis executed via Gemini 2.0 Flash; automatically switches to local Ollama (Llama 3.2) if rate limits occur.
- **Market Metrics**: Computes average review character lengths, star rating distributions, and keyword frequency tags.
- **Structured Export**: Generates printable PDF documents and Markdown (.md) reports.
- **Minimalist Interface**: Zero-clutter, monochrome user interface with custom segmented controls.

---

## // Architecture & File Structure

```
revixa/
├── backend/
│   ├── main.py          # FastAPI application & REST endpoints
│   ├── analyzer.py      # AI Router (Gemini -> Ollama) & report generator
│   ├── scraper.py       # Multi-country review & metadata extraction engine
│   ├── models.py        # Pydantic data schemas & statistics models
│   └── requirements.txt # Python dependencies
├── frontend/
│   ├── index.html       # Minimalist HTML interface
│   ├── style.css        # Monochrome design system & print layout
│   └── app.js           # Client-side telemetry, API fetch & export logic
├── debug_reviews.py     # Review extraction debug utility
├── test_scraper.py      # Scraper validation script
├── test_analyzer.py     # AI Router fallback test script
├── .env                 # Environment configuration
├── .gitignore           # Git exclusion rules
└── README.md            # System documentation
```

---

## // Tech Stack

- **Backend**: Python 3.13, FastAPI, Pydantic, HTTPX, google-genai
- **Frontend**: HTML5, Vanilla JavaScript, CSS3 (Monochrome & Print Layout)
- **AI Engines**: Google Gemini 2.0 Flash, Ollama (Llama 3.2)

---

## // Quick Start

### 1. Environment Setup

Copy `.env.example` to `.env` and set your configuration:

```bash
GEMINI_API_KEY=your_gemini_api_key
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2
```

### 2. Backend Server Initialization

```bash
# Create virtual environment & install dependencies
python -m venv venv
venv\Scripts\activate
pip install -r backend/requirements.txt

# Start FastAPI server
uvicorn backend.main:app --port 8000
```

### 3. Frontend Execution

Open `frontend/index.html` in any web browser.

---

## // License & Credits

MIT License. Designed and developed by **blosny**.
