/**
 * i18n.js — Internationalization Module for OptimalEats
 *
 * Provides a complete EN/ES translation dictionary and a toggle
 * mechanism so every translatable UI element switches language with
 * a single click.  Other modules listen for the custom 'langchange'
 * event to re-render dynamic content.
 *
 * PUBLIC API
 *   i18n.t(key, replacements?)  — translated string for the active language
 *   i18n.setLang(lang)          — switch to 'en' or 'es', re-translate DOM
 *   i18n.getLang()              — current language code ('en' | 'es')
 *   i18n.toggleLang()           — flip between EN ↔ ES
 *   i18n.translateElement(el)   — translate one element via its data-i18n attr
 *   i18n.translateAll()         — translate every [data-i18n] in the document
 */

const i18n = (() => {
  "use strict";

  let currentLang = "en";

  /**
   * Master translation dictionary.
   * Keys are dot-separated paths; values hold { en, es } strings.
   */
  const translations = {
    /* ── Navigation / Global ───────────────────────── */
    "nav.title":            { en: "OptimalEats",                          es: "OptimalEats" },
    "nav.tagline":          { en: "Find affordable food near you",        es: "Encuentra comida accesible cerca de ti" },
    "nav.lang_toggle":      { en: "ES",                                   es: "EN" },

    /* ── ZIP Entry ─────────────────────────────────── */
    "zip.heading":          { en: "Enter Your ZIP Code",                  es: "Ingresa Tu Código Postal" },
    "zip.subheading":       { en: "Answer the question: how do I get food as cheaply as possible right now?", es: "Responde la pregunta: ¿cómo consigo comida lo más barato posible ahora mismo?" },
    "zip.placeholder":      { en: "e.g. 64130",                          es: "ej. 64130" },
    "zip.button":           { en: "Find Food Options",                    es: "Buscar Opciones de Comida" },
    "zip.error_invalid":    { en: "Please enter a valid Kansas City ZIP code (641xx).", es: "Por favor ingresa un código postal válido de Kansas City (641xx)." },
    "zip.error_no_results": { en: "No results found for this ZIP code.",  es: "No se encontraron resultados para este código postal." },
    "zip.error_network":    { en: "Could not reach the server. Please try again.", es: "No se pudo conectar al servidor. Inténtalo de nuevo." },

    /* ── NLP Input (Phase 3) ────────────────────────── */
    "input_placeholder":    { en: "Enter ZIP or describe your area (e.g. 'food near 64130')", es: "Ingrese ZIP o describa su área (ej. 'comida cerca de 64130')" },
    "interpreting_label":   { en: "Interpreting your request...",         es: "Interpretando su solicitud..." },
    "nlp_error_label":      { en: "Could not find a KC location. Try a ZIP code.", es: "No se pudo encontrar una ubicación en KC. Intente con un código ZIP." },
    "nlp_interpreted_as":   { en: "Showing results for {location}",       es: "Mostrando resultados para {location}" },
    "spinner.searching":    { en: "Searching...",                         es: "Buscando..." },

    /* ── Need Score Badge ──────────────────────────── */
    "score.label":          { en: "Need Score",                           es: "Puntaje de Necesidad" },
    "score.high_alert":     { en: "High Need Area",                       es: "Zona de Alta Necesidad" },
    "score.high_alert_desc":{ en: "This ZIP code is in a high-need area. More free resources are listed first.", es: "Este código postal está en una zona de alta necesidad. Más recursos gratuitos se muestran primero." },

    /* ── Cost Comparison Table ─────────────────────── */
    "table.heading":        { en: "Food Access Options",                  es: "Opciones de Acceso a Alimentos" },
    "table.click_hint":     { en: "Click any pantry row to see full details.", es: "Haz clic en cualquier fila de despensa para ver los detalles." },
    "table.col_option":     { en: "Option",                               es: "Opción" },
    "table.col_type":       { en: "Type",                                 es: "Tipo" },
    "table.col_cost":       { en: "Est. Cost",                            es: "Costo Est." },
    "table.col_distance":   { en: "Distance",                             es: "Distancia" },
    "table.col_transit":    { en: "Transit?",                             es: "¿Transporte?" },
    "table.col_language":   { en: "Language",                             es: "Idioma" },
    "table.col_notes":      { en: "Notes",                                es: "Notas" },
    "table.miles":          { en: "mi",                                   es: "mi" },
    "table.yes":            { en: "Yes",                                  es: "Sí" },
    "table.no":             { en: "No",                                   es: "No" },
    "table.na":             { en: "—",                                    es: "—" },

    /* ── Cost Tiers ────────────────────────────────── */
    "tier.free":            { en: "Free",                                 es: "Gratis" },
    "tier.low":             { en: "Low Cost",                             es: "Bajo Costo" },
    "tier.market":          { en: "Market Rate",                          es: "Precio de Mercado" },

    /* ── Option Types ──────────────────────────────── */
    "type.pantry":          { en: "Pantry",                               es: "Despensa" },
    "type.delivery":        { en: "Delivery",                             es: "Entrega" },
    "type.store":           { en: "Store",                                es: "Tienda" },

    /* ── Pantry Detail Cards ───────────────────────── */
    "card.hours":           { en: "Hours",                                es: "Horario" },
    "card.address":         { en: "Address",                              es: "Dirección" },
    "card.languages":       { en: "Languages",                            es: "Idiomas" },
    "card.id_required":     { en: "ID Required",                          es: "Se Requiere ID" },
    "card.cold_storage":    { en: "Cold Storage",                         es: "Almacenamiento en Frío" },
    "card.transit_nearby":  { en: "Nearby Transit",                       es: "Transporte Cercano" },
    "card.yes":             { en: "Yes",                                  es: "Sí" },
    "card.no":              { en: "No",                                   es: "No" },
    "card.available":       { en: "Available",                            es: "Disponible" },
    "card.not_available":   { en: "Not Available",                        es: "No Disponible" },

    /* ── Alert Banner ──────────────────────────────── */
    "alert.produce_title":  { en: "Fresh Produce Available!",             es: "¡Productos Frescos Disponibles!" },
    "alert.produce_body":        { en: "{pounds} lbs of {item} available — pick up before {hours} hours", es: "{pounds} lbs de {item} disponibles — recógelos antes de {hours} horas" },
    "alert.produce_body_simple": { en: "{item} available — claim at drop locations",                       es: "{item} disponibles — reclama en los puntos de entrega" },
    "alert.top_locations":  { en: "Recommended Pickup Locations",         es: "Ubicaciones de Recogida Recomendadas" },
    "alert.dismiss":        { en: "Dismiss",                              es: "Cerrar" },
    "alert.score":          { en: "Score",                                es: "Puntaje" },

    /* ── Community Vote Banner (Curveball) ────────── */
    "vote_banner.heading":      { en: "Community Priority Vote — Deadline: April 11", es: "Voto de Prioridad Comunitaria — Fecha Límite: 11 de Abril" },
    "vote_banner.desc":         { en: "City council is selecting 2 priority zones for enhanced food access. Your vote matters!", es: "El concejo municipal está seleccionando 2 zonas prioritarias para mejor acceso a alimentos. ¡Tu voto importa!" },
    "vote_banner.zone_label":   { en: "Priority Zone",                   es: "Zona Prioritaria" },
    "vote_banner.need_score":   { en: "Need Score: {score}",             es: "Puntaje de Necesidad: {score}" },
    "vote_banner.spanish_note": { en: "80%+ Spanish-speaking community", es: "Comunidad 80%+ hispanohablante" },
    "vote_banner.days_left":    { en: "{days} days left to vote",        es: "{days} días para votar" },
    "vote_banner.vote_now":     { en: "Vote Now",                        es: "Votar Ahora" },

    /* ── Community Vote Panel ──────────────────────── */
    "vote.heading":         { en: "Community Priority Vote",              es: "Voto de Prioridad Comunitaria" },
    "vote.desc":            { en: "Help us decide which neighborhoods should receive priority food access support.", es: "Ayúdanos a decidir qué vecindarios deberían recibir apoyo prioritario de acceso a alimentos." },
    "vote.name":            { en: "Your Name",                            es: "Tu Nombre" },
    "vote.zip":             { en: "Your ZIP",                             es: "Tu Código Postal" },
    "vote.support":         { en: "I support priority designation",       es: "Apoyo la designación prioritaria" },
    "vote.submit":          { en: "Submit Vote",                          es: "Enviar Voto" },
    "vote.thanks":          { en: "Thank you for your vote!",             es: "¡Gracias por tu voto!" },

    /* ── Delivery Table ───────────────────────────── */
    "delivery.heading":       { en: "Delivery Options",                                        es: "Opciones de Entrega" },
    "delivery.why_hint":      { en: "Based on your ZIP, fewer than 2 transit-accessible pantries are nearby. Delivery may be your most accessible option.", es: "Según tu código postal, hay menos de 2 despensas accesibles por transporte público cerca. La entrega puede ser tu opción más accesible." },
    "delivery.banner":        { en: "Delivery may be your best option",                        es: "La entrega puede ser tu mejor opción" },
    "delivery.col_provider":  { en: "Provider",                                                es: "Proveedor" },
    "delivery.col_snap_ebt":  { en: "SNAP / EBT",                                              es: "SNAP / EBT" },
    "delivery.col_fee":       { en: "Delivery Fee",                                            es: "Costo de Entrega" },
    "delivery.col_order_min": { en: "Order Min",                                               es: "Pedido Mínimo" },
    "delivery.col_total":     { en: "Est. Total",                                              es: "Total Est." },
    "delivery.col_same_day":  { en: "Same-Day",                                                es: "Mismo Día" },
    "delivery.snap":          { en: "SNAP",                                                    es: "SNAP" },
    "delivery.ebt":           { en: "EBT",                                                     es: "EBT" },
    "delivery.subsidy_discount": { en: "SNAP/EBT discount",                                    es: "Descuento SNAP/EBT" },

    /* ── Choice Architecture (1A) ─────────────────── */
    "free_route_label":     { en: "Free Route",                             es: "Ruta Gratuita" },
    "optimal_route_label":  { en: "Optimal Route",                          es: "Ruta Óptima" },
    "instant_route_label":  { en: "Instant Route",                          es: "Entrega Inmediata" },
    "best_value_badge":     { en: "Best Value",                             es: "Mejor Precio" },
    "no_delivery_zip":      { en: "Delivery not available in your area",    es: "Entrega no disponible en su área" },

    /* ── Drop Zone Reframing (1B) ────────────────── */
    "drop_zone_label":      { en: "Drop Zone",                              es: "Zona de Entrega" },
    "cold_storage_badge":   { en: "Cold Storage",                           es: "Almacenamiento Frío" },
    "transit_badge":        { en: "Transit Access",                         es: "Acceso en Tránsito" },
    "no_id_badge":          { en: "No ID Required",                         es: "Sin Identificación" },

    /* ── Active Drop Mission (1C) ────────────────── */
    "active_mission_label": { en: "Active Drop Mission",                    es: "Misión de Entrega Activa" },
    "routing_to_label":     { en: "Routing to",                             es: "Enviando a" },
    "urgent_label":         { en: "URGENT",                                 es: "URGENTE" },
    "today_label":          { en: "TODAY",                                  es: "HOY" },
    "active_label":         { en: "ACTIVE",                                 es: "ACTIVO" },
    "same_day_delivery":    { en: "Same-day delivery",                      es: "Entrega el mismo día" },
    "batched.provider":     { en: "OptimalEats Batched",                    es: "OptimalEats Agrupado" },
    "batched.per_delivery": { en: "/delivery",                              es: "/entrega" },
    "batched.eta":          { en: "~{hrs} hrs · Shared courier",            es: "~{hrs} hrs · Mensajero compartido" },
    "batched.note":         { en: "Algorithmically grouped with neighbors", es: "Agrupado algorítmicamente con vecinos" },
    "batched.recommended":  { en: "Recommended",                            es: "Recomendado" },
    "no_free_options":      { en: "No free options found for this ZIP.",     es: "No hay opciones gratuitas para este código postal." },
    "more_free_options":    { en: "+{count} more free option below",        es: "+{count} opción gratuita más abajo" },
    "more_free_options_pl": { en: "+{count} more free options below",       es: "+{count} opciones gratuitas más abajo" },
    "see_details_below":    { en: "See details in table below ↓",           es: "Ver detalles en la tabla abajo ↓" },

    /* ── Cuisine Preferences ──────────────────────── */
    "cuisine.heading":          { en: "Cuisine Preferences (optional)",       es: "Preferencias de Cocina (opcional)" },
    "cuisine.american":         { en: "American",                             es: "Americana" },
    "cuisine.hispanic":         { en: "Hispanic",                             es: "Hispana" },
    "cuisine.asian":            { en: "Asian",                                es: "Asiática" },
    "cuisine.african_caribbean":{ en: "African/Caribbean",                    es: "Africana/Caribeña" },
    "cuisine.soul_food":        { en: "Soul Food",                            es: "Soul Food" },
    "table.col_cuisine":        { en: "Cuisine",                              es: "Cocina" },

    /* ── Footer ────────────────────────────────────── */
    "footer.text":          { en: "OptimalEats — Connecting Kansas City to affordable food.", es: "OptimalEats — Conectando a Kansas City con comida accesible." },
    "footer.disclaimer":    { en: "Data sourced from public APIs. Availability may vary.",    es: "Datos obtenidos de APIs públicas. La disponibilidad puede variar." },
  };

  /**
   * t(key, replacements?) — Return the translated string for `key`.
   * Optional `replacements` object interpolates {token} placeholders.
   * @param {string} key           — dot-separated translation key
   * @param {Object} replacements  — optional { token: value } map
   * @returns {string}
   */
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

  /**
   * translateElement(el) — Apply translation to one DOM element that
   * carries a data-i18n="some.key" attribute.  Sets placeholder for
   * inputs, textContent otherwise.
   * @param {HTMLElement} el
   */
  function translateElement(el) {
    const key = el.getAttribute("data-i18n");
    if (!key) return;
    if (el.tagName === "INPUT" || el.tagName === "TEXTAREA") {
      el.placeholder = t(key);
    } else {
      el.textContent = t(key);
    }
  }

  /**
   * translateAll() — Walk the entire DOM and translate every element
   * with a data-i18n attribute.
   */
  function translateAll() {
    document.querySelectorAll("[data-i18n]").forEach(translateElement);
  }

  /**
   * setLang(lang) — Switch to a language ('en' | 'es'), re-translate
   * the DOM, and fire a 'langchange' CustomEvent on window so other
   * modules can re-render dynamic content.
   * @param {'en'|'es'} lang
   */
  function setLang(lang) {
    if (lang !== "en" && lang !== "es") return;
    currentLang = lang;
    document.documentElement.lang = lang;
    translateAll();
    window.dispatchEvent(new CustomEvent("langchange", { detail: { lang } }));
  }

  /**
   * getLang() — Returns the active language code.
   * @returns {'en'|'es'}
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
