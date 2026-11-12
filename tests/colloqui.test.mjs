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
    URL,
  };
  vm.createContext(contesto);
  vm.runInContext(`(function () {\n${CODICE}\n})();`, contesto, { filename: FILE });
  const card = new (definiti.get("cvv-dashboard-card"))();
  card.setConfig({ vista: "colloqui" });
  const ent = { colloqui: { state: "1", attributes: { items, stato_dati: stato, dal: giorno(0), al: giorno(27) } } };
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
  assert.match(html, /Docente A/);
  assert.match(html, /Disponibile/);
  assert.match(html, /Prenotato/);
  assert.match(html, /Docente B/);
  assert.match(html, /Aula 5/);
  assert.doesNotMatch(html, /Docente Fuori/);
  assert.ok(html.indexOf("Disponibile") < html.indexOf("Prenotato"));
  // the free slot opens the official page; the booked row opens its details
  assert.equal((html.match(/<button/g) || []).length, 2);
  assert.equal((html.match(/data-colloquio=/g) || []).length, 1);
  assert.equal((html.match(/data-apri-colloquio=/g) || []).length, 1);
});

test("the talks view shows the subject and an official link for a free slot", () => {
  const { card, ent } = nuovaScheda([
    { data: giorno(1), ora_inizio: "09:00", docente: "Docente A", materia: "Materia X", stato: "disponibile",
      link: "https://evil.example.org/x" },
  ]);
  const html = card._vistaColloqui(ent);
  assert.match(html, /Docente A – Materia X/);
  assert.match(html, /data-apri-colloquio="https:\/\/web\.spaggiari\.eu\/"/);
  assert.equal(card._linkColloqui("http://web.spaggiari.eu/a"), "https://web.spaggiari.eu/");
  assert.equal(card._linkColloqui("https://web.spaggiari.eu/p?x=1"), "https://web.spaggiari.eu/p?x=1");
});

test("the talks view shows a data error state", () => {
  const { card, ent } = nuovaScheda([], "errore_dati");
  assert.match(card._vistaColloqui(ent), /Errore dati/);
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
  // a booked link is never written in the HTML; the card asks the server for it
  const buono = nuovaScheda([{ ...base, id: "7", docente: "D", ha_link: true, link: "https://example.org/m" }]);
  const htmlBuono = buono.card._vistaColloqui(buono.ent);
  assert.doesNotMatch(htmlBuono, /href=/);
  assert.doesNotMatch(htmlBuono, /example\.org/);
  assert.match(htmlBuono, /data-talk="7"/);
  assert.equal(buono.card._linkRiunione("https://example.org/m"), "https://example.org/m");
  assert.equal(buono.card._linkRiunione("http://example.org/m"), "http://example.org/m");
  assert.equal(buono.card._linkRiunione("javascript:alert(1)"), "");
  assert.equal(buono.card._linkRiunione("ftp://example.org/m"), "");
  assert.equal(buono.card._linkRiunione("https://exa mple.org"), "");
  assert.equal(buono.card._linkRiunione(""), "");
  const libero = nuovaScheda([
    { data: giorno(1), ora_inizio: "09:00", stato: "disponibile", docente: "<img src=x onerror=1>" },
  ]);
  const htmlLibero = libero.card._vistaColloqui(libero.ent);
  assert.doesNotMatch(htmlLibero, /<img/);
  assert.match(htmlLibero, /&lt;img/);
});

test("the talks view shows the empty, error and not available states", () => {
  const vuota = nuovaScheda([]);
  assert.match(vuota.card._vistaColloqui(vuota.ent), /Nessun colloquio disponibile nei prossimi 28 giorni/);
  const errore = nuovaScheda([], "errore");
  assert.match(errore.card._vistaColloqui(errore.ent), /Colloqui non disponibili/);
  const assente = nuovaScheda([], "non_disponibile");
  assert.match(assente.card._vistaColloqui(assente.ent), /Funzione non disponibile per questo account/);
});

test("a booked talk shows its status and, in the details, the safe fields", () => {
  const { card, ent } = nuovaScheda([
    { id: "5", data: giorno(1), ora_inizio: "09:00", ora_fine: "09:10", docente: "Docente Z",
      materia: "Materia X, Materia Y", stato: "prenotato", aula: "Aula 1", modalita: "distanza",
      ha_link: false, dati: "" },
  ]);
  const html = card._vistaColloqui(ent);
  assert.match(html, /Prenotato/);
  assert.match(html, /data-colloquio="5"/);
  assert.match(html, /Docente Z/);
  assert.match(html, /Materia X, Materia Y/);
  assert.match(html, /09:00–09:10/);
  assert.match(html, /Aula 1/);
  assert.match(html, /a distanza/);
  assert.doesNotMatch(html, /link-riunione/);
  assert.match(html, /<div class="dettagli" hidden>/);
});

test("the card shows the mode of each booked row and no default for an unknown mode", () => {
  const base = { data: giorno(1), ora_inizio: "09:00", docente: "Docente Z", stato: "prenotato", dati: "" };
  const { card, ent } = nuovaScheda([
    { ...base, id: "1", modalita: "presenza" },
    { ...base, id: "2", modalita: "distanza" },
    { ...base, id: "3", modalita: "" },
  ]);
  const html = card._vistaColloqui(ent);
  assert.equal((html.match(/in presenza/g) || []).length, 1);
  assert.equal((html.match(/a distanza/g) || []).length, 1);
  assert.equal((html.match(/Modalità/g) || []).length, 2);
});

test("a partial booked talk shows a clear status and does not hide the other rows", () => {
  const { card, ent } = nuovaScheda([
    { id: "", data: "", ora_inizio: "", stato: "prenotato", dati: "parziali" },
    { id: "6", data: giorno(2), ora_inizio: "10:00", docente: "Docente V", stato: "prenotato", dati: "" },
  ]);
  const html = card._vistaColloqui(ent);
  assert.match(html, /Prenotato \(dati parziali\)/);
  assert.match(html, /Docente V/);
  assert.ok(html.indexOf("Docente V") < html.indexOf("dati parziali"));
});

test("the card asks for the meeting link only when the row opens and sends no write command", async () => {
  const { card, ent } = nuovaScheda([]);
  const chiamate = [];
  card._hass = {
    callWS: (msg) => {
      chiamate.push(msg);
      return Promise.resolve({ link: "https://example.org/m" });
    },
  };
  card._entitaCard = "sensor.voti_test";
  const figli = [];
  const box = { dataset: { talk: "9" }, appendChild: (a) => figli.push(a) };
  card._caricaLinkColloquio(box, ent);
  card._caricaLinkColloquio(box, ent);
  await new Promise((r) => setImmediate(r));
  assert.equal(chiamate.length, 1);
  assert.deepEqual(
    { ...chiamate[0] },
    { type: "cvv_dashboard/talk_link", entity_id: "sensor.voti_test", talk_id: "9" }
  );
  assert.equal(figli.length, 1);
  assert.equal(figli[0].href, "https://example.org/m");
  assert.equal(figli[0].rel, "noopener noreferrer");
  assert.doesNotMatch(CODICE, /cvv_dashboard\/(book|cancel|delete|edit|message)/);
});

test("the link request carries the displayed year only when it is not the configured one", async () => {
  const { card, ent } = nuovaScheda([]);
  const chiamate = [];
  card._hass = { callWS: (msg) => { chiamate.push(msg); return Promise.resolve({ link: "" }); } };
  card._entitaCard = "sensor.voti_test";
  card._annoLink = 2026;
  card._caricaLinkColloquio({ dataset: { talk: "1" }, appendChild() {} }, ent);
  card._annoLink = null;
  card._caricaLinkColloquio({ dataset: { talk: "2" }, appendChild() {} }, ent);
  await new Promise((r) => setImmediate(r));
  assert.equal(chiamate[0].anno, 2026);
  assert.equal("anno" in chiamate[1], false);
});

test("a redraw asks again for the link of the rows that are already open", () => {
  const { card, ent } = nuovaScheda([]);
  let selettore = "";
  card.shadowRoot = {
    querySelectorAll: (s) => { selettore = s; return [{ dataset: { talk: "3" } }]; },
  };
  const chiamati = [];
  card._caricaLinkColloquio = (box) => chiamati.push(box.dataset.talk);
  card._caricaLinkAperti(ent);
  assert.match(selettore, /\.dettagli:not\(\[hidden\]\) \.link-riunione/);
  assert.deepEqual(chiamati, ["3"]);
});

test("a booked talk without a date stays visible after the free slots", () => {
  const { card, ent } = nuovaScheda([
    { stato: "prenotato", data: "", ora_inizio: "" },
    { data: giorno(1), ora_inizio: "09:00", docente: "Docente A", stato: "disponibile" },
  ]);
  const html = card._vistaColloqui(ent);
  assert.match(html, /Prenotato/);
  assert.ok(html.indexOf("Docente A") < html.indexOf("Prenotato"));
  assert.doesNotMatch(html, /Nessun colloquio disponibile/);
});
