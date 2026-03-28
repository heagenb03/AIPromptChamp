/**
 * app.js — Main Entry Point for FoodFlow KC Frontend
 *
 * Orchestrates the entire client-side application:
 *  1. Handles ZIP code input and validation.
 *  2. Fetches data from the backend API (or uses mock data for dev).
 *  3. Renders the Need Score badge, comparison table, pantry cards,
 *     produce alert banner, and community vote panel.
 *  4. Wires up the language toggle.
 *
 * Depends on: i18n.js, table.js, cards.js, alerts.js (all loaded before this file).
 */

const app = (() => {
  "use strict";

  /* ─── Configuration ──────────────────────────────────────
   * Toggle USE_MOCK to false once the real backend is running.
   * API_BASE should point to the FastAPI server.
   * ───────────────────────────────────────────────────────── */
  const USE_MOCK = true;
  const API_BASE = "http://localhost:8000";

  /* ─── DOM References (populated in init()) ──────────────── */
  let elZipInput,
    elZipBtn,
    elZipError,
    elNeedBadge,
    elNeedScore,
    elNeedAlert,
    elTableContainer,
    elAlertContainer,
    elVoteForm,
    elVoteMessage,
    elLangToggle,
    elResultsSection,
    elLoadingSpinner;

  /* ─── Currently displayed data ──────────────────────────── */
  let currentData = null;

  /* ═══════════════════════════════════════════════════════════
   * MOCK DATA
   * Realistic sample data matching the API contract so the
   * frontend can be developed independently of the backend.
   * ═══════════════════════════════════════════════════════════ */
  const MOCK_DATA = {
    "64130": {
      zip: "64130",
      need_score: 82,
      options: [
        {
          name: "Harvesters Food Network",
          type: "pantry",
          cost_tier: "free",
          est_cost: "$0",
          distance_mi: 1.2,
          transit_accessible: true,
          languages: ["en", "es"],
          id_required: false,
          cold_storage: true,
          hours: "Mon–Fri 9AM–5PM",
          address: "3801 Topping Ave, Kansas City, MO 64129",
          notes: "Open today",
        },
        {
          name: "Community Assistance Council",
          type: "pantry",
          cost_tier: "free",
          est_cost: "$0",
          distance_mi: 2.4,
          transit_accessible: true,
          languages: ["en"],
          id_required: true,
          cold_storage: false,
          hours: "Tue & Thu 10AM–2PM",
          address: "10901 Blue Ridge Blvd, Kansas City, MO 64134",
          notes: "Photo ID needed",
        },
        {
          name: "Walmart Grocery Delivery",
          type: "delivery",
          cost_tier: "market",
          est_cost: "~$35+",
          distance_mi: null,
          transit_accessible: null,
          languages: ["en"],
          id_required: false,
          cold_storage: null,
          hours: "24/7 online",
          address: null,
          notes: "$7.95 delivery fee",
        },
        {
          name: "Price Chopper (64130)",
          type: "store",
          cost_tier: "low",
          est_cost: "~$40–60/wk",
          distance_mi: 2.1,
          transit_accessible: false,
          languages: ["en"],
          id_required: false,
          cold_storage: null,
          hours: "6AM–11PM daily",
          address: "4950 Troost Ave, Kansas City, MO 64110",
          notes: "SNAP accepted",
        },
        {
          name: "ALDI (Prospect)",
          type: "store",
          cost_tier: "low",
          est_cost: "~$30–50/wk",
          distance_mi: 3.0,
          transit_accessible: true,
          languages: ["en"],
          id_required: false,
          cold_storage: null,
          hours: "9AM–8PM daily",
          address: "5600 Prospect Ave, Kansas City, MO 64130",
          notes: "Budget-friendly, SNAP accepted",
        },
      ],
      produce_alert: {
        active: true,
        pounds: 1000,
        expires_in_hrs: 48,
        top_drop_locations: [
          { name: "Harvesters Food Network", address: "3801 Topping Ave" },
          { name: "Guadalupe Center", address: "1015 W Avenida Cesar E Chavez" },
          { name: "Community Assistance Council", address: "10901 Blue Ridge Blvd" },
        ],
      },
    },
    "64110": {
      zip: "64110",
      need_score: 65,
      options: [
        {
          name: "Reconciliation Services",
          type: "pantry",
          cost_tier: "free",
          est_cost: "$0",
          distance_mi: 0.8,
          transit_accessible: true,
          languages: ["en", "es"],
          id_required: false,
          cold_storage: true,
          hours: "Mon–Fri 8AM–4PM",
          address: "3101 Troost Ave, Kansas City, MO 64109",
          notes: "Walk-ins welcome",
        },
        {
          name: "Bishop Sullivan Center",
          type: "pantry",
          cost_tier: "free",
          est_cost: "$0",
          distance_mi: 1.5,
          transit_accessible: true,
          languages: ["en"],
          id_required: true,
          cold_storage: false,
          hours: "Wed & Fri 9AM–12PM",
          address: "6435 Rockhill Rd, Kansas City, MO 64131",
          notes: "Photo ID required",
        },
        {
          name: "Sun Fresh (Troost)",
          type: "store",
          cost_tier: "low",
          est_cost: "~$45–65/wk",
          distance_mi: 1.1,
          transit_accessible: true,
          languages: ["en"],
          id_required: false,
          cold_storage: null,
          hours: "7AM–10PM daily",
          address: "4001 Troost Ave, Kansas City, MO 64110",
          notes: "SNAP & WIC accepted",
        },
      ],
      produce_alert: {
        active: false,
        pounds: 0,
        expires_in_hrs: 0,
        top_drop_locations: [],
      },
    },
    "64108": {
      zip: "64108",
      need_score: 47,
      options: [
        {
          name: "Guadalupe Center",
          type: "pantry",
          cost_tier: "free",
          est_cost: "$0",
          distance_mi: 1.0,
          transit_accessible: true,
          languages: ["en", "es"],
          id_required: false,
          cold_storage: true,
          hours: "Mon–Fri 9AM–4PM",
          address: "1015 W Avenida Cesar E Chavez, Kansas City, MO 64108",
          notes: "Bilingual staff",
        },
        {
          name: "Cosentino's Price Chopper",
          type: "store",
          cost_tier: "low",
          est_cost: "~$40–55/wk",
          distance_mi: 1.8,
          transit_accessible: true,
          languages: ["en"],
          id_required: false,
          cold_storage: null,
          hours: "6AM–11PM daily",
          address: "1300 W 12th St, Kansas City, MO 64101",
          notes: "SNAP accepted",
        },
      ],
      produce_alert: {
        active: true,
        pounds: 500,
        expires_in_hrs: 24,
        top_drop_locations: [
          { name: "Guadalupe Center", address: "1015 W Avenida Cesar E Chavez" },
        ],
      },
    },
  };

  /* ═══════════════════════════════════════════════════════════
   * DATA FETCHING
   * ═══════════════════════════════════════════════════════════ */

  /**
   * fetchOptions(zip) — Retrieve food options for a ZIP code.
   * Uses mock data in dev mode, real API in production.
   * @param {string} zip — 5-digit ZIP string
   * @returns {Promise<Object|null>} — API response object or null
   */
  async function fetchOptions(zip) {
    if (USE_MOCK) {
      return new Promise((resolve) => {
        setTimeout(() => {
          resolve(MOCK_DATA[zip] || null);
        }, 400);
      });
    }

    try {
      const res = await fetch(`${API_BASE}/api/options?zip=${encodeURIComponent(zip)}`);
      if (!res.ok) return null;
      return await res.json();
    } catch (err) {
      console.error("API fetch failed:", err);
      return null;
    }
  }

  /* ═══════════════════════════════════════════════════════════
   * ZIP VALIDATION & SEARCH
   * ═══════════════════════════════════════════════════════════ */

  /**
   * _isValidZip(zip) — Check if the string is a valid 5-digit ZIP.
   * @param {string} zip
   * @returns {boolean}
   */
  function _isValidZip(zip) {
    return /^\d{5}$/.test(zip);
  }

  /**
   * _showError(msgKey) — Display a validation error below the ZIP input.
   * @param {string} msgKey — i18n translation key
   */
  function _showError(msgKey) {
    elZipError.textContent = i18n.t(msgKey);
    elZipError.classList.remove("hidden");
  }

  /** _hideError() — Hide the ZIP validation error. */
  function _hideError() {
    elZipError.classList.add("hidden");
  }

  /**
   * _showLoading() — Display the loading spinner and hide results.
   */
  function _showLoading() {
    elLoadingSpinner.classList.remove("hidden");
    elResultsSection.classList.add("hidden");
  }

  /**
   * _hideLoading() — Hide the loading spinner.
   */
  function _hideLoading() {
    elLoadingSpinner.classList.add("hidden");
  }

  /* ═══════════════════════════════════════════════════════════
   * RENDERING
   * ═══════════════════════════════════════════════════════════ */

  /**
   * _renderNeedScore(score) — Update the Need Score badge.
   * Colour shifts from green (<40) to amber (40-69) to red (>=70).
   * @param {number} score — 0–100
   */
  function _renderNeedScore(score) {
    elNeedScore.textContent = score;

    /* Colour coding */
    elNeedBadge.className = "need-badge flex items-center gap-3 px-5 py-3 rounded-xl shadow-sm border";
    if (score >= 70) {
      elNeedBadge.classList.add("bg-red-50", "border-red-200", "text-red-800");
    } else if (score >= 40) {
      elNeedBadge.classList.add("bg-amber-50", "border-amber-200", "text-amber-800");
    } else {
      elNeedBadge.classList.add("bg-emerald-50", "border-emerald-200", "text-emerald-800");
    }

    elNeedBadge.classList.remove("hidden");

    /* High-need alert banner */
    if (score >= 70) {
      elNeedAlert.classList.remove("hidden");
    } else {
      elNeedAlert.classList.add("hidden");
    }
  }

  /**
   * _renderResults(data) — Orchestrate rendering of all result sections.
   * @param {Object} data — Full API response object
   */
  function _renderResults(data) {
    currentData = data;

    _renderNeedScore(data.need_score);
    table.render(data.options, elTableContainer);
    alerts.render(data.produce_alert, elAlertContainer);

    elResultsSection.classList.remove("hidden");
    elResultsSection.scrollIntoView({ behavior: "smooth", block: "start" });
  }

  /* ═══════════════════════════════════════════════════════════
   * EVENT HANDLERS
   * ═══════════════════════════════════════════════════════════ */

  /**
   * _handleSearch() — Triggered on button click or Enter key.
   * Validates the ZIP, fetches data, and renders results.
   */
  async function _handleSearch() {
    _hideError();
    const zip = elZipInput.value.trim();

    if (!_isValidZip(zip)) {
      _showError("zip.error_invalid");
      return;
    }

    _showLoading();
    const data = await fetchOptions(zip);
    _hideLoading();

    if (!data) {
      _showError("zip.error_no_results");
      elResultsSection.classList.add("hidden");
      return;
    }

    _renderResults(data);
  }

  /**
   * _handleVoteSubmit(e) — Handle the community vote form submission.
   * In this demo it simply shows a thank-you message.
   * @param {Event} e — form submit event
   */
  function _handleVoteSubmit(e) {
    e.preventDefault();
    elVoteForm.classList.add("hidden");
    elVoteMessage.textContent = i18n.t("vote.thanks");
    elVoteMessage.classList.remove("hidden");

    setTimeout(() => {
      elVoteForm.classList.remove("hidden");
      elVoteMessage.classList.add("hidden");
      elVoteForm.reset();
    }, 3000);
  }

  /**
   * _handleLangChange() — Re-render dynamic content after language toggle.
   * Static data-i18n elements are handled by i18n.translateAll();
   * dynamic content (table, badges, alerts) needs explicit re-render.
   */
  function _handleLangChange() {
    if (currentData) {
      _renderNeedScore(currentData.need_score);
      table.render(currentData.options, elTableContainer);
      alerts.render(currentData.produce_alert, elAlertContainer);
    }
  }

  /* ═══════════════════════════════════════════════════════════
   * INITIALISATION
   * ═══════════════════════════════════════════════════════════ */

  /**
   * init() — Boot the application.
   * Grabs DOM refs, wires event listeners, initialises sub-modules.
   */
  function init() {
    /* Grab DOM elements */
    elZipInput       = document.getElementById("zip-input");
    elZipBtn         = document.getElementById("zip-btn");
    elZipError       = document.getElementById("zip-error");
    elNeedBadge      = document.getElementById("need-badge");
    elNeedScore      = document.getElementById("need-score");
    elNeedAlert      = document.getElementById("need-alert");
    elTableContainer = document.getElementById("table-container");
    elAlertContainer = document.getElementById("alert-container");
    elVoteForm       = document.getElementById("vote-form");
    elVoteMessage    = document.getElementById("vote-message");
    elLangToggle     = document.getElementById("lang-toggle");
    elResultsSection = document.getElementById("results-section");
    elLoadingSpinner = document.getElementById("loading-spinner");

    /* Wire event listeners */
    elZipBtn.addEventListener("click", _handleSearch);
    elZipInput.addEventListener("keydown", (e) => {
      if (e.key === "Enter") _handleSearch();
    });

    elLangToggle.addEventListener("click", () => {
      i18n.toggleLang();
    });

    if (elVoteForm) {
      elVoteForm.addEventListener("submit", _handleVoteSubmit);
    }

    /* Re-render dynamic content on language change */
    window.addEventListener("langchange", _handleLangChange);

    /* Initialise sub-modules */
    cards.init();

    /* Initial i18n pass for static elements */
    i18n.translateAll();
  }

  /* Boot when DOM is ready */
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }

  return { init };
})();
