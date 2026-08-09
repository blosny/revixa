/**
 * Revixa v2 — Minimalist Market Intelligence & PDF/MD Report Generator
 * Auth, Custom Prompt Extension, and Saved Apps Dashboard Integration.
 */

const API_BASE = "http://localhost:8000";

// DOM References
const playUrlInput      = document.getElementById("play-url-input");
const appstoreUrlInput  = document.getElementById("appstore-url-input");
const customPromptInput = document.getElementById("custom-prompt-input");

const analyzeBtn        = document.getElementById("analyze-btn");
const clearCacheBtn     = document.getElementById("clear-cache-btn");
const reviewsGroup      = document.getElementById("reviews-group");

const loadingSection    = document.getElementById("loading-section");
const errorSection      = document.getElementById("error-section");
const resultsSection    = document.getElementById("results-section");

const asciiBar         = document.getElementById("ascii-bar");
const progressPercent  = document.getElementById("progress-percent");
const loadingMsg      = document.getElementById("loading-msg");

const stepScraping   = document.getElementById("step-scraping");
const stepAnalyzing  = document.getElementById("step-analyzing");
const stepReport     = document.getElementById("step-report");

const errorTitle   = document.getElementById("error-title");
const errorDetail  = document.getElementById("error-detail");
const toastMsg     = document.getElementById("toast-message");

const resultAppName   = document.getElementById("result-app-name");
const resultMeta      = document.getElementById("result-meta");
const aiBadge         = document.getElementById("ai-badge");
const downloadMdBtn   = document.getElementById("download-md-btn");
const saveAppBtn      = document.getElementById("save-app-btn");

// Auth DOM
const openAuthModalBtn = document.getElementById("open-auth-modal-btn");
const closeAuthModalBtn = document.getElementById("close-auth-modal-btn");
const authModal        = document.getElementById("auth-modal");
const authForm         = document.getElementById("auth-form");
const authEmail        = document.getElementById("auth-email");
const authPassword     = document.getElementById("auth-password");
const authSubmitBtn    = document.getElementById("auth-submit-btn");

const tabLoginBtn      = document.getElementById("tab-login-btn");
const tabRegisterBtn   = document.getElementById("tab-register-btn");

const loggedOutView    = document.getElementById("logged-out-view");
const loggedInView     = document.getElementById("logged-in-view");
const userEmailDisplay = document.getElementById("user-email-display");
const logoutBtn        = document.getElementById("logout-btn");

// Saved Apps DOM
const openAppsModalBtn  = document.getElementById("open-apps-modal-btn");
const closeAppsModalBtn = document.getElementById("close-apps-modal-btn");
const appsModal         = document.getElementById("apps-modal");
const savedAppsList     = document.getElementById("saved-apps-list");

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

// State
let selectedMaxReviews = 0;
let currentReport = null;
let progressTimer = null;
let isRegisterTab = false;
let currentUser = null;

// Init Auth Check
checkAuth();

// Segmented Buttons
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

// Event Listeners
analyzeBtn.addEventListener("click", startAnalysis);

if (clearCacheBtn) {
  clearCacheBtn.addEventListener("click", handleClearCache);
}

[playUrlInput, appstoreUrlInput, customPromptInput].forEach(inp => {
  inp.addEventListener("keydown", (e) => {
    if (e.key === "Enter") startAnalysis();
  });
});

// Auth Modal Listeners
if (openAuthModalBtn) openAuthModalBtn.addEventListener("click", () => authModal.classList.remove("hidden"));
if (closeAuthModalBtn) closeAuthModalBtn.addEventListener("click", () => authModal.classList.add("hidden"));
if (logoutBtn) logoutBtn.addEventListener("click", handleLogout);

tabLoginBtn.addEventListener("click", () => setAuthTab(false));
tabRegisterBtn.addEventListener("click", () => setAuthTab(true));

authForm.addEventListener("submit", handleAuthSubmit);

// Saved Apps Modal Listeners
if (openAppsModalBtn) openAppsModalBtn.addEventListener("click", openSavedAppsModal);
if (closeAppsModalBtn) closeAppsModalBtn.addEventListener("click", () => appsModal.classList.add("hidden"));
if (saveAppBtn) saveAppBtn.addEventListener("click", handleSaveCurrentApp);

function setAuthTab(isRegister) {
  isRegisterTab = isRegister;
  if (isRegister) {
    tabRegisterBtn.classList.add("active");
    tabLoginBtn.classList.remove("active");
    authSubmitBtn.textContent = "KAYIT OL";
  } else {
    tabLoginBtn.classList.add("active");
    tabRegisterBtn.classList.remove("active");
    authSubmitBtn.textContent = "GİRİŞ YAP";
  }
}

async function checkAuth() {
  const token = localStorage.getItem("revixa_token");
  if (!token) {
    setLoggedOutUI();
    return;
  }

  try {
    const res = await fetch(`${API_BASE}/auth/me`, {
      headers: { "Authorization": `Bearer ${token}` }
    });
    if (res.ok) {
      currentUser = await res.json();
      setLoggedInUI(currentUser.email);
    } else {
      handleLogout();
    }
  } catch (err) {
    setLoggedOutUI();
  }
}

function setLoggedInUI(email) {
  loggedOutView.classList.add("hidden");
  loggedInView.classList.remove("hidden");
  userEmailDisplay.textContent = email;
  if (saveAppBtn) saveAppBtn.classList.remove("hidden");
}

function setLoggedOutUI() {
  currentUser = null;
  loggedOutView.classList.remove("hidden");
  loggedInView.classList.add("hidden");
  if (saveAppBtn) saveAppBtn.classList.add("hidden");
}

function handleLogout() {
  localStorage.removeItem("revixa_token");
  setLoggedOutUI();
  showToast("ÇIKIŞ YAPILDI");
}

async function handleAuthSubmit(e) {
  e.preventDefault();
  const email = authEmail.value.trim();
  const password = authPassword.value.trim();

  if (!email || !password) return;

  const endpoint = isRegisterTab ? "/auth/register" : "/auth/login";

  try {
    const res = await fetch(`${API_BASE}${endpoint}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password })
    });

    const data = await res.json();

    if (!res.ok) {
      showToast(`HATA: ${data.detail || "İşlem başarısız"}`);
      return;
    }

    if (isRegisterTab) {
      showToast("KAYIT BAŞARILI! ŞİMDİ GİRİŞ YAPABİLİRSİNİZ.");
      setAuthTab(false);
    } else {
      localStorage.setItem("revixa_token", data.access_token);
      authModal.classList.add("hidden");
      showToast("GİRİŞ BAŞARILI!");
      checkAuth();
    }
  } catch (err) {
    showToast("SUNUCU İLE İLETİŞİM KURULAMADI");
  }
}

async function openSavedAppsModal() {
  appsModal.classList.remove("hidden");
  savedAppsList.innerHTML = '<p class="modal-subtitle">Uygulamalar yükleniyor...</p>';

  const token = localStorage.getItem("revixa_token");
  try {
    const res = await fetch(`${API_BASE}/user/apps`, {
      headers: { "Authorization": `Bearer ${token}` }
    });
    const apps = await res.json();

    if (apps.length === 0) {
      savedAppsList.innerHTML = '<p class="modal-subtitle">Henüz kaydedilmiş uygulamanız yok.</p>';
      return;
    }

    savedAppsList.innerHTML = "";
    apps.forEach(app => {
      const item = document.createElement("div");
      item.className = "saved-app-item";
      item.innerHTML = `
        <span class="saved-app-title">${app.title}</span>
        <div class="saved-app-actions">
          <button class="app-load-btn" data-play="${app.play_url || ''}" data-appstore="${app.appstore_url || ''}">ANALİZ ET</button>
          <button class="app-delete-btn" data-id="${app.id}">SİL</button>
        </div>
      `;
      savedAppsList.appendChild(item);
    });

    // Add listeners to dynamic elements
    savedAppsList.querySelectorAll(".app-load-btn").forEach(btn => {
      btn.addEventListener("click", () => {
        playUrlInput.value = btn.getAttribute("data-play") || "";
        appstoreUrlInput.value = btn.getAttribute("data-appstore") || "";
        appsModal.classList.add("hidden");
        startAnalysis();
      });
    });

    savedAppsList.querySelectorAll(".app-delete-btn").forEach(btn => {
      btn.addEventListener("click", async () => {
        const appId = btn.getAttribute("data-id");
        await fetch(`${API_BASE}/user/apps/${appId}`, {
          method: "DELETE",
          headers: { "Authorization": `Bearer ${token}` }
        });
        showToast("UYGULAMA SİLİNDİ");
        openSavedAppsModal();
      });
    });

  } catch (err) {
    savedAppsList.innerHTML = '<p class="modal-subtitle">Uygulamalar yüklenirken hata oluştu.</p>';
  }
}

async function handleSaveCurrentApp() {
  if (!currentReport) return;

  const token = localStorage.getItem("revixa_token");
  if (!token) {
    showToast("LÜTFEN ÖNCE GİRİŞ YAPIN");
    return;
  }

  const payload = {
    title: currentReport.app_name,
    play_url: playUrlInput.value.trim() || null,
    appstore_url: appstoreUrlInput.value.trim() || null
  };

  try {
    const res = await fetch(`${API_BASE}/user/apps`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${token}`
      },
      body: JSON.stringify(payload)
    });

    if (res.ok) {
      showToast("UYGULAMA PANELİNİZE KAYDEDİLDİ!");
    } else {
      const err = await res.json();
      showToast(`HATA: ${err.detail}`);
    }
  } catch (err) {
    showToast("SUNUCU BAĞLANTISI BAŞARISIZ");
  }
}

async function handleClearCache() {
  try {
    const res = await fetch(`${API_BASE}/cache`, { method: "DELETE" });
    const data = await res.json();
    showToast(`VERİTABANI ÖNBELLEĞİ TEMİZLENDİ (${data.deleted_entries || 0} KAYIT SILINDI)`);
  } catch (err) {
    showToast("ÖNBELLEK TEMİZLENEMEDİ (SUNUCU BAĞLANTISI YOK)");
  }
}

async function startAnalysis() {
  const playUrl = playUrlInput.value.trim();
  const appstoreUrl = appstoreUrlInput.value.trim();
  const customPrompt = customPromptInput.value.trim();

  if (!playUrl && !appstoreUrl) {
    showToast("LÜTFEN EN AZ BİR MAĞAZA URL'Sİ GİRİN");
    return;
  }

  resetUI();
  showLoading();

  const payload = {
    play_url: playUrl || null,
    appstore_url: appstoreUrl || null,
    url: playUrl || appstoreUrl,
    platform: (playUrl && appstoreUrl) ? "both" : "auto",
    max_reviews: selectedMaxReviews,
    custom_prompt_extension: customPrompt || null
  };

  try {
    const response = await fetch(`${API_BASE}/analyze`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });

    const data = await response.json();

    if (!response.ok) {
      hideLoading();
      showError("ANALİZ BAŞARISIZ", data.detail || "Yorumlar işlenirken beklenmeyen bir hata oluştu.");
      return;
    }

    currentReport = data;
    finishLoading(() => {
      renderResults(data);
    });

  } catch (err) {
    hideLoading();
    showError("SUNUCU BAĞLANTI HATASI", "Backend sunucusuna ulaşılamıyor (http://localhost:8000). Sunucunun çalıştığından emin olun.");
  }
}

function resetUI() {
  errorSection.style.display = "none";
  resultsSection.style.display = "none";
}

function showLoading() {
  loadingSection.style.display = "block";
  stepScraping.classList.add("active");
  stepAnalyzing.classList.remove("active");
  stepReport.classList.remove("active");

  let pct = 0;
  progressPercent.textContent = "00%";
  loadingMsg.textContent = "ÇOKLU ÜLKE PAZAR SCRAPING BAŞLATILIYOR...";
  updateAsciiBar(0);

  if (progressTimer) clearInterval(progressTimer);

  progressTimer = setInterval(() => {
    pct += 2;
    if (pct <= 40) {
      loadingMsg.textContent = "ÇOKLU ÜLKE PAZAR SCRAPING BAŞLATILIYOR...";
      stepScraping.classList.add("active");
    } else if (pct <= 85) {
      loadingMsg.textContent = "AI DUYGU, CHURN VE PAZAR ANALİZİ YAPILIYOR...";
      stepScraping.classList.remove("active");
      stepAnalyzing.classList.add("active");
    } else if (pct < 98) {
      loadingMsg.textContent = "PAZAR TELEMETRİ YAPILANDIRMASI TAMAMLANIYOR...";
      stepAnalyzing.classList.remove("active");
      stepReport.classList.add("active");
    }

    if (pct >= 98) {
      pct = 98;
      clearInterval(progressTimer);
    }

    progressPercent.textContent = `${pct.toString().padStart(2, '0')}%`;
    updateAsciiBar(pct);
  }, 200);
}

function finishLoading(callback) {
  if (progressTimer) clearInterval(progressTimer);

  progressPercent.textContent = "100%";
  updateAsciiBar(100);
  loadingMsg.textContent = "ANALİZ BAŞARISIYLA TAMAMLANDI.";
  stepReport.classList.add("active");

  setTimeout(() => {
    loadingSection.style.display = "none";
    if (callback) callback();
  }, 400);
}

function hideLoading() {
  if (progressTimer) clearInterval(progressTimer);
  loadingSection.style.display = "none";
}

function updateAsciiBar(percent) {
  const totalBlocks = 40;
  const filledBlocks = Math.round((percent / 100) * totalBlocks);
  const emptyBlocks = totalBlocks - filledBlocks;
  asciiBar.textContent = `[ ${"█".repeat(filledBlocks)}${"░".repeat(emptyBlocks)} ]`;
}

function showError(title, detail) {
  errorTitle.textContent = title;
  errorDetail.textContent = detail;
  errorSection.style.display = "block";
}

function showToast(msg) {
  toastMsg.textContent = msg;
  toastMsg.classList.add("show");
  setTimeout(() => {
    toastMsg.classList.remove("show");
  }, 3000);
}

const customFocusCard = document.getElementById("custom-focus-card");
const customFocusText = document.getElementById("custom-focus-text");

function renderResults(data) {
  resultAppName.textContent = data.app_name.toUpperCase();
  resultMeta.textContent = `${data.metadata.total_ratings.toLocaleString()} Mağaza Oylaması • ${data.total_reviews} İnceleme • Platform: ${data.platform.toUpperCase()}`;

  aiBadge.textContent = data.ai_provider.toUpperCase();

  metricRating.textContent = `${data.metadata.average_rating} / 5.0`;
  metricRatingsCnt.textContent = `${data.metadata.total_ratings.toLocaleString()} toplam oylama`;

  metricSentiment.textContent = `%${data.sentiment_dist.positive_pct}`;
  metricSentiSub.textContent = `Pozitif: %${data.sentiment_dist.positive_pct} • Nötr: %${data.sentiment_dist.neutral_pct} • Negatif: %${data.sentiment_dist.negative_pct}`;

  metricDeveloper.textContent = data.metadata.developer;
  metricCategory.textContent = `${data.metadata.category} • Sürüm: ${data.metadata.version}`;

  metricLength.textContent = `${data.avg_review_length} karakter`;

  // Render Custom Focus Card
  if (data.custom_focus_analysis && typeof data.custom_focus_analysis === "string" && data.custom_focus_analysis.trim() !== "") {
    customFocusText.textContent = data.custom_focus_analysis;
    customFocusCard.classList.remove("hidden");
  } else {
    customFocusCard.classList.add("hidden");
  }

  // Render Countries
  countryDistBar.innerHTML = "";
  if (data.country_dist && data.country_dist.percentages) {
    Object.entries(data.country_dist.percentages).forEach(([code, pct]) => {
      const cnt = data.country_dist.counts[code] || 0;
      const pill = document.createElement("div");
      pill.className = "country-pill";
      pill.textContent = `${code}: %${pct} (${cnt} yorum)`;
      countryDistBar.appendChild(pill);
    });
  }

  // Render Keywords
  keywordsListBar.innerHTML = "";
  if (data.top_keywords) {
    data.top_keywords.forEach(kw => {
      const tag = document.createElement("div");
      tag.className = "keyword-tag";
      tag.textContent = `${kw.keyword} (${kw.count})`;
      keywordsListBar.appendChild(tag);
    });
  }

  summaryText.textContent = data.summary || "Özet bulunamadı.";

  renderCategoryList(likedList, data.liked);
  renderCategoryList(improveList, data.needs_improve);
  renderCategoryList(badList, data.bad);

  likedCount.textContent   = data.liked ? data.liked.length : 0;
  improveCount.textContent = data.needs_improve ? data.needs_improve.length : 0;
  badCount.textContent     = data.bad ? data.bad.length : 0;

  downloadMdBtn.onclick = () => downloadMarkdownReport(data);

  resultsSection.style.display = "block";
  resultsSection.scrollIntoView({ behavior: "smooth" });
}

function renderCategoryList(containerEl, items) {
  containerEl.innerHTML = "";
  if (!items || items.length === 0) {
    containerEl.innerHTML = '<div class="feature-item-desc">Öne çıkan kayıt bulunamadı.</div>';
    return;
  }

  items.forEach(item => {
    const el = document.createElement("div");
    el.className = "feature-item";

    let quotesHtml = "";
    if (item.example_quotes && item.example_quotes.length > 0) {
      quotesHtml = item.example_quotes.map(q => {
        const cleanQuote = q.replace(/^["'\s]+|["'\s]+$/g, '').trim();
        return cleanQuote ? `<div class="feature-quote">"${cleanQuote}"</div>` : '';
      }).filter(Boolean).join("");
    }

    el.innerHTML = `
      <div class="feature-item-title">${item.title} (${item.review_count} Yorum)</div>
      <div class="feature-item-desc">${item.description}</div>
      ${quotesHtml}
    `;

    containerEl.appendChild(el);
  });
}

function downloadMarkdownReport(data) {
  if (!data.markdown_report) return;

  const blob = new Blob([data.markdown_report], { type: "text/markdown;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  
  const cleanName = data.app_name.toLowerCase().replace(/[^a-z0-9]/g, "-");
  a.download = `revixa-${cleanName}-${dateTimeStr()}.md`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

function dateTimeStr() {
  const now = new Date();
  const yyyy = now.getFullYear();
  const mm   = String(now.getMonth() + 1).padStart(2, "0");
  const dd   = String(now.getDate()).padStart(2, "0");
  const hh   = String(now.getHours()).padStart(2, "0");
  const min  = String(now.getMinutes()).padStart(2, "0");
  return `${yyyy}-${mm}-${dd}_${hh}-${min}`;
}
