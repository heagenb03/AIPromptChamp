/**
 * cards.js — Pantry Detail Card Component for FoodFlow KC
 *
 * Renders expandable detail cards below table rows when the user
 * clicks a pantry option.  Each card shows hours, address, language
 * support, ID requirements, cold storage status, and nearby transit.
 *
 * Listens for the custom 'toggleCard' event dispatched by table.js.
 *
 * PUBLIC API
 *   cards.init()  — attach the global toggleCard listener (call once at startup)
 */

const cards = (() => {
  "use strict";

  /** Tracks which card elements are currently expanded, keyed by option name. */
  const _openCards = new Map();

  /* ─────────────────────────────────────────────────────────
   * _boolLabel(val, yesKey, noKey)
   * Returns a translated "Yes"/"No"/"Available"/"Not Available"
   * string with a colour-coded dot.
   *   val    — boolean
   *   yesKey — i18n key for the true case
   *   noKey  — i18n key for the false case
   * Returns an HTML string.
   * ───────────────────────────────────────────────────────── */
  function _boolLabel(val, yesKey, noKey) {
    if (val) {
      return `<span class="inline-flex items-center gap-1 text-emerald-700"><span class="w-2 h-2 rounded-full bg-emerald-500"></span>${i18n.t(yesKey)}</span>`;
    }
    return `<span class="inline-flex items-center gap-1 text-red-600"><span class="w-2 h-2 rounded-full bg-red-400"></span>${i18n.t(noKey)}</span>`;
  }

  /* ─────────────────────────────────────────────────────────
   * _buildCard(option)
   * Creates the full detail card DOM node for one pantry option.
   *   option — a single option object from the API
   * Returns an HTMLElement (a <tr> containing a colspan <td>).
   * ───────────────────────────────────────────────────────── */
  function _buildCard(option) {
    const tr = document.createElement("tr");
    tr.className = "card-row";

    const td = document.createElement("td");
    td.colSpan = 7;
    td.className = "px-0 py-0";

    const card = document.createElement("div");
    card.className =
      "mx-4 my-3 p-5 rounded-xl border border-blue-200 bg-gradient-to-br from-blue-50 to-white shadow-md " +
      "animate-slideDown";

    card.innerHTML = `
      <div class="flex items-start justify-between mb-4">
        <div>
          <h3 class="text-lg font-bold text-gray-900">${option.name}</h3>
          <p class="text-sm text-gray-500">${i18n.t("type." + option.type)}</p>
        </div>
        <button class="card-close text-gray-400 hover:text-gray-600 transition-colors text-xl leading-none" aria-label="Close">&times;</button>
      </div>

      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 text-sm">
        <!-- Address -->
        <div class="flex items-start gap-2">
          <span class="text-blue-500 mt-0.5">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M17.657 16.657L13.414 20.9a2 2 0 01-2.828 0L6.343 16.657a8 8 0 1111.314 0z"/><path stroke-linecap="round" stroke-linejoin="round" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z"/></svg>
          </span>
          <div>
            <p class="font-semibold text-gray-700" data-i18n="card.address">${i18n.t("card.address")}</p>
            <p class="text-gray-600">${option.address || "—"}</p>
          </div>
        </div>

        <!-- Hours -->
        <div class="flex items-start gap-2">
          <span class="text-blue-500 mt-0.5">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"/><path stroke-linecap="round" d="M12 6v6l4 2"/></svg>
          </span>
          <div>
            <p class="font-semibold text-gray-700" data-i18n="card.hours">${i18n.t("card.hours")}</p>
            <p class="text-gray-600">${option.hours || "—"}</p>
          </div>
        </div>

        <!-- Languages -->
        <div class="flex items-start gap-2">
          <span class="text-blue-500 mt-0.5">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M3 5h12M9 3v2m1.048 9.5A18.022 18.022 0 016.412 9m6.088 9h7M11 21l5-10 5 10M12.751 5C11.783 10.77 8.07 15.61 3 18.129"/></svg>
          </span>
          <div>
            <p class="font-semibold text-gray-700" data-i18n="card.languages">${i18n.t("card.languages")}</p>
            <p class="text-gray-600">${(option.languages || []).map((l) => l.toUpperCase()).join(", ")}</p>
          </div>
        </div>

        <!-- ID Required -->
        <div class="flex items-start gap-2">
          <span class="text-blue-500 mt-0.5">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><rect x="3" y="4" width="18" height="16" rx="2"/><path d="M7 8h4M7 12h2"/><circle cx="15" cy="10" r="2"/><path d="M13 14h4"/></svg>
          </span>
          <div>
            <p class="font-semibold text-gray-700" data-i18n="card.id_required">${i18n.t("card.id_required")}</p>
            ${_boolLabel(!option.id_required, "card.no", "card.yes")}
          </div>
        </div>

        <!-- Cold Storage -->
        <div class="flex items-start gap-2">
          <span class="text-blue-500 mt-0.5">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M12 3v18m-6-6l6 6 6-6M6 9l6-6 6 6"/></svg>
          </span>
          <div>
            <p class="font-semibold text-gray-700" data-i18n="card.cold_storage">${i18n.t("card.cold_storage")}</p>
            ${_boolLabel(option.cold_storage, "card.available", "card.not_available")}
          </div>
        </div>

        <!-- Transit Nearby -->
        <div class="flex items-start gap-2">
          <span class="text-blue-500 mt-0.5">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M8 7h8M8 11h8m-4 4v4m-4 0h8M6 3h12a2 2 0 012 2v14l-3 3H7l-3-3V5a2 2 0 012-2z"/></svg>
          </span>
          <div>
            <p class="font-semibold text-gray-700" data-i18n="card.transit_nearby">${i18n.t("card.transit_nearby")}</p>
            ${_boolLabel(option.transit_accessible, "card.yes", "card.no")}
          </div>
        </div>
      </div>
    `;

    /* Close button behaviour */
    card.querySelector(".card-close").addEventListener("click", (e) => {
      e.stopPropagation();
      _removeCard(option.name);
    });

    td.appendChild(card);
    tr.appendChild(td);
    return tr;
  }

  /* ─────────────────────────────────────────────────────────
   * _removeCard(name)
   * Removes an expanded card by option name and updates the
   * internal tracking map.
   *   name — option.name key
   * ───────────────────────────────────────────────────────── */
  function _removeCard(name) {
    const cardRow = _openCards.get(name);
    if (cardRow) {
      cardRow.remove();
      _openCards.delete(name);
    }
  }

  /* ─────────────────────────────────────────────────────────
   * _handleToggle(e)
   * Custom event handler for 'toggleCard'.  Inserts or removes
   * a detail card row directly below the clicked table row.
   *   e.detail.option — the option object
   *   e.detail.rowEl  — the <tr> element that was clicked
   * ───────────────────────────────────────────────────────── */
  function _handleToggle(e) {
    const { option, rowEl } = e.detail;

    if (_openCards.has(option.name)) {
      _removeCard(option.name);
      return;
    }

    const cardRow = _buildCard(option);
    rowEl.parentNode.insertBefore(cardRow, rowEl.nextSibling);
    _openCards.set(option.name, cardRow);
  }

  /* ─────────────────────────────────────────────────────────
   * init()
   * Attaches the global 'toggleCard' listener.  Call once when
   * the app boots.
   * ───────────────────────────────────────────────────────── */
  function init() {
    window.addEventListener("toggleCard", _handleToggle);

    /* Re-render open cards when the language changes */
    window.addEventListener("langchange", () => {
      _openCards.forEach((cardRow, name) => {
        /* Store reference to next sibling so we can re-insert */
        const nextSibling = cardRow.nextSibling;
        const parent = cardRow.parentNode;
        if (!parent) return;

        /* Find the original option data on the preceding <tr> */
        const prevRow = cardRow.previousElementSibling;
        if (!prevRow) return;

        const idx = prevRow.getAttribute("data-option-index");
        if (idx === null) return;

        /* Dispatch a fresh toggle to close + reopen with new lang */
        _removeCard(name);
        prevRow.click();
      });
    });
  }

  return { init };
})();
