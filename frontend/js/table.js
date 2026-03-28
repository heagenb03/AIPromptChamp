/**
 * table.js — Cost Comparison Table Renderer for FoodFlow KC
 *
 * Renders the ranked list of food access options (pantries, stores,
 * delivery services) into an interactive HTML table with cost-tier
 * color badges.  Rows are clickable to expand pantry detail cards
 * (handled by cards.js).
 *
 * PUBLIC API
 *   table.render(options, containerEl)  — build the table from an array of option objects
 *   table.clear(containerEl)            — empty the table container
 */

const table = (() => {
  "use strict";

  /* ─────────────────────────────────────────────────────────
   * COST TIER CONFIG
   * Maps the API's cost_tier string to a colour scheme and
   * translation key for the badge.
   * ───────────────────────────────────────────────────────── */
  const TIER_CONFIG = {
    free:   { color: "bg-emerald-100 text-emerald-800 border-emerald-300", icon: "🟢", i18nKey: "tier.free" },
    low:    { color: "bg-amber-100 text-amber-800 border-amber-300",       icon: "🟡", i18nKey: "tier.low" },
    market: { color: "bg-red-100 text-red-800 border-red-300",             icon: "🔴", i18nKey: "tier.market" },
  };

  /* ─────────────────────────────────────────────────────────
   * TYPE CONFIG
   * Maps option type to an i18n key for the "Type" column.
   * ───────────────────────────────────────────────────────── */
  const TYPE_I18N = {
    pantry:   "type.pantry",
    delivery: "type.delivery",
    store:    "type.store",
  };

  /* ─────────────────────────────────────────────────────────
   * _buildCostBadge(costTier, estCost)
   * Returns a styled <span> element showing the tier badge.
   *   costTier  — 'free' | 'low' | 'market'
   *   estCost   — display string like "$0" or "~$35+"
   * ───────────────────────────────────────────────────────── */
  function _buildCostBadge(costTier, estCost) {
    const cfg = TIER_CONFIG[costTier] || TIER_CONFIG.market;
    const span = document.createElement("span");
    span.className = `inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-semibold border ${cfg.color}`;
    span.innerHTML = `${cfg.icon} <span data-i18n="${cfg.i18nKey}">${i18n.t(cfg.i18nKey)}</span> <span class="font-normal ml-1">${estCost}</span>`;
    return span;
  }

  /* ─────────────────────────────────────────────────────────
   * _formatDistance(distMi)
   * Returns a readable distance string or em-dash for delivery.
   *   distMi — number (miles) or null
   * ───────────────────────────────────────────────────────── */
  function _formatDistance(distMi) {
    if (distMi === null || distMi === undefined) return i18n.t("table.na");
    return `${distMi} ${i18n.t("table.miles")}`;
  }

  /* ─────────────────────────────────────────────────────────
   * _transitLabel(accessible)
   * Returns translated Yes/No/— for transit accessibility.
   *   accessible — boolean | null
   * ───────────────────────────────────────────────────────── */
  function _transitLabel(accessible) {
    if (accessible === null || accessible === undefined) return i18n.t("table.na");
    return accessible ? i18n.t("table.yes") : i18n.t("table.no");
  }

  /* ─────────────────────────────────────────────────────────
   * render(options, containerEl)
   * Builds the full comparison table and inserts it into the
   * given container element.
   *   options      — array of option objects from the API
   *   containerEl  — DOM element to render into
   * ───────────────────────────────────────────────────────── */
  function render(options, containerEl) {
    clear(containerEl);

    if (!options || options.length === 0) {
      containerEl.innerHTML = `<p class="text-gray-500 text-center py-8" data-i18n="zip.error_no_results">${i18n.t("zip.error_no_results")}</p>`;
      return;
    }

    const wrapper = document.createElement("div");
    wrapper.className = "overflow-x-auto rounded-xl border border-gray-200 shadow-sm";

    const tbl = document.createElement("table");
    tbl.className = "min-w-full divide-y divide-gray-200 text-sm";

    /* ── thead ─────────────────────────────────────── */
    const thead = document.createElement("thead");
    thead.className = "bg-gray-50";
    const headRow = document.createElement("tr");
    const columns = [
      "table.col_option",
      "table.col_type",
      "table.col_cost",
      "table.col_distance",
      "table.col_transit",
      "table.col_language",
      "table.col_notes",
    ];
    columns.forEach((key) => {
      const th = document.createElement("th");
      th.className = "px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider";
      th.setAttribute("data-i18n", key);
      th.textContent = i18n.t(key);
      headRow.appendChild(th);
    });
    thead.appendChild(headRow);
    tbl.appendChild(thead);

    /* ── tbody ─────────────────────────────────────── */
    const tbody = document.createElement("tbody");
    tbody.className = "divide-y divide-gray-100 bg-white";

    options.forEach((opt, idx) => {
      const tr = document.createElement("tr");
      tr.className = "hover:bg-blue-50/50 transition-colors cursor-pointer";
      tr.setAttribute("data-option-index", idx);

      /* Clicking a pantry row toggles the detail card beneath it */
      if (opt.type === "pantry") {
        tr.addEventListener("click", () => {
          window.dispatchEvent(
            new CustomEvent("toggleCard", { detail: { option: opt, rowEl: tr } })
          );
        });
      }

      /* Option name */
      const tdName = document.createElement("td");
      tdName.className = "px-4 py-3 font-medium text-gray-900 whitespace-nowrap";
      tdName.textContent = opt.name;
      tr.appendChild(tdName);

      /* Type */
      const tdType = document.createElement("td");
      tdType.className = "px-4 py-3 text-gray-600";
      const typeKey = TYPE_I18N[opt.type] || "type.store";
      tdType.setAttribute("data-i18n", typeKey);
      tdType.textContent = i18n.t(typeKey);
      tr.appendChild(tdType);

      /* Est. Cost (badge) */
      const tdCost = document.createElement("td");
      tdCost.className = "px-4 py-3";
      tdCost.appendChild(_buildCostBadge(opt.cost_tier, opt.est_cost));
      tr.appendChild(tdCost);

      /* Distance */
      const tdDist = document.createElement("td");
      tdDist.className = "px-4 py-3 text-gray-600";
      tdDist.textContent = _formatDistance(opt.distance_mi);
      tr.appendChild(tdDist);

      /* Transit */
      const tdTransit = document.createElement("td");
      tdTransit.className = "px-4 py-3 text-gray-600";
      tdTransit.textContent = _transitLabel(opt.transit_accessible);
      tr.appendChild(tdTransit);

      /* Language */
      const tdLang = document.createElement("td");
      tdLang.className = "px-4 py-3 text-gray-600";
      tdLang.textContent = (opt.languages || []).map((l) => l.toUpperCase()).join(" / ");
      tr.appendChild(tdLang);

      /* Notes */
      const tdNotes = document.createElement("td");
      tdNotes.className = "px-4 py-3 text-gray-500 text-xs";
      tdNotes.textContent = opt.notes || "";
      tr.appendChild(tdNotes);

      tbody.appendChild(tr);
    });

    tbl.appendChild(tbody);
    wrapper.appendChild(tbl);
    containerEl.appendChild(wrapper);
  }

  /* ─────────────────────────────────────────────────────────
   * clear(containerEl)
   * Empties the table container.
   *   containerEl — DOM element to clear
   * ───────────────────────────────────────────────────────── */
  function clear(containerEl) {
    containerEl.innerHTML = "";
  }

  return { render, clear };
})();
