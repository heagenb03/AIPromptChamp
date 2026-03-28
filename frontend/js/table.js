/**
 * table.js — Cost Comparison Table Renderer for OptimalEats
 *
 * Renders the ranked list of food access options (pantries, stores,
 * delivery services) as an interactive HTML table with cost-tier
 * colour badges.  Clicking a pantry row dispatches a 'toggleCard'
 * CustomEvent consumed by cards.js.
 *
 * PUBLIC API
 *   table.render(options, containerEl)  — build the table from options array
 *   table.clear(containerEl)            — empty the table container
 */

const table = (() => {
  "use strict";

  /* ── Cost-tier visual config ────────────────────────── */
  const TIER_CONFIG = {
    free:   { css: "bg-emerald-100 text-emerald-800 border-emerald-300", icon: "🟢", key: "tier.free" },
    low:    { css: "bg-amber-100 text-amber-800 border-amber-300",      icon: "🟡", key: "tier.low" },
    market: { css: "bg-red-100 text-red-800 border-red-300",            icon: "🔴", key: "tier.market" },
  };

  /* ── Type → i18n key map ────────────────────────────── */
  const TYPE_KEY = {
    pantry:   "type.pantry",
    delivery: "type.delivery",
    store:    "type.store",
  };

  /**
   * _costBadge(costTier, estCost) — Build a coloured <span> badge.
   * @param {string} costTier — 'free' | 'low' | 'market'
   * @param {string} estCost  — display cost string ("$0", "~$35+")
   * @returns {HTMLSpanElement}
   */
  function _costBadge(costTier, estCost) {
    const cfg = TIER_CONFIG[costTier] || TIER_CONFIG.market;
    const span = document.createElement("span");
    span.className = `inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold border ${cfg.css}`;
    span.innerHTML =
      `${cfg.icon} <span data-i18n="${cfg.key}">${i18n.t(cfg.key)}</span>` +
      `<span class="font-normal ml-1 opacity-80">${estCost}</span>`;
    return span;
  }

  /**
   * _distanceText(mi) — Format miles or em-dash for delivery.
   * @param {number|null} mi
   * @returns {string}
   */
  function _distanceText(mi) {
    if (mi === null || mi === undefined) return i18n.t("table.na");
    return `${mi} ${i18n.t("table.miles")}`;
  }

  /**
   * _transitText(accessible) — Translated Yes / No / —.
   * @param {boolean|null} accessible
   * @returns {string}
   */
  function _transitText(accessible) {
    if (accessible === null || accessible === undefined) return i18n.t("table.na");
    return accessible ? i18n.t("table.yes") : i18n.t("table.no");
  }

  /**
   * render(options, containerEl) — Build the full comparison table.
   * @param {Array}       options      — option objects from the API
   * @param {HTMLElement}  containerEl  — DOM element to render into
   */
  function render(options, containerEl) {
    clear(containerEl);

    if (!options || options.length === 0) {
      containerEl.innerHTML =
        `<p class="text-gray-500 text-center py-8" data-i18n="zip.error_no_results">${i18n.t("zip.error_no_results")}</p>`;
      return;
    }

    const wrapper = document.createElement("div");
    wrapper.className = "overflow-x-auto rounded-xl border border-gray-200 shadow-sm";

    const tbl = document.createElement("table");
    tbl.className = "min-w-full divide-y divide-gray-200 text-sm";

    /* ── <thead> ──────────────────────────────────── */
    const thead = document.createElement("thead");
    thead.className = "bg-gray-50";
    const headRow = document.createElement("tr");

    const cols = [
      "table.col_option", "table.col_type", "table.col_cost",
      "table.col_distance", "table.col_transit", "table.col_language",
      "table.col_cuisine",
    ];
    cols.forEach((key) => {
      const th = document.createElement("th");
      th.className = "px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider";
      th.setAttribute("data-i18n", key);
      th.textContent = i18n.t(key);
      headRow.appendChild(th);
    });
    thead.appendChild(headRow);
    tbl.appendChild(thead);

    /* ── <tbody> ──────────────────────────────────── */
    const tbody = document.createElement("tbody");
    tbody.className = "divide-y divide-gray-100 bg-white";

    options.forEach((opt, idx) => {
      const tr = document.createElement("tr");
      tr.className = "hover:bg-blue-50/60 transition-colors";
      tr.setAttribute("data-option-index", idx);

      /* Pantry rows are clickable → dispatch toggleCard */
      if (opt.type === "pantry") {
        tr.classList.add("cursor-pointer");
        tr.addEventListener("click", () => {
          window.dispatchEvent(
            new CustomEvent("toggleCard", { detail: { option: opt, rowEl: tr } })
          );
        });
      }

      /* Name */
      const tdName = document.createElement("td");
      tdName.className = "px-4 py-3 font-medium text-gray-900 whitespace-nowrap";
      tdName.textContent = opt.name;
      if (opt.type === "pantry") {
        const arrow = document.createElement("span");
        arrow.className = "text-blue-400 text-xs align-middle";
        arrow.textContent = " \u25B8";
        tdName.appendChild(arrow);
      }
      tr.appendChild(tdName);

      /* Type */
      const tdType = document.createElement("td");
      tdType.className = "px-4 py-3 text-gray-600";
      const typeKey = TYPE_KEY[opt.type] || "type.store";
      tdType.setAttribute("data-i18n", typeKey);
      tdType.textContent = i18n.t(typeKey);
      tr.appendChild(tdType);

      /* Cost badge */
      const tdCost = document.createElement("td");
      tdCost.className = "px-4 py-3";
      tdCost.appendChild(_costBadge(opt.cost_tier, opt.est_cost));
      tr.appendChild(tdCost);

      /* Distance */
      const tdDist = document.createElement("td");
      tdDist.className = "px-4 py-3 text-gray-600";
      tdDist.textContent = _distanceText(opt.distance_mi);
      tr.appendChild(tdDist);

      /* Transit */
      const tdTransit = document.createElement("td");
      tdTransit.className = "px-4 py-3 text-gray-600";
      tdTransit.textContent = _transitText(opt.transit_accessible);
      tr.appendChild(tdTransit);

      /* Languages */
      const tdLang = document.createElement("td");
      tdLang.className = "px-4 py-3 text-gray-600";
      tdLang.textContent = (opt.languages || []).map((l) => l.toUpperCase()).join(" / ");
      tr.appendChild(tdLang);

      /* Cuisine Tags */
      const tdCuisine = document.createElement("td");
      tdCuisine.className = "px-4 py-3";
      const tags = opt.cuisine_tags || [];
      const CUISINE_COLORS = {
        american:           "bg-blue-100 text-blue-700",
        hispanic:           "bg-orange-100 text-orange-700",
        asian:              "bg-purple-100 text-purple-700",
        african_caribbean:  "bg-rose-100 text-rose-700",
        soul_food:          "bg-amber-100 text-amber-700",
      };
      tags.forEach((tag) => {
        const badge = document.createElement("span");
        const colorCls = CUISINE_COLORS[tag] || "bg-gray-100 text-gray-600";
        badge.className = `inline-block px-2 py-0.5 rounded-full text-xs font-medium mr-1 mb-1 ${colorCls}`;
        const i18nKey = "cuisine." + tag;
        badge.setAttribute("data-i18n", i18nKey);
        badge.textContent = i18n.t(i18nKey);
        tdCuisine.appendChild(badge);
      });
      tr.appendChild(tdCuisine);

      tbody.appendChild(tr);
    });

    tbl.appendChild(tbody);
    wrapper.appendChild(tbl);
    containerEl.appendChild(wrapper);
  }

  /**
   * clear(containerEl) — Empty the table container.
   * @param {HTMLElement} containerEl
   */
  function clear(containerEl) {
    containerEl.innerHTML = "";
  }

  return { render, clear };
})();
