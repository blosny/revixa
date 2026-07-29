/**
 * Revixa — Minimalist Market Intelligence & PDF/MD Report Generator
 */

const API_BASE = "http://localhost:8000";

// ─── DOM References ───
const playUrlInput     = document.getElementById("play-url-input");
const appstoreUrlInput = document.getElementById("appstore-url-input");
const analyzeBtn       = document.getElementById("analyze-btn");

const reviewsGroup  = document.getElementById("reviews-group");

const loadingSection = document.getElementById("loading-section");
const errorSection   = document.getElementById("error-section");
const resultsSection = document.getElementById("results-section");

const asciiBar        = document.getElementById("ascii-bar");
const progressPercent = document.getElementById("progress-percent");
const loadingMsg     = document.getElementById("loading-msg");

const stepScraping  = document.getElementById("step-scraping");
const stepAnalyzing = document.getElementById("step-analyzing");
const stepReport    = document.getElementById("step-report");

const errorTitle  = document.getElementById("error-title");
const errorDetail = document.getElementById("error-detail");

const resultAppName = document.getElementById("result-app-name");
const resultMeta    = document.getElementById("result-meta");
const aiBadge       = document.getElementById("ai-badge");
const downloadMdBtn = document.getElementById("download-md-btn");
const downloadPdfBtn = document.getElementById("download-pdf-btn");

// Metrics DOM
const metricRating      = document.getElementById("metric-rating");
const metricRatingsCnt  = document.getElementById("metric-ratings-count");
const metricSentiment   = document.getElementById("metric-sentiment");
const metricSentiSub    = document.getElementById("metric-sentiment-sub");
const metricDeveloper   = document.getElementById("metric-developer");
const metricCategory    = document.getElementById("metric-category");
const metricLength      = document.getElementById("metric-length");

const countryDistBar  = document.getElementById("country-distribution-bar");
const keywordsListBar = document.getElementById("keywords-list-bar");
const summaryText     = document.getElementById("summary-text");

const likedList   = document.getElementById("liked-list");
const improveList = document.getElementById("improve-list");
const badList     = document.getElementById("bad-list");

const likedCount   = document.getElementById("liked-count");
const improveCount = document.getElementById("improve-count");
const badCount     = document.getElementById("bad-count");

// ─── State ───
let selectedMaxReviews = 0;
let currentReport = null;
let progressTimer = null;

// ─── Segmented Buttons ───
setupSegmentGroup(reviewsGroup, (val) => { selectedMaxReviews = parseInt(val); });

function setupSegmentGroup(groupEl, callback) {
  if (!groupEl) return;
  const buttons = groupEl.querySelectorAll(".segment-btn");
  buttons.forEach((btn) => {
    btn.addEventListener("click", () => {
      buttons.forEach(b => b.classList.remove("active"));
      btn.classList.add("active");
      callback(btn.getAttribute("data-value"));
    });
  });
}

// ─── Event Listeners ───
analyzeBtn.addEventListener("click", startAnalysis);

[playUrlInput, appstoreUrlInput].forEach(inp => {
  inp.addEventListener("keydown", (e) => {
    if (e.key === "Enter") startAnalysis();
  });
});

async function startAnalysis() {
  const playUrl = playUrlInput.value.trim();
  const appstoreUrl = appstoreUrlInput.value.trim();

  if (!playUrl && !appstoreUrl) {
    playUrlInput.focus();
    playUrlInput.style.borderColor = "#ffffff";
    setTimeout(() => { playUrlInput.style.borderColor = ""; }, 1500);
    return;
  }

  showLoading();

  try {
    const result = await analyzeApp(playUrl, appstoreUrl);
    showResults(result);
  } catch (err) {
    showError("ANALİZ BAŞARISIZ", err.message || "Bilinmeyen bir hata oluştu.");
  }
}

// ─── ASCII Bar Telemetry Renderer ───
function renderAsciiBar(percent) {
  const totalBlocks = 30;
  const filledBlocks = Math.round((percent / 100) * totalBlocks);
  const emptyBlocks = totalBlocks - filledBlocks;
  return `[ ${"█".repeat(filledBlocks)}${"░".repeat(emptyBlocks)} ]`;
}

function updateProgress(percent, message, step) {
  percent = Math.min(100, Math.max(0, percent));
  
  if (asciiBar) asciiBar.textContent = renderAsciiBar(percent);
  if (progressPercent) progressPercent.textContent = `${percent.toString().padStart(2, '0')}%`;
  if (message) loadingMsg.textContent = message;

  if (step) {
    const steps = { scraping: stepScraping, analyzing: stepAnalyzing, report: stepReport };
    const order = ["scraping", "analyzing", "report"];
    const idx   = order.indexOf(step);

    order.forEach((s, i) => {
      const el = steps[s];
      if (!el) return;
      el.classList.remove("active", "done");
      if (i < idx)   el.classList.add("done");
      if (i === idx) el.classList.add("active");
    });
  }
}

function simulateProgress() {
  let current = 5;
  updateProgress(5, "ÇOKLU_ÜLKE_YORUMLARI_TOPLANIYOR...", "scraping");

  progressTimer = setInterval(() => {
    if (current < 45) {
      current += Math.floor(Math.random() * 4) + 2;
      updateProgress(current, "MAĞAZALARDAN_METİNLİ_VERİLER_ÇEKİLİYOR...", "scraping");
    } else if (current < 88) {
      current += Math.floor(Math.random() * 2) + 1;
      updateProgress(current, "AI_DUYGU_VE_PAZAR_ANALİZİ_YAPILIYOR...", "analyzing");
    } else if (current < 98) {
      current += 1;
      updateProgress(current, "RAPOR_METRİKLERİ_YAPILANDIRILIYOR...", "report");
    }
  }, 700);
}

function stopProgress() {
  if (progressTimer) {
    clearInterval(progressTimer);
    progressTimer = null;
  }
}

// ─── API Request ───
async function analyzeApp(playUrl, appstoreUrl) {
  const body = {
    play_url: playUrl || null,
    appstore_url: appstoreUrl || null,
    url: playUrl || appstoreUrl || null,
    max_reviews: selectedMaxReviews,
  };

  simulateProgress();

  try {
    const response = await fetch(`${API_BASE}/analyze`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });

    stopProgress();

    if (!response.ok) {
      const errData = await response.json().catch(() => ({}));
      throw new Error(errData.detail || errData.error || `Sunucu hatası: ${response.status}`);
    }

    updateProgress(100, "ANALİZ_TAMAMLANDI.", "report");
    await delay(300);

    return response.json();
  } catch (err) {
    stopProgress();
    throw err;
  }
}

// ─── UI Rendering ───
function showLoading() {
  hideAll();
  loadingSection.classList.add("visible");
  analyzeBtn.disabled = true;
  analyzeBtn.textContent = "İŞLENİYOR...";
  updateProgress(0, "BAĞLANTI_KURULUYOR...", "scraping");
}

function showError(title, detail) {
  hideAll();
  errorSection.classList.add("visible");
  errorTitle.textContent = title;
  errorDetail.textContent = detail;
  resetBtn();
}

function showResults(data) {
  hideAll();
  currentReport = data;
  resultsSection.classList.add("visible");
  resetBtn();

  const meta = data.metadata || {};
  resultAppName.textContent = data.app_name || meta.title || "Bilinmeyen Uygulama";
  resultMeta.textContent = `${data.total_reviews} metinli yorum işlendi // Platform: ${(data.platform || "").toUpperCase()}`;

  aiBadge.textContent = (data.ai_provider || "AI").toUpperCase();

  // Metrics Grid
  metricRating.textContent = `⭐ ${meta.average_rating || 0.0}`;
  metricRatingsCnt.textContent = `${(meta.total_ratings || 0).toLocaleString()} toplam puanlama`;

  const sent = data.sentiment_dist || {};
  metricSentiment.textContent = `%${sent.positive_pct || 0}`;
  metricSentiSub.textContent = `Pozitif // Nötr: %${sent.neutral_pct || 0} // Negatif: %${sent.negative_pct || 0}`;

  metricDeveloper.textContent = meta.developer || "Bilinmiyor";
  metricCategory.textContent = `${meta.category || "Genel"} // Sürüm: ${meta.version || "v1.0"}`;

  metricLength.textContent = `${data.avg_review_length || 0} kr.`;

  // Country Distribution Bar
  renderCountryBar(data.country_dist || {});

  // Top Keywords
  renderKeywordsBar(data.top_keywords || []);

  // Summary
  summaryText.textContent = data.summary || "Özet bulunamadı.";

  // Categories
  renderFeatures(likedList,   likedCount,   data.liked         || []);
  renderFeatures(improveList, improveCount, data.needs_improve  || []);
  renderFeatures(badList,     badCount,     data.bad            || []);

  resultsSection.scrollIntoView({ behavior: "smooth", block: "start" });
}

function renderCountryBar(countryDist) {
  countryDistBar.innerHTML = "";
  const pcts = countryDist.percentages || {};
  const cnts = countryDist.counts || {};

  const keys = Object.keys(pcts);
  if (!keys.length) {
    countryDistBar.innerHTML = `<span class="metric-sub">// Coğrafi veri bulunamadı</span>`;
    return;
  }

  keys.forEach(code => {
    const chip = document.createElement("div");
    chip.className = "country-chip";
    chip.textContent = `${code}: %${pcts[code]} (${cnts[code]} yorum)`;
    countryDistBar.appendChild(chip);
  });
}

function renderKeywordsBar(keywords) {
  keywordsListBar.innerHTML = "";
  if (!keywords || !keywords.length) return;

  keywords.forEach(k => {
    const badge = document.createElement("div");
    badge.className = "keyword-badge";
    badge.textContent = `${k.keyword} (${k.count})`;
    keywordsListBar.appendChild(badge);
  });
}

function hideAll() {
  loadingSection.classList.remove("visible");
  errorSection.classList.remove("visible");
  resultsSection.classList.remove("visible");
}

function resetBtn() {
  analyzeBtn.disabled = false;
  analyzeBtn.textContent = "ANALİZ ET";
}

function renderFeatures(container, countBadge, features) {
  container.innerHTML = "";
  countBadge.textContent = features.length;

  if (!features.length) {
    container.innerHTML = `<div class="empty-category">// Kayıtlı özellik yok</div>`;
    return;
  }

  features.forEach((f) => {
    const item = document.createElement("div");
    item.className = "feature-item";
    item.innerHTML = `
      <div class="feature-title">
        <span>${escHtml(f.title)}</span>
        ${f.review_count ? `<span class="feature-review-count">[${f.review_count}]</span>` : ""}
      </div>
      <div class="feature-desc">${escHtml(f.description)}</div>
      ${f.example_quotes?.length ? `
        <div class="feature-quotes">
          ${f.example_quotes.map(q => `<div class="quote">"${escHtml(q)}"</div>`).join("")}
        </div>
      ` : ""}
    `;

    if (f.example_quotes?.length) {
      item.addEventListener("click", () => {
        item.classList.toggle("expanded");
      });
    }

    container.appendChild(item);
  });
}

// ─── Markdown Download ───
downloadMdBtn.addEventListener("click", () => {
  if (!currentReport) return;

  const md = currentReport.markdown_report || generateMarkdown(currentReport);
  const blob = new Blob([md], { type: "text/markdown;charset=utf-8" });
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = `revixa-${slugify(currentReport.app_name)}-${dateStr()}.md`;
  a.click();
  URL.revokeObjectURL(a.href);
});

// ─── PDF Export (Print Clean View) ───
downloadPdfBtn.addEventListener("click", () => {
  if (!currentReport) return;
  // Bütün alıntıları aç ve baskı penceresini başlat
  document.querySelectorAll(".feature-item").forEach(el => el.classList.add("expanded"));
  window.print();
});

function generateMarkdown(data) {
  return data.markdown_report || "Rapor oluşturuldu.";
}

function escHtml(str) {
  return (str || "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function slugify(str) {
  return (str || "rapor").toLowerCase().replace(/\s+/g, "-").replace(/[^a-z0-9-]/g, "").slice(0, 40);
}

function dateStr() {
  return new Date().toISOString().slice(0, 10);
}

function delay(ms) {
  return new Promise(r => setTimeout(r, ms));
}
