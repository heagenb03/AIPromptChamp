/**
 * alerts.js — Supply Alert Banner for FoodFlow KC
 *
 * Renders a full-width bilingual banner when the supply-alerts API
 * reports an active fresh produce donation.  Also shows the top 3
 * recommended pantry drop-off locations (from ML routing).
 *
 * PUBLIC API
 *   alerts.render(produceAlert, containerEl) — display or hide the banner
 *   alerts.clear(containerEl)                — remove the banner
 */

const alerts = (() => {
  "use strict";

  /* ─────────────────────────────────────────────────────────
   * render(produceAlert, containerEl)
   * Builds the full-width produce alert banner.  If the alert
   * is not active the banner is cleared.
   *   produceAlert — object from API: { active, pounds, expires_in_hrs, top_drop_locations }
   *   containerEl  — DOM element to render into
   * ───────────────────────────────────────────────────────── */
  function render(produceAlert, containerEl) {
    clear(containerEl);

    if (!produceAlert || !produceAlert.active) return;

    const banner = document.createElement("div");
    banner.className =
      "relative bg-gradient-to-r from-green-600 to-emerald-500 text-white rounded-xl " +
      "p-5 shadow-lg animate-slideDown";

    const bodyText = i18n.t("alert.produce_body", {
      pounds: produceAlert.pounds.toLocaleString(),
      hours: produceAlert.expires_in_hrs,
    });

    /* ── Banner content ───────────────────────────── */
    let locationsHTML = "";
    if (produceAlert.top_drop_locations && produceAlert.top_drop_locations.length > 0) {
      const items = produceAlert.top_drop_locations
        .map(
          (loc) => `
          <div class="flex items-center gap-2 bg-white/20 backdrop-blur-sm rounded-lg px-3 py-2">
            <span class="text-lg">📍</span>
            <div>
              <p class="font-semibold text-sm">${loc.name}</p>
              <p class="text-xs text-green-100">${loc.address || ""}</p>
            </div>
          </div>`
        )
        .join("");

      locationsHTML = `
        <div class="mt-4 pt-4 border-t border-white/30">
          <p class="text-sm font-semibold mb-2" data-i18n="alert.top_locations">${i18n.t("alert.top_locations")}</p>
          <div class="grid grid-cols-1 sm:grid-cols-3 gap-2">
            ${items}
          </div>
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
      ${locationsHTML}
    `;

    /* Dismiss behaviour */
    banner.querySelector(".alert-dismiss").addEventListener("click", () => {
      banner.classList.add("animate-fadeOut");
      setTimeout(() => clear(containerEl), 300);
    });

    containerEl.appendChild(banner);
  }

  /* ─────────────────────────────────────────────────────────
   * clear(containerEl)
   * Removes the alert banner from the container.
   *   containerEl — DOM element to clear
   * ───────────────────────────────────────────────────────── */
  function clear(containerEl) {
    containerEl.innerHTML = "";
  }

  return { render, clear };
})();
