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

    /* ── Urgency tier based on expiry ─────────────── */
    const hrs = alert.expires_in_hrs || 999;
    let urgencyLabel, urgencyBadgeCss, bannerGradient, locTextCss;
    if (hrs <= 12) {
      urgencyLabel   = i18n.t("urgent_label");
      urgencyBadgeCss = "bg-red-200 text-red-900";
      bannerGradient  = "from-red-700 to-red-500 text-white";
      locTextCss      = "text-red-100";
    } else if (hrs <= 24) {
      urgencyLabel   = i18n.t("today_label");
      urgencyBadgeCss = "bg-orange-200 text-orange-900";
      bannerGradient  = "from-orange-600 to-amber-500 text-white";
      locTextCss      = "text-orange-100";
    } else {
      urgencyLabel   = i18n.t("active_label");
      urgencyBadgeCss = "bg-yellow-200 text-yellow-900";
      bannerGradient  = "from-yellow-600 to-yellow-400 text-gray-900";
      locTextCss      = "text-yellow-800";
    }

    const hasPounds = alert.pounds > 0;
    const hasHours  = alert.expires_in_hrs > 0;
    const item      = alert.item || "fresh produce";
    const bodyText  = (hasPounds && hasHours)
      ? i18n.t("alert.produce_body", {
          pounds: alert.pounds.toLocaleString(),
          item,
          hours: alert.expires_in_hrs,
        })
      : i18n.t("alert.produce_body_simple", { item });

    /* ── Drop-location cards ──────────────────────── */
    let locsHTML = "";
    if (alert.top_drop_locations && alert.top_drop_locations.length > 0) {
      const items = alert.top_drop_locations.map((loc) => `
        <div class="bg-white/20 backdrop-blur-sm rounded-lg px-4 py-3">
          <div class="flex items-center gap-2 mb-1">
            <span class="text-lg">📍</span>
            <p class="font-semibold text-sm">${loc.name}</p>
          </div>
          <p class="text-xs ${locTextCss} mb-1">${loc.address || ""}</p>
          ${loc.routing_score != null ? `<p class="text-xs font-medium"><span data-i18n="alert.score">${i18n.t("alert.score")}</span>: ${loc.routing_score.toFixed(1)}</p>` : ""}
          ${loc.reason ? `<p class="text-xs ${locTextCss} italic mt-0.5">${loc.reason}</p>` : ""}
        </div>
      `).join("");

      locsHTML = `
        <div class="mt-4 pt-4 border-t border-white/30">
          <p class="text-sm font-semibold mb-2">${i18n.t("routing_to_label")}:</p>
          <div class="grid grid-cols-1 sm:grid-cols-3 gap-2">${items}</div>
        </div>`;
    }

    const banner = document.createElement("div");
    banner.className =
      `relative bg-gradient-to-r ${bannerGradient} ` +
      "rounded-xl p-5 shadow-lg animate-slideDown";

    banner.innerHTML = `
      <div class="flex items-start justify-between gap-3 mb-1">
        <div class="flex items-center gap-3">
          <span class="text-3xl flex-shrink-0">🚚</span>
          <h3 class="text-lg font-bold">${i18n.t("active_mission_label")}</h3>
        </div>
        <div class="flex items-center gap-2 flex-shrink-0">
          <span class="text-xs font-bold px-2.5 py-1 rounded-full ${urgencyBadgeCss}">${urgencyLabel}</span>
          <button class="alert-dismiss text-current opacity-60 hover:opacity-100 transition-opacity text-xl leading-none" aria-label="Dismiss">&times;</button>
        </div>
      </div>
      <p class="mt-1 text-sm opacity-90 ml-12">${bodyText}</p>
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

  /**
   * renderVoteBanner(communityVote, containerEl) — Render community vote banner.
   * Shows 2 priority zones with need scores, Spanish badge, and days-left countdown.
   * Spanish-first: if any zone is spanish_dominant, renders ES regardless of toggle.
   *
   * @param {Object|null} communityVote — community_vote from API response:
   *   { active, deadline, zones: [{ zip, need_score, spanish_dominant, label }], total_zones }
   * @param {HTMLElement}  containerEl  — DOM element to render into
   */
  function renderVoteBanner(communityVote, containerEl) {
    containerEl.innerHTML = "";

    if (!communityVote || !communityVote.active || !communityVote.zones?.length) return;

    const deadline = new Date(communityVote.deadline + "T00:00:00");
    const daysLeft = Math.max(0, Math.ceil((deadline - Date.now()) / 86400000));

    const hasSpanishZone = communityVote.zones.some((z) => z.spanish_dominant);

    const zoneCards = communityVote.zones.map((zone) => `
      <div class="bg-white/20 backdrop-blur-sm rounded-lg px-4 py-3">
        <p class="text-xs font-semibold uppercase tracking-wider opacity-70 mb-1">${i18n.t("vote_banner.zone_label")}</p>
        <p class="font-bold text-sm mb-1">${zone.label} (${zone.zip})</p>
        <p class="text-xs mb-1">${i18n.t("vote_banner.need_score", { score: zone.need_score })}</p>
        ${zone.spanish_dominant ? `<span class="inline-block text-xs font-semibold bg-white/30 rounded-full px-2 py-0.5">🇲🇽 ${i18n.t("vote_banner.spanish_note")}</span>` : ""}
      </div>
    `).join("");

    const banner = document.createElement("div");
    banner.className =
      "relative bg-gradient-to-r from-indigo-700 to-purple-600 text-white " +
      "rounded-xl p-5 shadow-lg animate-slideDown";

    banner.innerHTML = `
      <div class="flex items-start justify-between gap-3 mb-2">
        <div class="flex items-center gap-3">
          <span class="text-3xl flex-shrink-0">🗳️</span>
          <h3 class="text-lg font-bold">${i18n.t("vote_banner.heading")}</h3>
        </div>
        <div class="flex items-center gap-2 flex-shrink-0">
          <span class="text-xs font-bold px-2.5 py-1 rounded-full bg-white/20">${i18n.t("vote_banner.days_left", { days: daysLeft })}</span>
          <button class="vote-banner-dismiss opacity-60 hover:opacity-100 transition-opacity text-xl leading-none" aria-label="Dismiss">&times;</button>
        </div>
      </div>
      <p class="text-sm opacity-90 ml-12 mb-4">${i18n.t("vote_banner.desc")}</p>
      <div class="grid grid-cols-1 sm:grid-cols-2 gap-3 ml-12 mb-4">${zoneCards}</div>
      <div class="ml-12">
        <a href="#vote-form"
           class="inline-block bg-white text-indigo-700 font-bold text-sm px-4 py-2 rounded-lg hover:bg-indigo-50 transition-colors">
          ${i18n.t("vote_banner.vote_now")} →
        </a>
      </div>
    `;

    banner.querySelector(".vote-banner-dismiss").addEventListener("click", () => {
      banner.classList.add("animate-fadeOut");
      setTimeout(() => { containerEl.innerHTML = ""; }, 300);
    });

    containerEl.appendChild(banner);
  }

  return { render, clear, renderVoteBanner };
})();
