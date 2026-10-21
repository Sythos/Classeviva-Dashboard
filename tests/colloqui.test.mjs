// SPDX-License-Identifier: MIT
// Copyright (c) 2026 Sythos <sythos@gmail.com>
// Author: Sythos <sythos@gmail.com>
//
// Tests of the Colloqui view of the card. They use made-up data only.

import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import test from "node:test";
import vm from "node:vm";
import { fileURLToPath } from "node:url";

const FILE = path.join(
  path.dirname(fileURLToPath(import.meta.url)),
  "..", "custom_components", "cvv_dashboard", "www", "cvv-dashboard-card.js"
);
const CODICE = fs.readFileSync(FILE, "utf8");

function nuovaScheda(items, stato = "ok") {
  const definiti = new Map();
  class Elemento {
    attachShadow() {
      this.shadowRoot = { innerHTML: "", querySelector: () => null, querySelectorAll: () => [] };
      return this.shadowRoot;
    }
    addEventListener() {}
    setAttribute() {}
    getAttribute() {}
  }
  const contesto = {
    HTMLElement: Elemento,
    customElements: { get: (n) => definiti.get(n), define: (n, c) => definiti.set(n, c) },
    window: { customCards: [] },
    localStorage: { getItem: () => null, setItem() {}, removeItem() {} },
    document: { createElement: () => new Elemento() },
    console: { info() {}, error() {}, warn() {}, log() {} },
  };
  vm.createContext(contesto);
  vm.runInContext(`(function () {\n${CODICE}\n})();`, contesto, { filename: FILE });
  const card = new (definiti.get("cvv-dashboard-card"))();
  card.setConfig({ vista: "colloqui" });
  const ent = { colloqui: { state: "1", attributes: { items, stato_dati: stato } } };
  return { card, ent };
}

function giorno(spostamento) {
  const d = new Date();
  d.setDate(d.getDate() + spostamento);
  return [d.getFullYear(), String(d.getMonth() + 1).padStart(2, "0"), String(d.getDate()).padStart(2, "0")].join("-");
}

test("the talks view shows both statuses in date order and hides a day outside the range", () => {
  const { card, ent } = nuovaScheda([
    { data: giorno(3), ora_inizio: "10:00", docente: "Docente B", stato: "prenotato", aula: "Aula 5" },
    { data: giorno(1), ora_inizio: "09:00", docente: "Docente A", stato: "disponibile" },
    { data: giorno(28), ora_inizio: "09:00", docente: "Docente Fuori", stato: "disponibile" },
  ]);
  const html = card._vistaColloqui(ent);
  assert.ok(html.indexOf("Docente A") < html.indexOf("Docente B"));
  assert.doesNotMatch(html, /Docente Fuori/);
  assert.match(html, /Disponibile/);
  assert.match(html, /Prenotato/);
  assert.equal((html.match(/<button/g) || []).length, 1);
});

test("the talks view includes today and day 27 and hides day 28", () => {
  const { card, ent } = nuovaScheda([
    { data: giorno(0), docente: "Oggi", stato: "disponibile" },
    { data: giorno(27), docente: "Ultimo", stato: "disponibile" },
    { data: giorno(28), docente: "Troppo", stato: "disponibile" },
  ]);
  const html = card._vistaColloqui(ent);
  assert.match(html, /Oggi/);
  assert.match(html, /Ultimo/);
  assert.doesNotMatch(html, /Troppo/);
});

test("the talks view shows only safe links and escapes the text", () => {
  const base = { data: giorno(1), ora_inizio: "09:00", stato: "prenotato" };
  const cattivo = nuovaScheda([
    { ...base, docente: "<img src=x onerror=1>", link: "javascript:alert(1)", aula: "<b>A</b>" },
  ]);
  const html = cattivo.card._vistaColloqui(cattivo.ent);
  assert.doesNotMatch(html, /<img/);
  assert.doesNotMatch(html, /<b>A<\/b>/);
  assert.doesNotMatch(html, /javascript:/);
  assert.doesNotMatch(html, /<a /);
  const buono = nuovaScheda([{ ...base, docente: "D", link: "https://example.org/m" }]);
  assert.match(
    buono.card._vistaColloqui(buono.ent),
    /href="https:\/\/example.org\/m"[^>]*rel="noopener noreferrer"/
  );
});

test("the talks view shows the empty, error and not available states", () => {
  const vuota = nuovaScheda([]);
  assert.match(vuota.card._vistaColloqui(vuota.ent), /Nessun colloquio disponibile nei prossimi 28 giorni/);
  const errore = nuovaScheda([], "errore");
  assert.match(errore.card._vistaColloqui(errore.ent), /Colloqui non disponibili/);
  const assente = nuovaScheda([], "non_disponibile");
  assert.match(assente.card._vistaColloqui(assente.ent), /Funzione non disponibile per questo account/);
});

test("a click on a booked slot opens and closes the details without a redraw", () => {
  const { card, ent } = nuovaScheda([
    { data: giorno(1), ora_inizio: "09:00", docente: "D", stato: "prenotato", aula: "Aula 1" },
  ]);
  let gestore = null;
  const dettagli = { hidden: true };
  const bottone = {
    dataset: { colloquio: "k" },
    attributi: {},
    setAttribute(n, v) { this.attributi[n] = v; },
    parentElement: { querySelector: () => dettagli },
    addEventListener(_tipo, f) { gestore = f; },
  };
  card.shadowRoot.querySelectorAll = (sel) => (sel === "[data-colloquio]" ? [bottone] : []);
  card._disegna(ent);
  const prima = card.shadowRoot.innerHTML;
  assert.ok(gestore);
  gestore();
  assert.equal(bottone.attributi["aria-expanded"], "true");
  assert.equal(dettagli.hidden, false);
  gestore();
  assert.equal(bottone.attributi["aria-expanded"], "false");
  assert.equal(dettagli.hidden, true);
  assert.equal(card.shadowRoot.innerHTML, prima);
});
