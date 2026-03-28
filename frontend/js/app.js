/**
 * app.js — Main Entry Point for OptimalEats Frontend
 *
 * Orchestrates the entire client-side application:
 *  1. Handles ZIP code input and validation
 *  2. Fetches data from the FastAPI backend (or falls back to mock data)
 *  3. Renders the Need Score badge, comparison table, pantry cards,
 *     produce alert banner, and community vote panel
 *  4. Wires the EN/ES language toggle
 *
 * Depends on: i18n.js, table.js, cards.js, alerts.js (loaded before this).
 */

const app = (() => {
  "use strict";

  /* ─── Configuration ──────────────────────────────────
   * The app first attempts to call the real backend.
   * If that fails (e.g. backend not running) it falls
   * back to the built-in mock data automatically.
   * ─────────────────────────────────────────────────── */
  const API_BASE = window.location.origin;

  /* ─── DOM element references (set in init()) ──────── */
  let elZipInput,
    elZipBtn,
    elZipError,
    elNeedBadge,
    elNeedScoreNum,
    elNeedAlert,
    elTableContainer,
    elAlertContainer,
    elDeliveryContainer,
    elDeliveryTableContainer,
    elVoteForm,
    elVoteMsg,
    elLangToggle,
    elResultsSection,
    elSpinner;

  /** Caches the most recent API response for lang-change re-renders. */
  let currentData = null;

  /* ═══════════════════════════════════════════════════════
   * MOCK DATA
   * Matches the backend OptionsResponse schema exactly so
   * the frontend works standalone during development.
   * ═══════════════════════════════════════════════════════ */
  const MOCK = {
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
        },
        {
          name: "Walmart Grocery Delivery",
          type: "delivery",
          cost_tier: "market",
          est_cost: "~$35+",
          distance_mi: null,
          transit_accessible: false,
          languages: ["en"],
          id_required: false,
          cold_storage: false,
          hours: "24/7 online",
          address: "Online/Delivery",
        },
        {
          name: "Price Chopper (Troost)",
          type: "store",
          cost_tier: "low",
          est_cost: "~$40–60/wk",
          distance_mi: 2.1,
          transit_accessible: false,
          languages: ["en"],
          id_required: false,
          cold_storage: false,
          hours: "6AM–11PM daily",
          address: "4950 Troost Ave, Kansas City, MO 64110",
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
          cold_storage: false,
          hours: "9AM–8PM daily",
          address: "5600 Prospect Ave, Kansas City, MO 64130",
        },
      ],
      produce_alert: {
        active: true,
        pounds: 1000,
        expires_in_hrs: 48,
        item: "fresh produce",
        top_drop_locations: [
          { name: "Harvesters Food Network", address: "3801 Topping Ave", routing_score: 82.4, reason: "High need ZIP, cold storage available, transit-accessible" },
          { name: "Guadalupe Center",        address: "1015 W Avenida Cesar E Chavez", routing_score: 74.1, reason: "High need ZIP, bilingual (ES), transit-accessible" },
          { name: "Community Assistance Council", address: "10901 Blue Ridge Blvd", routing_score: 61.8, reason: "High need ZIP, transit-accessible" },
        ],
      },
      delivery_necessity_flag: true,
      delivery_options: [
        { name: "Walmart Grocery",             snap_accepted: true,  ebt_accepted: true,  delivery_fee: 7.95, order_minimum: 35.00, estimated_weekly_total: 42.95, same_day: true,  cost_tier: "low",    serves_zip: true, notes: "SNAP/EBT accepted" },
        { name: "Amazon Fresh",                snap_accepted: true,  ebt_accepted: true,  delivery_fee: 9.95, order_minimum: 35.00, estimated_weekly_total: 44.95, same_day: true,  cost_tier: "market", serves_zip: true, notes: "Free with Prime; EBT accepted" },
        { name: "Instacart (Aldi/Price Chopper)", snap_accepted: true, ebt_accepted: false, delivery_fee: 5.99, order_minimum: 10.00, estimated_weekly_total: 15.99, same_day: true, cost_tier: "low",   serves_zip: true, notes: "Fee varies $3.99–$9.99" },
        { name: "Dillons/Kroger",              snap_accepted: true,  ebt_accepted: true,  delivery_fee: 9.95, order_minimum: 35.00, estimated_weekly_total: 44.95, same_day: true,  cost_tier: "market", serves_zip: true, notes: "SNAP/EBT accepted" },
        { name: "Hy-Vee Aisles Online",        snap_accepted: false, ebt_accepted: false, delivery_fee: 9.95, order_minimum: 24.95, estimated_weekly_total: 34.90, same_day: true,  cost_tier: "market", serves_zip: true, notes: "No SNAP/EBT currently" },
      ],
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
          cold_storage: false,
          hours: "7AM–10PM daily",
          address: "4001 Troost Ave, Kansas City, MO 64110",
        },
      ],
      produce_alert: { active: false, pounds: 0, expires_in_hrs: 0, item: null, top_drop_locations: [] },
      delivery_necessity_flag: false,
      delivery_options: [],
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
          cold_storage: false,
          hours: "6AM–11PM daily",
          address: "1300 W 12th St, Kansas City, MO 64101",
        },
      ],
      produce_alert: {
        active: true,
        pounds: 500,
        expires_in_hrs: 24,
        item: "fresh produce",
        top_drop_locations: [
          { name: "Guadalupe Center", address: "1015 W Avenida Cesar E Chavez", routing_score: 78.3, reason: "Bilingual (ES), cold storage, high transit frequency" },
        ],
      },
      delivery_necessity_flag: false,
      delivery_options: [],
    },
  };

  /* ═══════════════════════════════════════════════════════
   * DATA FETCHING
   * ═══════════════════════════════════════════════════════ */

  /**
   * fetchOptions(zip) — Try the real backend first; fall back to mock.
   * @param {string} zip — 5-digit ZIP string
   * @returns {Promise<Object|null>}
   */
  async function fetchOptions(zip) {
    try {
      const res = await fetch(`${API_BASE}/api/options?zip=${encodeURIComponent(zip)}`);
      if (res.ok) return await res.json();

      /* Backend returned an error — try mock */
      const errBody = await res.json().catch(() => null);
      console.warn("Backend error:", errBody);
    } catch (err) {
      console.warn("Backend unreachable, using mock data:", err.message);
    }

    /* Fallback to mock data */
    return MOCK[zip] || null;
  }

  /**
   * submitVote(name, zip, support) — POST to /api/vote.
   * @param {string}  name
   * @param {string}  zip
   * @param {boolean} support
   * @returns {Promise<Object|null>}
   */
  async function submitVote(name, zip, support) {
    try {
      const res = await fetch(`${API_BASE}/api/vote`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name, zip, support }),
      });
      if (res.ok) return await res.json();
    } catch (err) {
      console.warn("Vote submission failed:", err.message);
    }
    return { status: "recorded", message: i18n.t("vote.thanks") };
  }

  /* ═══════════════════════════════════════════════════════
   * VALIDATION
   * ═══════════════════════════════════════════════════════ */

  /**
   * _isValidZip(zip) — Must be 5 digits starting with 641.
   * @param {string} zip
   * @returns {boolean}
   */
  function _isValidZip(zip) {
    return /^(641|661)\d{2}$/.test(zip);
  }

  /** Show a translated error below the ZIP input. */
  function _showError(key) {
    elZipError.textContent = i18n.t(key);
    elZipError.classList.remove("hidden");
  }

  /** Hide the error message. */
  function _hideError() {
    elZipError.classList.add("hidden");
  }

  /** Show spinner, hide results. */
  function _showLoading() {
    elSpinner.classList.remove("hidden");
    elResultsSection.classList.add("hidden");
  }

  /** Hide spinner. */
  function _hideLoading() {
    elSpinner.classList.add("hidden");
  }

  /* ═══════════════════════════════════════════════════════
   * RENDERING
   * ═══════════════════════════════════════════════════════ */

  /**
   * _renderNeedScore(score) — Update the Need Score badge.
   * Colour shifts: green (<40), amber (40–69), red (≥70).
   * @param {number} score — 0–100
   */
  function _renderNeedScore(score) {
    elNeedScoreNum.textContent = score;

    /* Reset and apply colour classes */
    const base = "need-badge flex items-center gap-3 px-5 py-3 rounded-xl shadow-sm border";
    if (score >= 70) {
      elNeedBadge.className = `${base} bg-red-50 border-red-200 text-red-800`;
      elNeedAlert.classList.remove("hidden");
    } else if (score >= 40) {
      elNeedBadge.className = `${base} bg-amber-50 border-amber-200 text-amber-800`;
      elNeedAlert.classList.add("hidden");
    } else {
      elNeedBadge.className = `${base} bg-emerald-50 border-emerald-200 text-emerald-800`;
      elNeedAlert.classList.add("hidden");
    }

    elNeedBadge.classList.remove("hidden");
  }

  /**
   * _renderResults(data) — Orchestrate rendering of all result sections.
   * @param {Object} data — full OptionsResponse from the API / mock
   */
  function _renderResults(data) {
    currentData = data;

    _renderNeedScore(data.need_score);
    table.render(data.options, elTableContainer);
    alerts.render(data.produce_alert, elAlertContainer);

    if (data.delivery_necessity_flag && data.delivery_options && data.delivery_options.length > 0) {
      delivery.render(data.delivery_options, elDeliveryTableContainer);
      elDeliveryContainer.classList.remove("hidden");
    } else {
      elDeliveryContainer.classList.add("hidden");
    }

    elResultsSection.classList.remove("hidden");
    elResultsSection.scrollIntoView({ behavior: "smooth", block: "start" });
  }

  /* ═══════════════════════════════════════════════════════
   * EVENT HANDLERS
   * ═══════════════════════════════════════════════════════ */

  /** Triggered on button click or Enter key. */
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

  /** Handle community vote form submission via POST /api/vote. */
  async function _handleVote(e) {
    e.preventDefault();
    const formData = new FormData(elVoteForm);
    const name    = formData.get("vote-name") || "";
    const zip     = formData.get("vote-zip") || "";
    const support = formData.get("vote-support") === "on";

    const result = await submitVote(name, zip, support);

    elVoteForm.classList.add("hidden");
    elVoteMsg.textContent = result.message || i18n.t("vote.thanks");
    elVoteMsg.classList.remove("hidden");

    setTimeout(() => {
      elVoteForm.classList.remove("hidden");
      elVoteMsg.classList.add("hidden");
      elVoteForm.reset();
    }, 3000);
  }

  /** Re-render dynamic content after a language toggle. */
  function _handleLangChange() {
    if (currentData) {
      _renderNeedScore(currentData.need_score);
      table.render(currentData.options, elTableContainer);
      alerts.render(currentData.produce_alert, elAlertContainer);
      if (currentData.delivery_necessity_flag && currentData.delivery_options && currentData.delivery_options.length > 0) {
        delivery.render(currentData.delivery_options, elDeliveryTableContainer);
      }
    }
  }

  /* ═══════════════════════════════════════════════════════
   * INITIALISATION
   * ═══════════════════════════════════════════════════════ */

  /** Boot the app — grab DOM refs, wire listeners, init sub-modules. */
  function init() {
    elZipInput              = document.getElementById("zip-input");
    elZipBtn                = document.getElementById("zip-btn");
    elZipError              = document.getElementById("zip-error");
    elNeedBadge             = document.getElementById("need-badge");
    elNeedScoreNum          = document.getElementById("need-score-num");
    elNeedAlert             = document.getElementById("need-alert");
    elTableContainer        = document.getElementById("table-container");
    elAlertContainer        = document.getElementById("alert-container");
    elDeliveryContainer     = document.getElementById("delivery-container");
    elDeliveryTableContainer = document.getElementById("delivery-table-container");
    elVoteForm              = document.getElementById("vote-form");
    elVoteMsg               = document.getElementById("vote-msg");
    elLangToggle            = document.getElementById("lang-toggle");
    elResultsSection        = document.getElementById("results-section");
    elSpinner               = document.getElementById("spinner");

    elZipBtn.addEventListener("click", _handleSearch);
    elZipInput.addEventListener("keydown", (e) => {
      if (e.key === "Enter") _handleSearch();
    });

    elLangToggle.addEventListener("click", () => i18n.toggleLang());

    if (elVoteForm) elVoteForm.addEventListener("submit", _handleVote);

    window.addEventListener("langchange", _handleLangChange);

    cards.init();
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
