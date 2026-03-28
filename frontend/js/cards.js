/**
 * cards.js — Pantry Detail Card Component for OptimalEats
 *
 * Renders expandable detail cards below table rows when the user
 * clicks a pantry option.  Each card shows hours, address, language
 * support, ID requirements, cold storage status, and transit access.
 *
 * Listens for the custom 'toggleCard' event dispatched by table.js.
 *
 * PUBLIC API
 *   cards.init()  — attach the global toggleCard listener (call once)
 */

const cards = (() => {
  "use strict";

  /** Tracks currently expanded cards keyed by option name. */
  const _open = new Map();

  /**
   * _dot(ok) — Small colour-coded dot HTML.
   * @param {boolean} ok — green if true, red if false
   * @returns {string} HTML string
   */
  function _dot(ok) {
    const colour = ok ? "bg-emerald-500" : "bg-red-400";
    return `<span class="inline-block w-2 h-2 rounded-full ${colour}"></span>`;
  }

  /**
   * _boolLine(val, yesKey, noKey) — Translated Yes/No with dot.
   * @param {boolean}  val
   * @param {string}   yesKey — i18n key for the true case
   * @param {string}   noKey  — i18n key for the false case
   * @returns {string} HTML string
   */
  function _boolLine(val, yesKey, noKey) {
    const colour = val ? "text-emerald-700" : "text-red-600";
    const label  = val ? i18n.t(yesKey) : i18n.t(noKey);
    return `<span class="inline-flex items-center gap-1 ${colour}">${_dot(val)} ${label}</span>`;
  }

  /**
   * _icon(svgPath) — Wrap an SVG path in a 4×4 icon.
   * @param {string} svgPath — <path> d attribute
   * @returns {string} HTML string
   */
  function _icon(svgPath) {
    return `<span class="text-blue-500 mt-0.5 flex-shrink-0"><svg class="w-4 h-4" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="${svgPath}"/></svg></span>`;
  }

  /**
   * _buildCard(option) — Create the detail card DOM node.
   * Returns a <tr> containing a single colspan <td> wrapping the card.
   * @param {Object} option — a single option object from the API
   * @returns {HTMLTableRowElement}
   */
  function _buildCard(option) {
    const tr = document.createElement("tr");
    tr.className = "card-row";

    const td = document.createElement("td");
    td.colSpan = 7;
    td.className = "px-0 py-0";

    const card = document.createElement("div");
    card.className =
      "mx-4 my-3 p-5 rounded-xl border border-blue-200 " +
      "bg-gradient-to-br from-blue-50 to-white shadow-md animate-slideDown";

    card.innerHTML = `
      <div class="flex items-start justify-between mb-3">
        <div>
          <h3 class="text-lg font-bold text-gray-900">${option.name}</h3>
          <p class="text-sm text-gray-500">${option.type === "pantry" ? i18n.t("drop_zone_label") : i18n.t("type." + option.type)}</p>
        </div>
        <button class="card-close text-gray-400 hover:text-gray-600 transition-colors text-xl leading-none" aria-label="Close">&times;</button>
      </div>

      <div class="flex flex-wrap gap-2 mb-4">
        ${option.cold_storage ? `<span class="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-semibold bg-blue-100 text-blue-700 border border-blue-200">❄️ ${i18n.t("cold_storage_badge")}</span>` : ""}
        ${option.transit_accessible ? `<span class="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-semibold bg-emerald-100 text-emerald-700 border border-emerald-200">🚌 ${i18n.t("transit_badge")}</span>` : ""}
        ${!option.id_required ? `<span class="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-semibold bg-purple-100 text-purple-700 border border-purple-200">✓ ${i18n.t("no_id_badge")}</span>` : ""}
      </div>

      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 text-sm">
        <!-- Address -->
        <div class="flex items-start gap-2">
          ${_icon("M17.657 16.657L13.414 20.9a2 2 0 01-2.828 0L6.343 16.657a8 8 0 1111.314 0zM15 11a3 3 0 11-6 0 3 3 0 016 0z")}
          <div>
            <p class="font-semibold text-gray-700" data-i18n="card.address">${i18n.t("card.address")}</p>
            <p class="text-gray-600">${option.address || "—"}</p>
          </div>
        </div>

        <!-- Hours -->
        <div class="flex items-start gap-2">
          ${_icon("M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z")}
          <div>
            <p class="font-semibold text-gray-700" data-i18n="card.hours">${i18n.t("card.hours")}</p>
            <p class="text-gray-600">${option.hours || "—"}</p>
          </div>
        </div>

        <!-- Languages -->
        <div class="flex items-start gap-2">
          ${_icon("M3 5h12M9 3v2m1.048 9.5A18.022 18.022 0 016.412 9m6.088 9h7M11 21l5-10 5 10M12.751 5C11.783 10.77 8.07 15.61 3 18.129")}
          <div>
            <p class="font-semibold text-gray-700" data-i18n="card.languages">${i18n.t("card.languages")}</p>
            <div class="flex flex-wrap gap-1 mt-0.5">${(option.languages || []).map((l) => `<span class="inline-block px-2 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-700">${l.toUpperCase()}</span>`).join("")}</div>
          </div>
        </div>

        <!-- ID Required -->
        <div class="flex items-start gap-2">
          ${_icon("M10 6H5a2 2 0 00-2 2v9a2 2 0 002 2h14a2 2 0 002-2V8a2 2 0 00-2-2h-5m-4 0V5a2 2 0 114 0v1m-4 0a2 2 0 104 0")}
          <div>
            <p class="font-semibold text-gray-700" data-i18n="card.id_required">${i18n.t("card.id_required")}</p>
            ${_boolLine(option.id_required, "card.yes", "card.no")}
          </div>
        </div>

        <!-- Cold Storage -->
        <div class="flex items-start gap-2">
          ${_icon("M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4")}
          <div>
            <p class="font-semibold text-gray-700" data-i18n="card.cold_storage">${i18n.t("card.cold_storage")}</p>
            ${_boolLine(option.cold_storage, "card.available", "card.not_available")}
          </div>
        </div>

        <!-- Transit Nearby -->
        <div class="flex items-start gap-2">
          ${_icon("M8 7h8M8 11h8m-4 4v4m-4 0h8M6 3h12a2 2 0 012 2v14l-3 3H7l-3-3V5a2 2 0 012-2z")}
          <div>
            <p class="font-semibold text-gray-700" data-i18n="card.transit_nearby">${i18n.t("card.transit_nearby")}</p>
            ${_boolLine(option.transit_accessible, "card.yes", "card.no")}
          </div>
        </div>
      </div>
    `;

    card.querySelector(".card-close").addEventListener("click", (e) => {
      e.stopPropagation();
      _removeCard(option.name);
    });

    td.appendChild(card);
    tr.appendChild(td);
    return tr;
  }

  /**
   * _removeCard(name) — Collapse a card by option name.
   * @param {string} name
   */
  function _removeCard(name) {
    const row = _open.get(name);
    if (row) {
      row.remove();
      _open.delete(name);
    }
  }

  /**
   * _handleToggle(e) — Listener for the 'toggleCard' custom event.
   * Inserts or removes a detail card row below the clicked table row.
   * @param {CustomEvent} e — { detail: { option, rowEl } }
   */
  function _handleToggle(e) {
    const { option, rowEl } = e.detail;

    if (_open.has(option.name)) {
      _removeCard(option.name);
      return;
    }

    const cardRow = _buildCard(option);
    rowEl.parentNode.insertBefore(cardRow, rowEl.nextSibling);
    _open.set(option.name, cardRow);
  }

  /**
   * init() — Attach the global 'toggleCard' listener.
   * Also re-renders any open cards when the language changes.
   */
  function init() {
    window.addEventListener("toggleCard", _handleToggle);

    window.addEventListener("langchange", () => {
      /* Close all open cards — they'll be re-opened by clicking again */
      _open.forEach((row) => row.remove());
      _open.clear();
    });
  }

  return { init };
})();
