/**
 * Revixa — Frontend Logic
 * ========================
 * Backend API ile iletişim, UI state yönetimi,
 * mock data ile test modu.
 */

const API_BASE = "http://localhost:8000";

// ─── DOM References ───
const urlInput       = document.getElementById("url-input");
const analyzeBtn     = document.getElementById("analyze-btn");
const platformSelect = document.getElementById("platform-select");
const reviewsSelect  = document.getElementById("reviews-select");

const loadingSection = document.getElementById("loading-section");
const errorSection   = document.getElementById("error-section");
const resultsSection = document.getElementById("results-section");

const stepScraping  = document.getElementById("step-scraping");
const stepAnalyzing = document.getElementById("step-analyzing");
const stepReport    = document.getElementById("step-report");
const loadingMsg    = document.getElementById("loading-msg");

const errorTitle  = document.getElementById("error-title");
const errorDetail = document.getElementById("error-detail");

const resultAppName = document.getElementById("result-app-name");
const resultMeta    = document.getElementById("result-meta");
const platformIcon  = document.getElementById("platform-icon");
const aiBadge       = document.getElementById("ai-badge");
const downloadBtn   = document.getElementById("download-btn");
const summaryText   = document.getElementById("summary-text");

const likedList   = document.getElementById("liked-list");
const improveList = document.getElementById("improve-list");
const badList     = document.getElementById("bad-list");

const likedCount   = document.getElementById("liked-count");
const improveCount = document.getElementById("improve-count");
const badCount     = document.getElementById("bad-count");

// ─── State ───
let currentReport = null;

// ─── Analyze Button Click ───
analyzeBtn.addEventListener("click", startAnalysis);

urlInput.addEventListener("keydown", (e) => {
  if (e.key === "Enter") startAnalysis();
});

async function startAnalysis() {
  const url = urlInput.value.trim();

  if (!url) {
    urlInput.focus();
    urlInput.style.borderColor = "rgba(239,68,68,0.5)";
    setTimeout(() => { urlInput.style.borderColor = ""; }, 1500);
    return;
  }

  if (!url.includes("play.google.com") && !url.includes("apps.apple.com")) {
    showError(
      "Geçersiz URL",
      "Lütfen Google Play Store veya Apple App Store URL'si girin."
    );
    return;
  }

  showLoading();

  try {
    const result = await analyzeApp(url);
    showResults(result);
  } catch (err) {
    showError("Analiz başarısız", err.message || "Bilinmeyen hata oluştu.");
  }
}

// ─── API Call ───
async function analyzeApp(url) {
  const body = {
    url: url,
    platform: platformSelect.value,
    max_reviews: parseInt(reviewsSelect.value),
  };

  setLoadingStep("scraping");
  setLoadingMsg("Yorumlar çekiliyor...");

  // Simülasyon: adımlar arasında geçiş (gerçekte backend halleder)
  await delay(800);
  setLoadingStep("analyzing");
  setLoadingMsg("AI yorumları analiz ediyor...");

  const response = await fetch(`${API_BASE}/analyze`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });

  if (!response.ok) {
    const errData = await response.json().catch(() => ({}));
    throw new Error(errData.detail || errData.error || `Sunucu hatası: ${response.status}`);
  }

  setLoadingStep("report");
  setLoadingMsg("Rapor oluşturuluyor...");
  await delay(300);

  return response.json();
}

// ─── UI State ───
function showLoading() {
  hideAll();
  loadingSection.classList.add("visible");
  analyzeBtn.disabled = true;
  analyzeBtn.innerHTML = '<span class="btn-icon">⏳</span> Analiz ediliyor...';

  // Adımları sıfırla
  [stepScraping, stepAnalyzing, stepReport].forEach(s => {
    s.classList.remove("active", "done");
  });
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

  // App info
  resultAppName.textContent = data.app_name || "Bilinmeyen Uygulama";
  resultMeta.textContent = `${data.total_reviews} yorum analiz edildi`;
  platformIcon.textContent = data.platform === "play" ? "▶" : "";

  // AI badge
  if (data.ai_provider === "ollama") {
    aiBadge.className = "ai-badge ollama";
    aiBadge.textContent = "🦙 Ollama";
  } else {
    aiBadge.className = "ai-badge gemini";
    aiBadge.textContent = "🌟 Gemini";
  }

  // Summary
  summaryText.textContent = data.summary || "Özet oluşturulamadı.";

  // Categories
  renderFeatures(likedList,   likedCount,   data.liked         || []);
  renderFeatures(improveList, improveCount, data.needs_improve  || []);
  renderFeatures(badList,     badCount,     data.bad            || []);

  // Scroll to results
  resultsSection.scrollIntoView({ behavior: "smooth", block: "start" });
}

function hideAll() {
  loadingSection.classList.remove("visible");
  errorSection.classList.remove("visible");
  resultsSection.classList.remove("visible");
}

function resetBtn() {
  analyzeBtn.disabled = false;
  analyzeBtn.innerHTML = '<span class="btn-icon">⚡</span> Analiz Et';
}

// ─── Loading Steps ───
function setLoadingStep(step) {
  const steps = { scraping: stepScraping, analyzing: stepAnalyzing, report: stepReport };
  const order = ["scraping", "analyzing", "report"];
  const idx   = order.indexOf(step);

  order.forEach((s, i) => {
    const el = steps[s];
    el.classList.remove("active", "done");
    if (i < idx)  el.classList.add("done");
    if (i === idx) el.classList.add("active");
  });
}

function setLoadingMsg(msg) {
  loadingMsg.textContent = msg;
}

// ─── Feature Rendering ───
function renderFeatures(container, countBadge, features) {
  container.innerHTML = "";
  countBadge.textContent = features.length;

  if (!features.length) {
    container.innerHTML = `<div class="empty-category">Özellik bulunamadı</div>`;
    return;
  }

  features.forEach((f) => {
    const item = document.createElement("div");
    item.className = "feature-item";
    item.innerHTML = `
      <div class="feature-title">
        ${escHtml(f.title)}
        ${f.review_count ? `<span class="feature-review-count">${f.review_count} yorum</span>` : ""}
      </div>
      <div class="feature-desc">${escHtml(f.description)}</div>
      ${f.example_quotes?.length ? `
        <div class="feature-quotes">
          ${f.example_quotes.map(q => `<div class="quote">"${escHtml(q)}"</div>`).join("")}
        </div>
      ` : ""}
    `;

    // Expand/collapse on click (to show quotes)
    if (f.example_quotes?.length) {
      item.style.cursor = "pointer";
      item.addEventListener("click", () => {
        item.classList.toggle("expanded");
      });
    }

    container.appendChild(item);
  });
}

// ─── Download Report ───
downloadBtn.addEventListener("click", () => {
  if (!currentReport) return;

  const md = currentReport.markdown_report || generateMarkdown(currentReport);
  const blob = new Blob([md], { type: "text/markdown;charset=utf-8" });
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = `revixa-${slugify(currentReport.app_name)}-${dateStr()}.md`;
  a.click();
  URL.revokeObjectURL(a.href);
});

function generateMarkdown(data) {
  const lines = [
    `# Revixa Analiz Raporu: ${data.app_name}`,
    ``,
    `**Platform:** ${data.platform}  `,
    `**Analiz edilen yorum:** ${data.total_reviews}  `,
    `**AI:** ${data.ai_provider}  `,
    `**Tarih:** ${new Date().toLocaleDateString("tr-TR")}`,
    ``,
    `---`,
    ``,
    `## 📝 Genel Özet`,
    ``,
    data.summary,
    ``,
    `---`,
    ``,
    `## 🟢 Beğenilen Özellikler`,
    ``,
    ...formatFeaturesMd(data.liked),
    ``,
    `## 🟡 Geliştirilmesi Gereken`,
    ``,
    ...formatFeaturesMd(data.needs_improve),
    ``,
    `## 🔴 Kötü / Eksik Özellikler`,
    ``,
    ...formatFeaturesMd(data.bad),
  ];
  return lines.join("\n");
}

function formatFeaturesMd(features) {
  if (!features?.length) return ["_Özellik bulunamadı_"];
  return features.flatMap(f => [
    `### ${f.title} _(${f.review_count} yorum)_`,
    `${f.description}`,
    ...(f.example_quotes?.length
      ? [``, `> ${f.example_quotes.join("\n> ")}`]
      : []),
    ``,
  ]);
}

// ─── Utils ───
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

// ─── MOCK TEST (API hazır olmadan UI'ı test etmek için) ───
// Konsola: window.testMock() yaz ve Enter'a bas
window.testMock = function () {
  const mockData = {
    app_name: "Acaba Ne Yesem? - Tarif Bulucu",
    platform: "play",
    total_reviews: 6,
    ai_provider: "gemini",
    summary: "Uygulama, kullanıcılar tarafından genel olarak olumlu karşılanmaktadır. Evdeki malzemelere göre tarif önerme özelliği öne çıkan en sevilen unsurdur. Kullanıcılar arayüzü sade ve kullanışlı bulmaktadır. Bununla birlikte, doğrudan tarif arama özelliğinin eksikliği sıkça dile getirilmektedir.",
    liked: [
      {
        title: "Malzemeye göre tarif önerisi",
        description: "Kullanıcılar evdeki malzemelere göre tarif önerisi yapan sistemi çok başarılı buluyor.",
        review_count: 3,
        example_quotes: [
          "Sadece evdeki malzemeler ile yemek yapmak için kullanmıyorum, market alışverişi yapmadan önce de kullanıyorum.",
          "Çok beğendim, öğrenci evinde birebir."
        ]
      },
      {
        title: "Kullanıcı Dostu Arayüz",
        description: "Uygulamanın sade ve anlaşılır arayüzü kullanıcılar tarafından beğenilmektedir.",
        review_count: 2,
        example_quotes: ["Kaliteli ve özenli bir uygulama, çok beğendim."]
      }
    ],
    needs_improve: [
      {
        title: "Tarif Arama Özelliği",
        description: "Kullanıcılar doğrudan tarif adı ile arama yapabilmek istediklerini belirtiyor.",
        review_count: 1,
        example_quotes: ["Direkt tarif arama kısmı da eklenirse süper olur."]
      }
    ],
    bad: [
      {
        title: "İçerik Genişliği",
        description: "Bazı kullanıcılar uygulamanın daha fazla tarif içermesi gerektiğini düşünüyor.",
        review_count: 1,
        example_quotes: ["Faydalı bir uygulama, gelişmesi lazım."]
      }
    ],
    markdown_report: ""
  };

  showResults(mockData);
};

console.log("💡 UI'ı test etmek için konsola: testMock() yazın");
