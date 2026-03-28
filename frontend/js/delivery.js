/**
 * delivery.js — Delivery Options Table Renderer
 *
 * Renders the `delivery_options` array from the API response as a
 * formatted table below the main options table.  Only shown when
 * `delivery_necessity_flag` is true.
 *
 * PUBLIC API
 *   delivery.render(options, container) — render table into container element
 *
 * Depends on: i18n.js (loaded before this).
 */

const delivery = (() => {
  "use strict";

  /** Cost-tier → Tailwind colour classes (mirrors table.js convention). */
  const TIER_STYLE = {
    free:   "bg-emerald-100 text-emerald-700 border-emerald-200",
    low:    "bg-amber-100   text-amber-700   border-amber-200",
    market: "bg-red-100     text-red-700     border-red-200",
  };

  /**
   * _pill(text, classes) — Inline badge/pill element string.
   * @param {string} text
   * @param {string} classes — Tailwind classes
   * @returns {string} HTML string
   */
  function _pill(text, classes) {
    return `<span class="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-semibold ${classes}">${text}</span>`;
  }

  /**
   * _buildRow(opt) — Build a <tr> string for one delivery option.
   * @param {Object} opt — delivery option object from API
   * @returns {string} HTML string
   */
  function _buildRow(opt) {
    const tierClass = TIER_STYLE[opt.cost_tier] || TIER_STYLE.market;

    const snapBadge = opt.snap_accepted
      ? _pill(i18n.t("delivery.snap"), "bg-emerald-100 text-emerald-700")
      : "";
    const ebtBadge = opt.ebt_accepted
      ? _pill(i18n.t("delivery.ebt"), "bg-blue-100 text-blue-700")
      : "";
    const badgeCell = [snapBadge, ebtBadge].filter(Boolean).join(" ") || i18n.t("table.na");

    const feeDisplay =
      opt.delivery_fee === 0
        ? _pill(i18n.t("tier.free"), "bg-emerald-100 text-emerald-700 border border-emerald-200")
        : _pill(`$${opt.delivery_fee.toFixed(2)}`, `border ${tierClass}`);

    const orderMin =
      opt.order_minimum > 0
        ? `$${opt.order_minimum.toFixed(2)}`
        : i18n.t("table.na");

    let totalCell;
    if (opt.subsidy_applied && opt.subsidy_applied > 0) {
      totalCell = `
        <span class="line-through text-gray-400 text-xs">$${opt.market_rate.toFixed(2)}</span>
        <span class="block text-emerald-600 font-semibold">$${opt.final_cost.toFixed(2)}</span>
        <span class="block text-xs text-emerald-500">-$${opt.subsidy_applied.toFixed(2)} ${i18n.t("delivery.subsidy_discount")}</span>`;
    } else {
      totalCell = `$${opt.estimated_weekly_total.toFixed(2)}`;
    }

    const sameDay = opt.same_day ? i18n.t("table.yes") : i18n.t("table.no");

    const notesLine = opt.notes
      ? `<span class="block text-xs text-gray-400 font-normal mt-0.5">${opt.notes}</span>`
      : "";

    return `
      <tr class="hover:bg-gray-50 transition-colors">
        <td class="px-4 py-3 font-medium text-gray-900 text-sm">
          ${opt.name}${notesLine}
        </td>
        <td class="px-4 py-3 text-sm">${badgeCell}</td>
        <td class="px-4 py-3 text-sm">${feeDisplay}</td>
        <td class="px-4 py-3 text-sm text-gray-600">${orderMin}</td>
        <td class="px-4 py-3 text-sm font-semibold text-gray-900">${totalCell}</td>
        <td class="px-4 py-3 text-sm text-gray-600">${sameDay}</td>
      </tr>`;
  }

  /**
   * _buildBatchedRow(bd) — Build the highlighted OptimalEats Batched Delivery row.
   * @param {Object} bd — batched_delivery object from API
   * @returns {string} HTML string
   */
  function _buildBatchedRow(bd) {
    const snapBadge = bd.snap_accepted
      ? _pill(i18n.t("delivery.snap"), "bg-emerald-100 text-emerald-700")
      : "";
    const ebtBadge = bd.ebt_accepted
      ? _pill(i18n.t("delivery.ebt"), "bg-blue-100 text-blue-700")
      : "";
    const badgeCell = [snapBadge, ebtBadge].filter(Boolean).join(" ") || i18n.t("table.na");

    const feeDisplay = _pill(
      `$${bd.cost_per_delivery.toFixed(2)}`,
      "bg-amber-100 text-amber-700 border border-amber-200"
    );

    return `
      <tr class="bg-amber-50 border-l-4 border-amber-400">
        <td class="px-4 py-3 text-sm">
          <span class="font-semibold text-amber-900">${i18n.t("batched.provider")}</span>
          <span class="ml-2 inline-flex items-center px-1.5 py-0.5 rounded text-xs font-semibold bg-amber-400 text-white">${i18n.t("batched.recommended")}</span>
          <span class="block text-xs text-amber-700 font-normal mt-0.5">${i18n.t("batched.eta", { hrs: bd.estimated_hrs })}</span>
          <span class="block text-xs text-gray-400 font-normal mt-0.5">${i18n.t("batched.note")}</span>
        </td>
        <td class="px-4 py-3 text-sm">${badgeCell}</td>
        <td class="px-4 py-3 text-sm">${feeDisplay}</td>
        <td class="px-4 py-3 text-sm text-gray-500">${i18n.t("table.na")}</td>
        <td class="px-4 py-3 text-sm font-semibold text-amber-800">$${bd.cost_per_delivery.toFixed(2)}${i18n.t("batched.per_delivery")}</td>
        <td class="px-4 py-3 text-sm text-gray-500">${i18n.t("table.na")}</td>
      </tr>`;
  }

  /**
   * render(options, container, batchedDelivery?) — Build and inject the full delivery table.
   * Clears the container if options is empty/null and no batchedDelivery.
   * @param {Array}       options         — delivery_options from API response
   * @param {HTMLElement} container       — target DOM element
   * @param {Object|null} batchedDelivery — batched_delivery from API response (optional)
   */
  function render(options, container, batchedDelivery) {
    if (!container) return;

    const hasOptions = options && options.length > 0;
    if (!hasOptions && !batchedDelivery) {
      container.innerHTML = "";
      return;
    }

    const batchedRow = batchedDelivery ? _buildBatchedRow(batchedDelivery) : "";
    const rows = hasOptions ? options.map(_buildRow).join("") : "";

    container.innerHTML = `
      <div class="overflow-x-auto rounded-xl border border-gray-200 shadow-sm">
        <table class="w-full text-left text-sm">
          <thead class="bg-gray-50 border-b border-gray-200">
            <tr>
              <th class="px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wider">${i18n.t("delivery.col_provider")}</th>
              <th class="px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wider">${i18n.t("delivery.col_snap_ebt")}</th>
              <th class="px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wider">${i18n.t("delivery.col_fee")}</th>
              <th class="px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wider">${i18n.t("delivery.col_order_min")}</th>
              <th class="px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wider">${i18n.t("delivery.col_total")}</th>
              <th class="px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wider">${i18n.t("delivery.col_same_day")}</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-gray-100 bg-white">
            ${batchedRow}
            ${rows}
          </tbody>
        </table>
      </div>`;
  }

  return { render };
})();
