/**
 * paths.js — 3-Path Choice Architecture for OptimalEats
 *
 * Renders the top-level "how do I get food?" decision summary as three
 * hero cards: Free Route, Optimal Route, and Instant Route.  Each card
 * is derived from the existing API response — no backend changes needed.
 *
 * PUBLIC API
 *   paths.render(options, deliveryOptions, batchedDelivery, containerEl)
 */

const paths = (() => {
  "use strict";

  /**
   * _snapBadges(option) — SNAP/EBT pill HTML for a delivery option.
   * @param {Object} option
   * @returns {string} HTML string
   */
  function _snapBadges(option) {
    const badges = [];
    if (option.snap_accepted) badges.push('<span class="inline-block px-2 py-0.5 rounded-full text-xs font-semibold bg-emerald-100 text-emerald-700">SNAP</span>');
    if (option.ebt_accepted)  badges.push('<span class="inline-block px-2 py-0.5 rounded-full text-xs font-semibold bg-blue-100 text-blue-700">EBT</span>');
    return badges.join(" ");
  }

  /**
   * _buildCard(config) — Render a single path card.
   * @param {Object} config — { colorClass, headerBg, label, badge, content }
   * @returns {string} HTML string
   */
  function _buildCard({ borderColor, headerBg, labelKey, badge, content }) {
    return `
      <div class="rounded-xl border-2 ${borderColor} bg-white shadow-sm overflow-hidden flex flex-col">
        <div class="${headerBg} px-4 py-3 flex items-center justify-between">
          <span class="font-bold text-sm tracking-wide">${i18n.t(labelKey)}</span>
          ${badge ? `<span class="text-xs font-semibold px-2 py-0.5 rounded-full bg-white/30">${badge}</span>` : ""}
        </div>
        <div class="px-4 py-4 flex-1 text-sm text-gray-700">
          ${content}
        </div>
      </div>`;
  }

  /**
   * render(options, deliveryOptions, containerEl) — Build and inject the
   * 3-path cards.  Clears containerEl first.
   *
   * @param {Array}       options         — options[] from API response
   * @param {Array}       deliveryOptions — delivery_options[] from API response
   * @param {Object|null} batchedDelivery — batched_delivery from API response
   * @param {HTMLElement} containerEl     — DOM element to render into
   */
  function render(options, deliveryOptions, batchedDelivery, containerEl) {
    containerEl.innerHTML = "";

    const freeOptions = (options || []).filter((o) => o.cost_tier === "free");
    const servingDeliveries = (deliveryOptions || []).filter(
      (d) => d.serves_zip && d.estimated_weekly_total != null
    );

    /* Instant Route: cheapest same-day option */
    const sameDayOptions = servingDeliveries.filter((d) => d.same_day);
    let instantOption = null;
    if (sameDayOptions.length > 0) {
      instantOption = sameDayOptions.reduce((min, d) =>
        d.estimated_weekly_total < min.estimated_weekly_total ? d : min
      );
    }

    /* ── Path A: Free Route (green) ────────────────── */
    let pathAContent;
    if (freeOptions.length === 0) {
      pathAContent = `<p class="text-gray-400 italic">${i18n.t("no_free_options")}</p>`;
    } else {
      const closest = freeOptions[0];
      const extraCount = freeOptions.length - 1;
      const moreKey = extraCount === 1 ? "more_free_options" : "more_free_options_pl";
      pathAContent = `
        <p class="text-2xl font-extrabold text-emerald-600 mb-1">$0</p>
        <p class="font-semibold text-gray-800">${closest.name}</p>
        ${closest.distance_mi != null ? `<p class="text-xs text-gray-500 mt-0.5">${closest.distance_mi} ${i18n.t("table.miles")} away</p>` : ""}
        ${extraCount > 0 ? `<p class="mt-2 text-xs text-gray-500">${i18n.t(moreKey, { count: extraCount })}</p>` : ""}
        <p class="mt-3 text-xs text-gray-400">${i18n.t("see_details_below")}</p>`;
    }

    /* ── Path B: Optimal Route (amber) — batched delivery ─────────────── */
    let pathBContent;
    if (!batchedDelivery) {
      pathBContent = `<p class="text-gray-400 italic">${i18n.t("no_delivery_zip")}</p>`;
    } else {
      pathBContent = `
        <p class="text-2xl font-extrabold text-amber-600 mb-1">$${batchedDelivery.cost_per_delivery.toFixed(2)}<span class="text-sm font-normal text-gray-500">${i18n.t("batched.per_delivery")}</span></p>
        <p class="font-semibold text-gray-800">${i18n.t("batched.provider")}</p>
        <p class="text-xs text-amber-700 font-medium mt-0.5">${i18n.t("batched.eta", { hrs: batchedDelivery.estimated_hrs })}</p>
        <div class="flex flex-wrap gap-1 mt-1">${_snapBadges(batchedDelivery)}</div>
        <p class="text-xs text-gray-400 mt-1">${i18n.t("batched.note")}</p>`;
    }

    /* ── Path C: Instant Route (blue) ──────────────── */
    let pathCContent;
    if (!instantOption) {
      pathCContent = `<p class="text-gray-400 italic">${i18n.t("no_delivery_zip")}</p>`;
    } else {
      pathCContent = `
        <p class="text-2xl font-extrabold text-blue-600 mb-1">$${instantOption.estimated_weekly_total.toFixed(2)}<span class="text-sm font-normal text-gray-500">/wk</span></p>
        <p class="font-semibold text-gray-800">${instantOption.name}</p>
        <p class="text-xs text-blue-600 font-medium mt-0.5">${i18n.t("same_day_delivery")}</p>
        <div class="flex flex-wrap gap-1 mt-1">${_snapBadges(instantOption)}</div>`;
    }

    const wrapper = document.createElement("div");
    wrapper.innerHTML = `
      <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
        ${_buildCard({ borderColor: "border-emerald-500", headerBg: "bg-emerald-500 text-white", labelKey: "free_route_label", badge: null, content: pathAContent })}
        ${_buildCard({ borderColor: "border-amber-400",   headerBg: "bg-amber-400 text-white",   labelKey: "optimal_route_label", badge: i18n.t("best_value_badge"), content: pathBContent })}
        ${_buildCard({ borderColor: "border-blue-500",    headerBg: "bg-blue-500 text-white",    labelKey: "instant_route_label", badge: null, content: pathCContent })}
      </div>`;

    containerEl.appendChild(wrapper.firstElementChild);
  }

  return { render };
})();
