/**
 * i18n.js — Internationalization module for FoodFlow KC
 *
 * Provides a complete EN/ES translation map and a toggle mechanism
 * so every translatable UI element can switch language with one click.
 *
 * PUBLIC API
 *   i18n.t(key)            — returns the translated string for the current language
 *   i18n.setLang(lang)     — switches to 'en' or 'es' and re-renders all [data-i18n] elements
 *   i18n.getLang()          — returns current language code ('en' | 'es')
 *   i18n.toggleLang()      — flips between EN and ES
 *   i18n.translateElement(el) — translates a single DOM element via its data-i18n attribute
 */

const i18n = (() => {
  "use strict";

  let currentLang = "en";

  /**
   * Translation dictionary keyed by dotted path.
   * Every user-facing string lives here so nothing is hard-coded in HTML.
   */
  const translations = {
    /* ── Navigation / Global ───────────────────────────── */
    "nav.title":            { en: "FoodFlow KC",               es: "FoodFlow KC" },
    "nav.tagline":          { en: "Find affordable food near you", es: "Encuentra comida accesible cerca de ti" },
    "nav.lang_toggle":      { en: "ES",                        es: "EN" },

    /* ── ZIP Entry ─────────────────────────────────────── */
    "zip.heading":          { en: "Enter Your ZIP Code",       es: "Ingresa Tu Código Postal" },
    "zip.placeholder":      { en: "e.g. 64130",                es: "ej. 64130" },
    "zip.button":           { en: "Find Food Options",         es: "Buscar Opciones de Comida" },
    "zip.error_invalid":    { en: "Please enter a valid 5-digit ZIP code.", es: "Por favor ingresa un código postal válido de 5 dígitos." },
    "zip.error_no_results": { en: "No results found for this ZIP code.",    es: "No se encontraron resultados para este código postal." },

    /* ── Need Score Badge ──────────────────────────────── */
    "score.label":          { en: "Need Score",                es: "Puntaje de Necesidad" },
    "score.high_alert":     { en: "High Need Area",            es: "Zona de Alta Necesidad" },
    "score.high_alert_desc":{ en: "This ZIP code is in a high-need area. More free resources are available below.", es: "Este código postal está en una zona de alta necesidad. Más recursos gratuitos están disponibles abajo." },

    /* ── Cost Comparison Table ─────────────────────────── */
    "table.heading":        { en: "Food Access Options",       es: "Opciones de Acceso a Alimentos" },
    "table.col_option":     { en: "Option",                    es: "Opción" },
    "table.col_type":       { en: "Type",                      es: "Tipo" },
    "table.col_cost":       { en: "Est. Cost",                 es: "Costo Est." },
    "table.col_distance":   { en: "Distance",                  es: "Distancia" },
    "table.col_transit":    { en: "Transit?",                   es: "¿Transporte?" },
    "table.col_language":   { en: "Language",                   es: "Idioma" },
    "table.col_notes":      { en: "Notes",                      es: "Notas" },
    "table.miles":          { en: "mi",                         es: "mi" },
    "table.yes":            { en: "Yes",                        es: "Sí" },
    "table.no":             { en: "No",                         es: "No" },
    "table.na":             { en: "—",                          es: "—" },

    /* ── Cost Tiers ────────────────────────────────────── */
    "tier.free":            { en: "Free",                       es: "Gratis" },
    "tier.low":             { en: "Low Cost",                   es: "Bajo Costo" },
    "tier.market":          { en: "Market Rate",                es: "Precio de Mercado" },

    /* ── Option Types ──────────────────────────────────── */
    "type.pantry":          { en: "Pantry",                     es: "Despensa" },
    "type.delivery":        { en: "Delivery",                   es: "Entrega" },
    "type.store":           { en: "Store",                      es: "Tienda" },

    /* ── Pantry Detail Cards ───────────────────────────── */
    "card.hours":           { en: "Hours",                      es: "Horario" },
    "card.address":         { en: "Address",                    es: "Dirección" },
    "card.languages":       { en: "Languages",                  es: "Idiomas" },
    "card.id_required":     { en: "ID Required",                es: "Se Requiere ID" },
    "card.cold_storage":    { en: "Cold Storage",               es: "Almacenamiento en Frío" },
    "card.transit_nearby":  { en: "Nearby Transit",             es: "Transporte Cercano" },
    "card.yes":             { en: "Yes",                        es: "Sí" },
    "card.no":              { en: "No",                         es: "No" },
    "card.available":       { en: "Available",                  es: "Disponible" },
    "card.not_available":   { en: "Not Available",              es: "No Disponible" },
    "card.view_details":    { en: "View Details",               es: "Ver Detalles" },
    "card.hide_details":    { en: "Hide Details",               es: "Ocultar Detalles" },
    "card.open_today":      { en: "Open today",                 es: "Abierto hoy" },

    /* ── Alert Banner ──────────────────────────────────── */
    "alert.produce_title":  { en: "Fresh Produce Available!",   es: "¡Productos Frescos Disponibles!" },
    "alert.produce_body":   { en: "{pounds} lbs of fresh produce available — pick up before {hours} hours", es: "{pounds} lbs de productos frescos disponibles — recógelos antes de {hours} horas" },
    "alert.top_locations":  { en: "Recommended Pickup Locations", es: "Ubicaciones de Recogida Recomendadas" },
    "alert.dismiss":        { en: "Dismiss",                    es: "Cerrar" },

    /* ── Community Vote Panel ──────────────────────────── */
    "vote.heading":         { en: "Community Priority Vote",    es: "Voto de Prioridad Comunitaria" },
    "vote.desc":            { en: "Help us decide which neighborhoods should receive priority food access support.", es: "Ayúdanos a decidir qué vecindarios deberían recibir apoyo prioritario de acceso a alimentos." },
    "vote.name":            { en: "Your Name",                  es: "Tu Nombre" },
    "vote.zip":             { en: "Your ZIP",                   es: "Tu Código Postal" },
    "vote.support":         { en: "I support priority designation", es: "Apoyo la designación prioritaria" },
    "vote.submit":          { en: "Submit Vote",                es: "Enviar Voto" },
    "vote.thanks":          { en: "Thank you for your vote!",   es: "¡Gracias por tu voto!" },

    /* ── Footer ────────────────────────────────────────── */
    "footer.text":          { en: "FoodFlow KC — Connecting Kansas City to affordable food.", es: "FoodFlow KC — Conectando a Kansas City con comida accesible." },
    "footer.disclaimer":    { en: "Data sourced from public APIs. Availability may vary.", es: "Datos obtenidos de APIs públicas. La disponibilidad puede variar." },
  };

  /* ─────────────────────────────────────────────────────────
   * t(key, replacements?) — Translate a key for the current lang.
   * Optional `replacements` object interpolates {token} placeholders.
   *   e.g. i18n.t("alert.produce_body", { pounds: 1000, hours: 48 })
   * ───────────────────────────────────────────────────────── */
  function t(key, replacements) {
    const entry = translations[key];
    if (!entry) return key;

    let text = entry[currentLang] || entry.en || key;

    if (replacements) {
      Object.keys(replacements).forEach((token) => {
        text = text.replace(new RegExp(`\\{${token}\\}`, "g"), replacements[token]);
      });
    }
    return text;
  }

  /* ─────────────────────────────────────────────────────────
   * translateElement(el) — Apply translation to a single element
   * that carries a data-i18n="some.key" attribute.
   * If the element is an <input>, sets the placeholder; otherwise
   * sets textContent.
   * ───────────────────────────────────────────────────────── */
  function translateElement(el) {
    const key = el.getAttribute("data-i18n");
    if (!key) return;
    if (el.tagName === "INPUT" || el.tagName === "TEXTAREA") {
      el.placeholder = t(key);
    } else {
      el.textContent = t(key);
    }
  }

  /* ─────────────────────────────────────────────────────────
   * translateAll() — Walk the DOM and translate every element
   * with a data-i18n attribute.
   * ───────────────────────────────────────────────────────── */
  function translateAll() {
    document.querySelectorAll("[data-i18n]").forEach(translateElement);
  }

  /* ─────────────────────────────────────────────────────────
   * setLang(lang) — Switch to a language ('en' | 'es').
   * Fires a custom 'langchange' event so other modules can
   * re-render dynamic content.
   * ───────────────────────────────────────────────────────── */
  function setLang(lang) {
    if (lang !== "en" && lang !== "es") return;
    currentLang = lang;
    document.documentElement.lang = lang;
    translateAll();
    window.dispatchEvent(new CustomEvent("langchange", { detail: { lang } }));
  }

  /**
   * getLang() — Returns the active language code.
   * @returns {'en' | 'es'}
   */
  function getLang() {
    return currentLang;
  }

  /**
   * toggleLang() — Flip between EN and ES.
   */
  function toggleLang() {
    setLang(currentLang === "en" ? "es" : "en");
  }

  return { t, setLang, getLang, toggleLang, translateElement, translateAll };
})();
