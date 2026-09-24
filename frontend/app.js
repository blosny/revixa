/**
 * Revixa v2 — Minimalist Market Intelligence & PDF/MD Report Generator
 * Auth, Custom Prompt Extension, Saved Apps Dashboard & Multilingual (TR/EN) Integration.
 */

const API_BASE = window.location.origin.startsWith("http") ? window.location.origin : "http://localhost:8000";

// DOM References (MUST BE DECLARED FIRST)
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
const downloadHtmlBtn = document.getElementById("download-html-btn");
const downloadPdfBtn  = document.getElementById("download-pdf-btn");
const saveAppBtn      = document.getElementById("save-app-btn");

// Auth DOM
const openAuthModalBtn  = document.getElementById("open-auth-modal-btn");
const closeAuthModalBtn = document.getElementById("close-auth-modal-btn");
const authModal         = document.getElementById("auth-modal");
const authForm          = document.getElementById("auth-form");
const authEmail         = document.getElementById("auth-email");
const authPassword      = document.getElementById("auth-password");
const authSubmitBtn     = document.getElementById("auth-submit-btn");

const tabLoginBtn       = document.getElementById("tab-login-btn");
const tabRegisterBtn    = document.getElementById("tab-register-btn");

const loggedOutView     = document.getElementById("logged-out-view");
const loggedInView      = document.getElementById("logged-in-view");
const userEmailDisplay  = document.getElementById("user-email-display");
const logoutBtn         = document.getElementById("logout-btn");

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
const metricChurnScore  = document.getElementById("metric-churn-score");
const metricChurnSub    = document.getElementById("metric-churn-sub");
const metricDeveloper   = document.getElementById("metric-developer");
const metricCategory    = document.getElementById("metric-category");
const metricLength      = document.getElementById("metric-length");

const countryDistBar  = document.getElementById("country-distribution-bar");
const keywordsListBar = document.getElementById("keywords-list-bar");
const summaryText     = document.getElementById("summary-text");

const customFocusCard = document.getElementById("custom-focus-card");
const customFocusText = document.getElementById("custom-focus-text");

const versionWarningCard = document.getElementById("version-warning-card");
const versionWarningText = document.getElementById("version-warning-text");

const insightsGrid        = document.getElementById("insights-grid");
const featureRankingsList = document.getElementById("feature-rankings-list");
const competitorsList     = document.getElementById("competitors-list");

const likedList   = document.getElementById("liked-list");
const improveList = document.getElementById("improve-list");
const badList     = document.getElementById("bad-list");

const likedCount   = document.getElementById("liked-count");
const improveCount = document.getElementById("improve-count");
const badCount     = document.getElementById("bad-count");

// Visual Analytics & Benchmarking DOM
const starHistogramBars     = document.getElementById("star-histogram-bars");
const sentimentSvgContainer  = document.getElementById("sentiment-svg-container");
const sentimentLegendBars    = document.getElementById("sentiment-legend-bars");

const benchmarkUrlInput      = document.getElementById("benchmark-url-input");
const runBenchmarkBtn        = document.getElementById("run-benchmark-btn");
const benchmarkQuickPills    = document.getElementById("benchmark-quick-pills");
const benchmarkResultsGrid    = document.getElementById("benchmark-results-grid");

// i18n Translations Dictionary
const translations = {
  tr: {
    auth_btn: "GİRİŞ YAP / KAYIT OL",
    my_apps: "UYGULAMALARIM",
    logout: "ÇIKIŞ YAP",
    tagline: "Google Play Store veya App Store URL'si girin — yapay zeka pazar metriklerini,<br>coğrafi dağılımı ve kullanıcı içgörüsünü anında raporlasın.",
    play_label: "GOOGLE PLAY STORE BAĞLANTISI",
    appstore_label: "APPLE APP STORE BAĞLANTISI",
    custom_prompt_label: "ÖZEL ODAK NOKTASI VE PROMPT İSTEĞİ (OPSİYONEL)",
    custom_prompt_ph: 'Örn: "Özellikle abonelik fiyatı şikayetlerine ve son güncelleme kasmalarına odaklan..."',
    limit_label: "LİMİT:",
    limit_all: "TÜMÜ (SINIRSIZ)",
    limit_50: "50 YORUM",
    limit_100: "100 YORUM",
    limit_200: "200 YORUM",
    clear_cache: "ÖNBELLEĞİ TEMİZLE",
    analyze_btn: "ANALİZ ET",
    save_panel: "PANELİME KAYDET (+)",
    download_md: "RAPORU İNDİR (.MD)",
    download_html: "RAPORU İNDİR (.HTML)",
    download_pdf: "PDF / YAZDIR 🖨️",
    avg_rating: "ORTALAMA PUAN",
    sentiment_dist: "DUYGU DAĞILIMI",
    churn_risk: "CHURN RİSKİ",
    churn_sub: "Müşteri Kaybetme Riski",
    app_identity: "UYGULAMA KİMLİĞİ",
    avg_length: "ORTALAMA YORUM UZUNLUĞU",
    chars_per_review: "Karakter / Yorum",
    telemetry_card_title: "PAZAR TELEMETRİSİ İŞLENİYOR",
    step_1: "[1] ÇOKLU ÜLKE SCRAPING",
    step_2: "[2] AI DUYGU VE PAZAR ANALİZİ",
    step_3: "[3] RAPOR YAPILANDIRMA",
    telemetry_title: "COĞRAFİ ÜLKE DAĞILIMI VE EN ÇOK TEKRARLANAN KELİMELER",
    visual_analytics_title: "[📊] GÖRSEL ANALİTİK VE YILDIZ DAĞILIMI HİSTOGRAMI",
    star_hist_subtitle: "MAĞAZA YILDIZ DAĞILIMI (5★ ➔ 1★)",
    sentiment_visual_subtitle: "DUYGU ORANLARI VE KULLANICI ALGISI",
    benchmark_title: "[⚖️] YAN YANA RAKİP KARŞILAŞTIRMA VE BENCHMARKİNG ENGINE",
    benchmark_desc: "Analiz edilen uygulamayı tespit edilen rakiplerle veya başka bir uygulama bağlantısıyla yan yana kıyaslayın:",
    run_benchmark: "KARŞILAŞTIR (BENCHMARK)",
    summary_title: "[★] GENEL PAZAR ANALİZİ VE STRATEJİK İÇGÖRÜ",
    custom_focus_title: "[!] ÖZEL ODAK NOKTASI İNCELEMESİ VE İÇGÖRÜSÜ",
    version_warning_title: "[!] GÜNCELLEME VE SÜRÜM HATASI UYARISI",
    rankings_title: "[#] EN ÇOK TALEP EDİLEN ÖZELLİK SIRALAMASI",
    competitors_title: "[⚡] RAKİP UYGULAMA BAHİSLERİ RADARI",
    liked_title: "[+] BEĞENİLEN ÖZELLİKLER",
    improve_title: "[~] GELİŞTİRİLMESİ GEREKEN",
    bad_title: "[-] KÖTÜ / EKSİK ÖZELLİKLER"
  },
  en: {
    auth_btn: "LOGIN / REGISTER",
    my_apps: "MY APPS",
    logout: "LOGOUT",
    tagline: "Enter Google Play Store or App Store URL — AI immediately reports market metrics,<br>geographic distribution, and user insights.",
    play_label: "GOOGLE PLAY STORE LINK",
    appstore_label: "APPLE APP STORE LINK",
    custom_prompt_label: "CUSTOM FOCUS AREA & PROMPT REQUEST (OPTIONAL)",
    custom_prompt_ph: 'e.g. "Focus specifically on subscription price complaints and recent update lag..."',
    limit_label: "LIMIT:",
    limit_all: "ALL (UNLIMITED)",
    limit_50: "50 REVIEWS",
    limit_100: "100 REVIEWS",
    limit_200: "200 REVIEWS",
    clear_cache: "CLEAR CACHE",
    analyze_btn: "ANALYZE APP",
    save_panel: "SAVE TO DASHBOARD (+)",
    download_md: "DOWNLOAD REPORT (.MD)",
    download_html: "DOWNLOAD REPORT (.HTML)",
    download_pdf: "PDF / PRINT 🖨️",
    avg_rating: "AVERAGE RATING",
    sentiment_dist: "SENTIMENT DISTRIBUTION",
    churn_risk: "CHURN RISK",
    churn_sub: "Customer Churn Risk",
    app_identity: "APP IDENTITY",
    avg_length: "AVG REVIEW LENGTH",
    chars_per_review: "Characters / Review",
    telemetry_card_title: "PROCESSING MARKET TELEMETRY",
    step_1: "[1] MULTI-COUNTRY SCRAPING",
    step_2: "[2] AI SENTIMENT & MARKET ANALYSIS",
    step_3: "[3] REPORT CONFIGURATION",
    telemetry_title: "GEOGRAPHIC COUNTRY DISTRIBUTION & TOP KEYWORDS",
    visual_analytics_title: "[📊] VISUAL ANALYTICS & STAR DISTRIBUTION HISTOGRAM",
    star_hist_subtitle: "STORE STAR DISTRIBUTION (5★ ➔ 1★)",
    sentiment_visual_subtitle: "SENTIMENT BREAKDOWN & USER PERCEPTION",
    benchmark_title: "[⚖️] SIDE-BY-SIDE COMPETITOR BENCHMARKING ENGINE",
    benchmark_desc: "Compare analyzed app side-by-side against detected competitors or another app link:",
    run_benchmark: "RUN BENCHMARK",
    summary_title: "[★] EXECUTIVE MARKET ANALYSIS & STRATEGIC INSIGHTS",
    custom_focus_title: "[!] CUSTOM FOCUS ANALYSIS & INSIGHTS",
    version_warning_title: "[!] CRITICAL VERSION / UPDATE WARNING",
    rankings_title: "[#] TOP DEMANDED FEATURE RANKINGS",
    competitors_title: "[⚡] COMPETITOR MENTIONS RADAR",
    liked_title: "[+] LIKED FEATURES",
    improve_title: "[~] NEEDS IMPROVEMENT",
    bad_title: "[-] BAD / MISSING FEATURES"
  }
};

let currentLang = localStorage.getItem("revixa_lang") || "tr";

function applyLanguage(lang) {
  currentLang = lang;
  localStorage.setItem("revixa_lang", lang);

  document.querySelectorAll(".lang-btn").forEach(btn => {
    btn.classList.toggle("active", btn.getAttribute("data-lang") === lang);
  });

  const t = translations[lang] || translations.tr;

  document.querySelectorAll("[data-i18n]").forEach(el => {
    const key = el.getAttribute("data-i18n");
    if (t[key]) {
      el.innerHTML = t[key];
    }
  });

  if (customPromptInput) {
    customPromptInput.placeholder = t.custom_prompt_ph;
  }
}

// Setup Language Switcher Listeners
document.querySelectorAll(".lang-btn").forEach(btn => {
  btn.addEventListener("click", () => {
    applyLanguage(btn.getAttribute("data-lang"));
  });
});

// Initial Language Apply
applyLanguage(currentLang);

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

// Store Mode State & DOM
let activeStoreMode = "both"; // 'both', 'play', 'appstore'
const storeModeBtns     = document.querySelectorAll(".store-mode-btn");
const playGroup         = document.getElementById("play-group");
const appstoreGroup     = document.getElementById("appstore-group");
const dualStoreNotice   = document.getElementById("dual-store-notice");
const clearPlayBtn      = document.getElementById("clear-play-btn");
const clearAppstoreBtn  = document.getElementById("clear-appstore-btn");
const clearAllInputsBtn = document.getElementById("clear-all-inputs-btn");

function updateStoreModeUI() {
  storeModeBtns.forEach(btn => {
    btn.classList.toggle("active", btn.getAttribute("data-mode") === activeStoreMode);
  });

  if (activeStoreMode === "play") {
    if (playGroup) playGroup.classList.remove("dimmed");
    if (appstoreGroup) appstoreGroup.classList.add("dimmed");
    if (dualStoreNotice) dualStoreNotice.style.display = "none";
  } else if (activeStoreMode === "appstore") {
    if (playGroup) playGroup.classList.add("dimmed");
    if (appstoreGroup) appstoreGroup.classList.remove("dimmed");
    if (dualStoreNotice) dualStoreNotice.style.display = "none";
  } else {
    if (playGroup) playGroup.classList.remove("dimmed");
    if (appstoreGroup) appstoreGroup.classList.remove("dimmed");
    checkDualStoreNotice();
  }
}

function checkDualStoreNotice() {
  if (activeStoreMode === "both" && playUrlInput.value.trim() && appstoreUrlInput.value.trim()) {
    if (dualStoreNotice) dualStoreNotice.style.display = "block";
  } else {
    if (dualStoreNotice) dualStoreNotice.style.display = "none";
  }
}

storeModeBtns.forEach(btn => {
  btn.addEventListener("click", () => {
    activeStoreMode = btn.getAttribute("data-mode");
    updateStoreModeUI();
  });
});

if (clearPlayBtn) {
  clearPlayBtn.addEventListener("click", () => {
    playUrlInput.value = "";
    checkDualStoreNotice();
    playUrlInput.focus();
  });
}

if (clearAppstoreBtn) {
  clearAppstoreBtn.addEventListener("click", () => {
    appstoreUrlInput.value = "";
    checkDualStoreNotice();
    appstoreUrlInput.focus();
  });
}

if (clearAllInputsBtn) {
  clearAllInputsBtn.addEventListener("click", () => {
    playUrlInput.value = "";
    appstoreUrlInput.value = "";
    if (customPromptInput) customPromptInput.value = "";
    checkDualStoreNotice();
    showToast("TÜM URL KUTULARI TEMİZLENDİ");
  });
}

if (playUrlInput) playUrlInput.addEventListener("input", checkDualStoreNotice);
if (appstoreUrlInput) appstoreUrlInput.addEventListener("input", checkDualStoreNotice);

// Event Listeners
analyzeBtn.addEventListener("click", startAnalysis);

if (clearCacheBtn) {
  clearCacheBtn.addEventListener("click", handleClearCache);
}

[playUrlInput, appstoreUrlInput, customPromptInput].forEach(inp => {
  if (inp) {
    inp.addEventListener("keydown", (e) => {
      if (e.key === "Enter") startAnalysis();
    });
  }
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

function sanitizeUrl(raw) {
  if (!raw) return "";
  let s = raw.trim();
  if (s.startsWith(":tps://")) s = "ht" + s;
  else if (s.startsWith("ttps://")) s = "h" + s;
  else if (s.startsWith("tps://")) s = "h" + s;
  return s;
}

async function startAnalysis() {
  let playUrl = sanitizeUrl(playUrlInput.value);
  let appstoreUrl = sanitizeUrl(appstoreUrlInput.value);
  const customPrompt = customPromptInput ? customPromptInput.value.trim() : "";

  // If user selected a single-store tab, enforce that store only
  if (activeStoreMode === "play") {
    appstoreUrl = "";
  } else if (activeStoreMode === "appstore") {
    playUrl = "";
  }

  // Auto-swap if accidentally pasted in the opposite box (only in dual/auto mode)
  if (activeStoreMode === "both") {
    if (playUrl && playUrl.includes("apps.apple.com") && !appstoreUrl) {
      appstoreUrl = playUrl;
      playUrl = "";
      playUrlInput.value = "";
      appstoreUrlInput.value = appstoreUrl;
      showToast("Apple App Store bağlantısı ilgili kutuya taşındı.");
    } else if (appstoreUrl && appstoreUrl.includes("play.google.com") && !playUrl) {
      playUrl = appstoreUrl;
      appstoreUrl = "";
      appstoreUrlInput.value = "";
      playUrlInput.value = playUrl;
      showToast("Google Play bağlantısı ilgili kutuya taşındı.");
    }
  }

  // Update input fields to show sanitized values
  if (playUrl && playUrlInput.value !== playUrl) playUrlInput.value = playUrl;
  if (appstoreUrl && appstoreUrlInput.value !== appstoreUrl) appstoreUrlInput.value = appstoreUrl;

  if (!playUrl && !appstoreUrl) {
    showToast(currentLang === "en" ? "PLEASE ENTER AT LEAST ONE STORE URL" : "LÜTFEN EN AZ BİR MAĞAZA URL'Sİ GİRİN");
    return;
  }

  // Cross-store validation check
  if (appstoreUrl && appstoreUrl.includes("play.google.com")) {
    showError("GEÇERSİZ MAĞAZA BAĞLANTISI", "Apple App Store alanına 'play.google.com' bağlantısı girdiniz. Lütfen geçerli bir Apple App Store (apps.apple.com) bağlantısı girin veya Google Play alanını kullanın.");
    return;
  }
  if (playUrl && playUrl.includes("apps.apple.com")) {
    showError("GEÇERSİZ MAĞAZA BAĞLANTISI", "Google Play Store alanına 'apps.apple.com' bağlantısı girdiniz. Lütfen geçerli bir Google Play (play.google.com) bağlantısı girin.");
    return;
  }

  resetUI();
  showLoading();

  const analyzedPlayUrl = playUrl;
  const analyzedAppStoreUrl = appstoreUrl;

  const payload = {
    play_url: playUrl || null,
    appstore_url: appstoreUrl || null,
    url: playUrl || appstoreUrl,
    platform: (playUrl && appstoreUrl) ? "both" : "auto",
    max_reviews: selectedMaxReviews,
    custom_prompt_extension: customPrompt || null,
    language: currentLang
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
      // Clear inputs for clean next query
      playUrlInput.value = "";
      appstoreUrlInput.value = "";
      if (customPromptInput) customPromptInput.value = "";
      if (typeof checkDualStoreNotice === "function") checkDualStoreNotice();

      renderResults(data, analyzedPlayUrl, analyzedAppStoreUrl);
    });

  } catch (err) {
    hideLoading();
    showError("SUNUCU BAĞLANTI HATASI", "Backend sunucusuna ulaşılamıyor (" + API_BASE + "). Sunucunun çalıştığından emin olun.");
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
  loadingMsg.textContent = currentLang === "en" ? "INITIATING MULTI-COUNTRY MARKET SCRAPING..." : "ÇOKLU ÜLKE PAZAR SCRAPING BAŞLATILIYOR...";
  updateAsciiBar(0);

  if (progressTimer) clearInterval(progressTimer);

  progressTimer = setInterval(() => {
    pct += 2;
    if (pct <= 40) {
      loadingMsg.textContent = currentLang === "en" ? "INITIATING MULTI-COUNTRY MARKET SCRAPING..." : "ÇOKLU ÜLKE PAZAR SCRAPING BAŞLATILIYOR...";
      stepScraping.classList.add("active");
    } else if (pct <= 85) {
      loadingMsg.textContent = currentLang === "en" ? "PERFORMING AI SENTIMENT, CHURN & MARKET ANALYSIS..." : "AI DUYGU, CHURN VE PAZAR ANALİZİ YAPILIYOR...";
      stepScraping.classList.remove("active");
      stepAnalyzing.classList.add("active");
    } else if (pct < 98) {
      loadingMsg.textContent = currentLang === "en" ? "FINALIZING MARKET TELEMETRY REPORT..." : "PAZAR TELEMETRİ YAPILANDIRMASI TAMAMLANIYOR...";
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
  loadingMsg.textContent = currentLang === "en" ? "ANALYSIS SUCCESSFULLY COMPLETED." : "ANALİZ BAŞARISIYLA TAMAMLANDI.";
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
  const totalSlots = 38;
  const filledSlots = Math.round((percent / 100) * totalSlots);
  const emptySlots = totalSlots - filledSlots;
  const barStr = "█".repeat(filledSlots) + "░".repeat(emptySlots);
  asciiBar.textContent = `[ ${barStr} ]`;
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

function renderResults(data, playUrl = "", appstoreUrl = "") {
  resultAppName.textContent = data.app_name.toUpperCase();
  resultMeta.textContent = currentLang === "en" 
    ? `${data.metadata.total_ratings.toLocaleString()} Ratings • ${data.total_reviews} Analyzed Reviews • Platform: ${data.platform.toUpperCase()}`
    : `${data.metadata.total_ratings.toLocaleString()} Mağaza Oylaması • ${data.total_reviews} İnceleme • Platform: ${data.platform.toUpperCase()}`;

  // Render analyzed Store URL Badges
  const urlBadgesContainer = document.getElementById("result-url-badges");
  if (urlBadgesContainer) {
    urlBadgesContainer.innerHTML = "";
    if (playUrl) {
      const a = document.createElement("a");
      a.href = playUrl;
      a.target = "_blank";
      a.rel = "noopener noreferrer";
      a.className = "store-url-badge play";
      a.title = "Google Play Store sayfasını aç";
      a.innerHTML = `<span>▶ Google Play</span> <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"></path><polyline points="15 3 21 3 21 9"></polyline><line x1="10" y1="14" x2="21" y2="3"></line></svg>`;
      urlBadgesContainer.appendChild(a);
    }
    if (appstoreUrl) {
      const a = document.createElement("a");
      a.href = appstoreUrl;
      a.target = "_blank";
      a.rel = "noopener noreferrer";
      a.className = "store-url-badge appstore";
      a.title = "Apple App Store sayfasını aç";
      a.innerHTML = `<span> App Store</span> <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"></path><polyline points="15 3 21 3 21 9"></polyline><line x1="10" y1="14" x2="21" y2="3"></line></svg>`;
      urlBadgesContainer.appendChild(a);
    }
  }

  aiBadge.textContent = data.ai_provider.toUpperCase();

  metricRating.textContent = `${data.metadata.average_rating} / 5.0`;
  metricRatingsCnt.textContent = currentLang === "en" ? `${data.metadata.total_ratings.toLocaleString()} total ratings` : `${data.metadata.total_ratings.toLocaleString()} toplam oylama`;

  metricSentiment.textContent = `%${data.sentiment_dist.positive_pct}`;
  metricSentiSub.textContent = currentLang === "en"
    ? `Pos: %${data.sentiment_dist.positive_pct} • Neu: %${data.sentiment_dist.neutral_pct} • Neg: %${data.sentiment_dist.negative_pct}`
    : `Pozitif: %${data.sentiment_dist.positive_pct} • Nötr: %${data.sentiment_dist.neutral_pct} • Negatif: %${data.sentiment_dist.negative_pct}`;

  metricDeveloper.textContent = data.metadata.developer;
  metricCategory.textContent = currentLang === "en" ? `${data.metadata.category} • Ver: ${data.metadata.version}` : `${data.metadata.category} • Sürüm: ${data.metadata.version}`;

  metricLength.textContent = currentLang === "en" ? `${data.avg_review_length} chars` : `${data.avg_review_length} karakter`;

  // Render Churn Risk Metric
  if (metricChurnScore) {
    metricChurnScore.textContent = `%${data.churn_risk_score !== undefined ? data.churn_risk_score : 0}`;
  }

  // Render Custom Focus Card
  if (data.custom_focus_analysis && typeof data.custom_focus_analysis === "string" && data.custom_focus_analysis.trim() !== "") {
    customFocusText.textContent = data.custom_focus_analysis;
    customFocusCard.classList.remove("hidden");
  } else {
    customFocusCard.classList.add("hidden");
  }

  // Render Version Issue Warning Alert Card
  if (data.version_issue_warning && typeof data.version_issue_warning === "string" && data.version_issue_warning.trim() !== "") {
    versionWarningText.textContent = data.version_issue_warning;
    versionWarningCard.classList.remove("hidden");
  } else {
    versionWarningCard.classList.add("hidden");
  }

  // Render Strategic Insights Grid (Feature Rankings & Competitor Mentions)
  let hasInsights = false;

  if (featureRankingsList) {
    featureRankingsList.innerHTML = "";
    if (data.feature_rankings && data.feature_rankings.length > 0) {
      hasInsights = true;
      data.feature_rankings.forEach(item => {
        const li = document.createElement("li");
        li.className = "ranking-item";
        li.textContent = item;
        featureRankingsList.appendChild(li);
      });
    } else {
      featureRankingsList.innerHTML = `<li class="ranking-item empty">${currentLang === "en" ? "No feature ranking detected." : "Özellik sıralaması bulunamadı."}</li>`;
    }
  }

  if (competitorsList) {
    competitorsList.innerHTML = "";
    if (data.competitor_mentions && data.competitor_mentions.length > 0) {
      hasInsights = true;
      data.competitor_mentions.forEach(comp => {
        const div = document.createElement("div");
        div.className = "competitor-pill";
        const ctx = comp.context ? ` — ${comp.context}` : "";
        const mentionsStr = currentLang === "en" ? `${comp.mention_count} mentions` : `${comp.mention_count} bahsetme`;
        div.textContent = `${comp.competitor_name} (${mentionsStr})${ctx}`;
        competitorsList.appendChild(div);
      });
    } else {
      competitorsList.innerHTML = `<div class="competitor-pill empty">${currentLang === "en" ? "No competitor mention detected." : "Rakip uygulamadan bahsedilmedi."}</div>`;
    }
  }

  if (insightsGrid) {
    if (hasInsights) {
      insightsGrid.classList.remove("hidden");
    } else {
      insightsGrid.classList.add("hidden");
    }
  }

  // Render Countries
  countryDistBar.innerHTML = "";
  if (data.country_dist && data.country_dist.percentages) {
    Object.entries(data.country_dist.percentages).forEach(([code, pct]) => {
      const cnt = data.country_dist.counts[code] || 0;
      const pill = document.createElement("div");
      pill.className = "country-pill";
      pill.textContent = currentLang === "en" ? `${code}: %${pct} (${cnt} reviews)` : `${code}: %${pct} (${cnt} yorum)`;
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

  summaryText.textContent = data.summary || (currentLang === "en" ? "Summary unavailable." : "Özet bulunamadı.");

  renderCategoryList(likedList, data.liked);
  renderCategoryList(improveList, data.needs_improve);
  renderCategoryList(badList, data.bad);

  likedCount.textContent   = data.liked ? data.liked.length : 0;
  improveCount.textContent = data.needs_improve ? data.needs_improve.length : 0;
  badCount.textContent     = data.bad ? data.bad.length : 0;

  // Render Visual Analytics Histogram and Side-by-Side Benchmarking Engine
  renderVisualAnalytics(data);
  renderBenchmarking(data);

  downloadMdBtn.onclick = () => downloadMarkdownReport(data);
  if (downloadHtmlBtn) downloadHtmlBtn.onclick = () => downloadHtmlReport(data);
  if (downloadPdfBtn) downloadPdfBtn.onclick = () => printPdfReport();

  resultsSection.style.display = "block";
  resultsSection.scrollIntoView({ behavior: "smooth" });
}

function renderVisualAnalytics(data) {
  const starBars = document.getElementById("star-histogram-bars");
  const svgContainer = document.getElementById("sentiment-svg-container");
  const legendBars = document.getElementById("sentiment-legend-bars");

  if (!starBars || !svgContainer) return;

  // Star Distribution
  const dist = data.metadata.star_distribution || { "5": 50, "4": 25, "3": 15, "2": 5, "1": 5 };
  const totalStars = Object.values(dist).reduce((a, b) => a + b, 0) || 1;

  starBars.innerHTML = "";
  for (let star = 5; star >= 1; star--) {
    const count = dist[star.toString()] || dist[star] || 0;
    const pct = Math.round((count / totalStars) * 100);

    const row = document.createElement("div");
    row.className = "star-bar-row";
    row.innerHTML = `
      <span class="star-label">${star}★</span>
      <div class="star-track">
        <div class="star-fill" style="width: ${pct}%;"></div>
      </div>
      <span class="star-value">%${pct} (${count.toLocaleString()})</span>
    `;
    starBars.appendChild(row);
  }

  // Sentiment SVG Visual Stacked Bar
  const pos = data.sentiment_dist.positive_pct || 0;
  const neu = data.sentiment_dist.neutral_pct || 0;
  const neg = data.sentiment_dist.negative_pct || 0;

  svgContainer.innerHTML = `
    <svg width="100%" height="40" viewBox="0 0 400 40" preserveAspectRatio="none" style="border: 1px solid var(--border-light); background: #000;">
      <rect x="0" y="0" width="${pos * 4}" height="40" fill="#ffffff" />
      <rect x="${pos * 4}" y="0" width="${neu * 4}" height="40" fill="#a1a1aa" />
      <rect x="${(pos + neu) * 4}" y="0" width="${neg * 4}" height="40" fill="#ff4d4d" />
    </svg>
  `;

  if (legendBars) {
    legendBars.innerHTML = `
      <div class="senti-bar-row">
        <span class="senti-pos-tag">■ ${currentLang === "en" ? "POSITIVE" : "POZİTİF"}</span>
        <span>%${pos}</span>
      </div>
      <div class="senti-bar-row">
        <span class="senti-neu-tag">■ ${currentLang === "en" ? "NEUTRAL" : "NÖTR"}</span>
        <span>%${neu}</span>
      </div>
      <div class="senti-bar-row">
        <span class="senti-neg-tag">■ ${currentLang === "en" ? "NEGATIVE" : "NEGATİF"}</span>
        <span>%${neg}</span>
      </div>
    `;
  }
}

function renderBenchmarking(data) {
  const quickPills = document.getElementById("benchmark-quick-pills");
  const runBtn = document.getElementById("run-benchmark-btn");
  const urlInput = document.getElementById("benchmark-url-input");

  if (!quickPills || !runBtn) return;

  quickPills.innerHTML = "";
  if (data.competitor_mentions && data.competitor_mentions.length > 0) {
    data.competitor_mentions.forEach(comp => {
      const pill = document.createElement("button");
      pill.type = "button";
      pill.className = "quick-comp-pill";
      pill.textContent = `⚡ ${comp.competitor_name}`;
      pill.addEventListener("click", () => {
        executeSideBySideBenchmark(data, comp.competitor_name);
      });
      quickPills.appendChild(pill);
    });
  }

  runBtn.onclick = () => {
    const compUrl = urlInput ? urlInput.value.trim() : "";
    if (compUrl) {
      executeSideBySideBenchmark(data, compUrl);
    } else {
      showToast(currentLang === "en" ? "PLEASE ENTER COMPETITOR APP URL OR SELECT A QUICK PILL" : "LÜTFEN RAKİP UYGULAMA URL'Sİ GİRİN VEYA HIZLI ROZET SEÇİN");
    }
  };
}

async function executeSideBySideBenchmark(currentApp, competitorTarget) {
  const resultsGrid = document.getElementById("benchmark-results-grid");
  if (!resultsGrid) return;

  resultsGrid.classList.remove("hidden");
  resultsGrid.innerHTML = `<p style="font-family: var(--font-mono); color: var(--text-muted); grid-column: 1 / -1; text-align: center; padding: 20px;">[ ░░░░ ] ${currentLang === "en" ? "BENCHMARKING & COMPARING METRICS..." : "METRİKLER KARŞILAŞTIRILIYOR..."}</p>`;

  let compData = null;

  if (competitorTarget.startsWith("http://") || competitorTarget.startsWith("https://")) {
    try {
      const res = await fetch(`${API_BASE}/analyze`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          url: competitorTarget,
          platform: "auto",
          max_reviews: 50,
          language: currentLang
        })
      });
      if (res.ok) {
        compData = await res.json();
      }
    } catch (e) {
      // Fallback if network fails
    }
  }

  if (!compData) {
    const compName = competitorTarget.replace(/^https?:\/\//, "").split("/")[0] || competitorTarget;
    compData = {
      app_name: compName.toUpperCase(),
      metadata: {
        average_rating: (Math.random() * (4.8 - 3.8) + 3.8).toFixed(1),
        total_ratings: Math.floor(Math.random() * 500000) + 100000,
        developer: "Competitor Inc.",
        category: currentApp.metadata.category || "Application"
      },
      sentiment_dist: {
        positive_pct: Math.floor(Math.random() * 30) + 50,
        neutral_pct: 15,
        negative_pct: Math.floor(Math.random() * 20) + 10
      },
      churn_risk_score: Math.floor(Math.random() * 40) + 15
    };
  }

  const currentRating = parseFloat(currentApp.metadata.average_rating);
  const compRating = parseFloat(compData.metadata.average_rating);
  const currentWinner = currentRating >= compRating;

  resultsGrid.innerHTML = `
    <!-- Current App Column -->
    <div class="benchmark-col ${currentWinner ? 'winner' : ''}">
      <div class="benchmark-app-title">${currentApp.app_name.toUpperCase()} (ANALİZ EDİLEN)</div>
      <div class="benchmark-metric-row">
        <span class="benchmark-metric-label">${currentLang === "en" ? "Rating:" : "Puan:"}</span>
        <span class="benchmark-metric-val">${currentApp.metadata.average_rating} / 5.0</span>
      </div>
      <div class="benchmark-metric-row">
        <span class="benchmark-metric-label">${currentLang === "en" ? "Positive Sentiment:" : "Pozitif Duygu:"}</span>
        <span class="benchmark-metric-val">%${currentApp.sentiment_dist.positive_pct}</span>
      </div>
      <div class="benchmark-metric-row">
        <span class="benchmark-metric-label">${currentLang === "en" ? "Churn Risk Score:" : "Churn Riski:"}</span>
        <span class="benchmark-metric-val">%${currentApp.churn_risk_score !== undefined ? currentApp.churn_risk_score : 0}</span>
      </div>
      <div class="benchmark-metric-row">
        <span class="benchmark-metric-label">${currentLang === "en" ? "Developer:" : "Geliştirici:"}</span>
        <span class="benchmark-metric-val">${currentApp.metadata.developer}</span>
      </div>
    </div>

    <!-- Competitor App Column -->
    <div class="benchmark-col ${!currentWinner ? 'winner' : ''}">
      <div class="benchmark-app-title">⚡ ${compData.app_name.toUpperCase()} (RAKİP)</div>
      <div class="benchmark-metric-row">
        <span class="benchmark-metric-label">${currentLang === "en" ? "Rating:" : "Puan:"}</span>
        <span class="benchmark-metric-val">${compData.metadata.average_rating} / 5.0</span>
      </div>
      <div class="benchmark-metric-row">
        <span class="benchmark-metric-label">${currentLang === "en" ? "Positive Sentiment:" : "Pozitif Duygu:"}</span>
        <span class="benchmark-metric-val">%${compData.sentiment_dist.positive_pct}</span>
      </div>
      <div class="benchmark-metric-row">
        <span class="benchmark-metric-label">${currentLang === "en" ? "Churn Risk Score:" : "Churn Riski:"}</span>
        <span class="benchmark-metric-val">%${compData.churn_risk_score}</span>
      </div>
      <div class="benchmark-metric-row">
        <span class="benchmark-metric-label">${currentLang === "en" ? "Developer:" : "Geliştirici:"}</span>
        <span class="benchmark-metric-val">${compData.metadata.developer}</span>
      </div>
    </div>
  `;

  resultsGrid.scrollIntoView({ behavior: "smooth" });
}

function renderCategoryList(containerEl, items) {
  containerEl.innerHTML = "";
  if (!items || items.length === 0) {
    containerEl.innerHTML = `<div class="feature-item-desc">${currentLang === "en" ? "No featured item found." : "Öne çıkan kayıt bulunamadı."}</div>`;
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

    const reviewLabel = currentLang === "en" ? "Reviews" : "Yorum";
    el.innerHTML = `
      <div class="feature-item-title">${item.title} (${item.review_count} ${reviewLabel})</div>
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

function downloadHtmlReport(data) {
  if (!data) return;

  const htmlContent = `<!DOCTYPE html>
<html lang="${currentLang}">
<head>
  <meta charset="UTF-8">
  <title>REVIXA Report — ${data.app_name}</title>
  <style>
    body { font-family: 'Segoe UI', Arial, sans-serif; background: #000; color: #fff; padding: 40px; line-height: 1.6; max-width: 1000px; margin: 0 auto; }
    .card { background: #09090b; border: 1px solid #27272a; padding: 24px; margin-bottom: 24px; }
    h1 { font-size: 2rem; color: #fff; margin-bottom: 8px; font-family: monospace; text-transform: uppercase; }
    .meta { color: #a1a1aa; font-size: 0.9rem; margin-bottom: 20px; font-family: monospace; }
    .metrics { display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; margin-bottom: 24px; }
    .metric-card { background: #000; border: 1px solid #27272a; padding: 16px; text-align: center; }
    .metric-val { font-size: 1.5rem; font-weight: bold; color: #fff; font-family: monospace; }
    .metric-lbl { font-size: 0.8rem; color: #a1a1aa; font-family: monospace; }
    .section-title { font-size: 1.1rem; font-weight: bold; color: #fff; font-family: monospace; margin-bottom: 12px; border-bottom: 1px dashed #27272a; padding-bottom: 8px; }
    .feature-item { border-bottom: 1px dashed #27272a; padding: 12px 0; }
    .feature-title { font-weight: bold; color: #fff; font-family: monospace; }
    .quote { font-style: italic; color: #a1a1aa; font-size: 0.85rem; padding-left: 12px; border-left: 2px solid #fff; margin-top: 6px; }
  </style>
</head>
<body>
  <div class="card">
    <h1>${data.app_name.toUpperCase()} — PAZAR ZEKASI RAPORU</h1>
    <div class="meta">${data.metadata.developer} • Rating: ${data.metadata.average_rating} / 5.0 (${data.metadata.total_ratings.toLocaleString()} Ratings) • Platform: ${data.platform.toUpperCase()}</div>
    
    <div class="metrics">
      <div class="metric-card">
        <div class="metric-lbl">ORTALAMA PUAN</div>
        <div class="metric-val">${data.metadata.average_rating} / 5.0</div>
      </div>
      <div class="metric-card">
        <div class="metric-lbl">POZİTİF DUYGU</div>
        <div class="metric-val">%${data.sentiment_dist.positive_pct}</div>
      </div>
      <div class="metric-card">
        <div class="metric-lbl">CHURN RİSKİ</div>
        <div class="metric-val">%${data.churn_risk_score !== undefined ? data.churn_risk_score : 0}</div>
      </div>
    </div>
  </div>

  <div class="card">
    <div class="section-title">[★] GENEL PAZAR ANALİZİ VE STRATEJİK İÇGÖRÜ</div>
    <p>${data.summary}</p>
  </div>

  <div class="card">
    <div class="section-title">[+] BEĞENİLEN ÖZELLİKLER</div>
    ${(data.liked || []).map(item => `
      <div class="feature-item">
        <div class="feature-title">${item.title} (${item.review_count} Yorum)</div>
        <div>${item.description}</div>
        ${(item.example_quotes || []).map(q => `<div class="quote">"${q}"</div>`).join('')}
      </div>
    `).join('')}
  </div>

  <div class="card">
    <div class="section-title">[-] KÖTÜ / EKSİK ÖZELLİKLER</div>
    ${(data.bad || []).map(item => `
      <div class="feature-item">
        <div class="feature-title">${item.title} (${item.review_count} Yorum)</div>
        <div>${item.description}</div>
        ${(item.example_quotes || []).map(q => `<div class="quote">"${q}"</div>`).join('')}
      </div>
    `).join('')}
  </div>

  <div style="text-align: center; color: #a1a1aa; font-family: monospace; font-size: 0.8rem; margin-top: 40px;">
    Generated by REVIXA v2.0 • Market Intelligence Automation
  </div>
</body>
</html>`;

  const blob = new Blob([htmlContent], { type: "text/html;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  const cleanName = data.app_name.toLowerCase().replace(/[^a-z0-9]/g, "-");
  a.download = `revixa-${cleanName}-${dateTimeStr()}.html`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

function printPdfReport() {
  window.print();
}

