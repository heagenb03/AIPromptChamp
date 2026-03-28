/**
 * alerts.js — Supply Alert Banner for OptimalEats
 *
 * Renders a full-width bilingual banner when the backend reports an
 * active fresh produce (or other) donation.  Displays the top 3
 * ML-routed pantry drop-off locations with routing scores and reasons.
 *
 * PUBLIC API
 *   alerts.render(produceAlert, containerEl)  — display or hide the banner
 *   alerts.clear(containerEl)                 — remove the banner
 */

const alerts = (() => {
  "use strict";

  /**
   * render(alert, containerEl) — Build the produce alert banner.
   * Clears and exits silently if the alert is inactive.
   *
   * @param {Object}      alert        — produce_alert from API response:
   *                                      { active, pounds, expires_in_hrs, item, top_drop_locations[] }
   *                                      Each drop location has { name, address, routing_score, reason }
   * @param {HTMLElement}  containerEl  — DOM element to render into
   */
  function render(alert, containerEl) {
    clear(containerEl);

    if (!alert || !alert.active) return;

    const banner = document.createElement("div");
    banner.className =
      "relative bg-gradient-to-r from-green-600 to-emerald-500 text-white " +
      "rounded-xl p-5 shadow-lg animate-slideDown";

    const bodyText = i18n.t("alert.produce_body", {
      pounds: (alert.pounds || 0).toLocaleString(),
      item:   alert.item || "fresh produce",
      hours:  alert.expires_in_hrs || "?",
    });

    /* ── Drop-location cards ──────────────────────── */
    let locsHTML = "";
    if (alert.top_drop_locations && alert.top_drop_locations.length > 0) {
      const items = alert.top_drop_locations.map((loc) => `
        <div class="bg-white/20 backdrop-blur-sm rounded-lg px-4 py-3">
          <div class="flex items-center gap-2 mb-1">
            <span class="text-lg">📍</span>
            <p class="font-semibold text-sm">${loc.name}</p>
          </div>
          <p class="text-xs text-green-100 mb-1">${loc.address || ""}</p>
          ${loc.routing_score != null ? `<p class="text-xs font-medium"><span data-i18n="alert.score">${i18n.t("alert.score")}</span>: ${loc.routing_score.toFixed(1)}</p>` : ""}
          ${loc.reason ? `<p class="text-xs text-green-100 italic mt-0.5">${loc.reason}</p>` : ""}
        </div>
      `).join("");

      locsHTML = `
        <div class="mt-4 pt-4 border-t border-white/30">
          <p class="text-sm font-semibold mb-2" data-i18n="alert.top_locations">${i18n.t("alert.top_locations")}</p>
          <div class="grid grid-cols-1 sm:grid-cols-3 gap-2">${items}</div>
        </div>`;
    }

    banner.innerHTML = `
      <button class="alert-dismiss absolute top-3 right-3 text-white/70 hover:text-white transition-colors text-xl leading-none" aria-label="Dismiss">&times;</button>
      <div class="flex items-start gap-3">
        <span class="text-3xl flex-shrink-0">🥦</span>
        <div class="flex-1">
          <h3 class="text-lg font-bold" data-i18n="alert.produce_title">${i18n.t("alert.produce_title")}</h3>
          <p class="mt-1 text-sm text-green-100">${bodyText}</p>
        </div>
      </div>
      ${locsHTML}
    `;

    banner.querySelector(".alert-dismiss").addEventListener("click", () => {
      banner.classList.add("animate-fadeOut");
      setTimeout(() => clear(containerEl), 300);
    });

    containerEl.appendChild(banner);
  }

  /**
   * clear(containerEl) — Remove the alert banner.
   * @param {HTMLElement} containerEl
   */
  function clear(containerEl) {
    containerEl.innerHTML = "";
  }

  return { render, clear };
})();
