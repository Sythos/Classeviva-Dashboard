// SPDX-License-Identifier: MIT
// Copyright (c) 2026 Sythos <sythos@gmail.com>
// Author: Sythos <sythos@gmail.com>
//
// Tests of the card file with a small stub of the browser. Run: node --test tests/
// They do not replace a check in a real browser with Home Assistant.

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

/** Contesto con un browser minimo. Ogni chiamata dà un contesto nuovo (cache fredda). */
function nuovoContesto() {
  const definiti = new Map();
  class Elemento {
    attachShadow() {
      this.shadowRoot = { innerHTML: "", querySelector: () => null, querySelectorAll: () => [] };
      return this.shadowRoot;
    }
    addEventListener(tipo, funzione) { (this.ascoltatori ||= {})[tipo] = funzione; }
    setAttribute(n, v) { (this.attributi ||= {})[n] = String(v); }
    getAttribute(n) { return (this.attributi || {})[n]; }
  }
  const navigazioni = [];
  const eventi = [];
  const finestra = { customCards: [], dispatchEvent: (e) => { eventi.push(e); return true; } };
  const contesto = {
    HTMLElement: Elemento,
    customElements: {
      get: (nome) => definiti.get(nome),
      define: (nome, classe) => {
        if (definiti.has(nome)) throw new Error(`doppia definizione: ${nome}`);
        definiti.set(nome, classe);
      },
    },
    window: finestra,
    history: { pushState: (stato, titolo, url) => navigazioni.push(url) },
    CustomEvent: class { constructor(tipo, init) { this.type = tipo; this.detail = init && init.detail; } },
    localStorage: { getItem: () => null, setItem() {}, removeItem() {} },
    document: { createElement: () => new Elemento() },
    console: { info() {}, error() {}, warn() {}, log() {} },
  };
  vm.createContext(contesto);
  return { contesto, definiti, finestra, navigazioni, eventi };
}

function carica(contesto) {
  vm.runInContext(`(function () {\n${CODICE}\n})();`, contesto, { filename: FILE });
}

function sensoreVoti() {
  return {
    entity_id: "sensor.cvv_dashboard_mario_voti",
    state: "7",
    last_updated: "2026-10-01T10:00:00Z",
    attributes: { anno: "26/27" },
  };
}

function hassCon(callWS) {
  const voti = sensoreVoti();
  return { states: { [voti.entity_id]: voti }, callWS };
}

const RISPOSTA = { nome: "Mario", anno: 2026, anni: [2026], entita: {} };

test("the file defines the card, the editor and the panel once", () => {
  const { contesto, definiti, finestra } = nuovoContesto();
  carica(contesto);
  assert.deepEqual([...definiti.keys()].sort(), [
    "cvv-dashboard-card", "cvv-dashboard-card-editor", "cvv-dashboard-card-panel",
  ]);
  assert.equal(finestra.customCards.length, 1);
});

test("a second load of the file does not define the elements again", () => {
  const { contesto, definiti, finestra } = nuovoContesto();
  carica(contesto);
  assert.doesNotThrow(() => carica(contesto));
  assert.equal(definiti.size, 3);
  assert.equal(finestra.customCards.length, 1);
});

test("a hass object that arrives before setConfig does not throw", () => {
  const { contesto, definiti } = nuovoContesto();
  carica(contesto);
  const card = new (definiti.get("cvv-dashboard-card"))();
  assert.doesNotThrow(() => { card.hass = { states: {} }; });
});

test("a hass object that arrives before setConfig is processed after setConfig", async () => {
  const { contesto, definiti } = nuovoContesto();
  carica(contesto);
  const card = new (definiti.get("cvv-dashboard-card"))();
  card.hass = hassCon(() => Promise.resolve(RISPOSTA));
  card.setConfig({});
  await new Promise((r) => setImmediate(r));
  assert.doesNotMatch(card.shadowRoot.innerHTML, /Caricamento anno/);
  assert.doesNotMatch(card.shadowRoot.innerHTML, /non disponibili/);
});

test("a hass object without states does not throw", () => {
  const { contesto, definiti } = nuovoContesto();
  carica(contesto);
  const card = new (definiti.get("cvv-dashboard-card"))();
  card.setConfig({});
  assert.doesNotThrow(() => { card.hass = {}; });
});

test("a valid configuration is accepted", () => {
  const { contesto, definiti } = nuovoContesto();
  carica(contesto);
  const card = new (definiti.get("cvv-dashboard-card"))();
  for (const vista of [undefined, "combo", "medie", "voti", "bacheca", "agenda", "note", "scrutini", "compiti"]) {
    assert.doesNotThrow(() => card.setConfig({ vista }));
  }
});

test("an invalid configuration still gives a clear error", () => {
  const { contesto, definiti } = nuovoContesto();
  carica(contesto);
  const card = new (definiti.get("cvv-dashboard-card"))();
  assert.throws(() => card.setConfig({ vista: "xyz" }), /vista "xyz" non valida/);
});

test("a callWS that throws at once shows a message and the next update recovers", async () => {
  const { contesto, definiti } = nuovoContesto();
  carica(contesto);
  const card = new (definiti.get("cvv-dashboard-card"))();
  card.setConfig({});

  let pronta = false;
  const callWS = () => {
    if (!pronta) throw new Error("connessione non pronta");
    return Promise.resolve(RISPOSTA);
  };

  assert.doesNotThrow(() => { card.hass = hassCon(callWS); });
  await new Promise((r) => setImmediate(r));
  assert.match(card.shadowRoot.innerHTML, /Dati dell(&#39;|')anno non disponibili/);

  pronta = true;
  card.hass = hassCon(callWS);
  await new Promise((r) => setImmediate(r));
  assert.doesNotMatch(card.shadowRoot.innerHTML, /Dati dell(&#39;|')anno non disponibili/);
  assert.doesNotMatch(card.shadowRoot.innerHTML, /Caricamento anno/);
});

test("a rejected callWS shows a message and the next update recovers", async () => {
  const { contesto, definiti } = nuovoContesto();
  carica(contesto);
  const card = new (definiti.get("cvv-dashboard-card"))();
  card.setConfig({});

  let pronta = false;
  const callWS = () => (pronta ? Promise.resolve(RISPOSTA) : Promise.reject(new Error("chiusa")));

  card.hass = hassCon(callWS);
  await new Promise((r) => setImmediate(r));
  assert.match(card.shadowRoot.innerHTML, /Dati dell(&#39;|')anno non disponibili/);

  pronta = true;
  card.hass = hassCon(callWS);
  await new Promise((r) => setImmediate(r));
  assert.doesNotMatch(card.shadowRoot.innerHTML, /Dati dell(&#39;|')anno non disponibili/);
});

test("two cards in one page work with a shared hass object", async () => {
  const { contesto, definiti } = nuovoContesto();
  carica(contesto);
  const Card = definiti.get("cvv-dashboard-card");
  const carte = [new Card(), new Card()];
  carte.forEach((c) => c.setConfig({}));
  const hass = hassCon(() => Promise.resolve(RISPOSTA));
  carte.forEach((c) => { c.hass = hass; });
  await new Promise((r) => setImmediate(r));
  for (const c of carte) assert.doesNotMatch(c.shadowRoot.innerHTML, /non disponibili/);
});

/** Contenitore minimo: tiene solo l'avviso HACS come primo figlio. */
function contenitoreFinto() {
  const c = { figli: [] };
  c.querySelector = (sel) => c.figli.find((f) => sel === `.${f.className}`) || null;
  c.prepend = (el) => { c.figli.unshift(el); el.remove = () => { c.figli = c.figli.filter((x) => x !== el); }; };
  return c;
}

function hassHacs({ admin, lista, stato = "on" }) {
  const voti = sensoreVoti();
  const chiamate = [];
  const hass = {
    user: { is_admin: admin },
    states: {
      [voti.entity_id]: voti,
      "update.cvv_dashboard_update": { entity_id: "update.cvv_dashboard_update", state: stato, attributes: { latest_version: "1.0" } },
    },
    entities: { "update.cvv_dashboard_update": { platform: "hacs" } },
    callWS: (msg) => {
      chiamate.push(msg.type);
      return Promise.resolve(msg.type === "hacs/repositories/list" ? lista : RISPOSTA);
    },
  };
  return { hass, chiamate };
}

function cardConAvviso(definiti) {
  const card = new (definiti.get("cvv-dashboard-card"))();
  const titolo = contenitoreFinto();
  card.shadowRoot.querySelector = (sel) => (sel === ".titolo" ? titolo : null);
  card.setConfig({});
  card.connectedCallback();
  return { card, titolo };
}

const LISTA_HACS = [
  { id: "111", full_name: "other/repo", pending_upgrade: true },
  { id: "222", full_name: "Sythos/Classeviva-Dashboard", pending_upgrade: true },
];

test("an administrator sees the HACS alert when HACS reports an update for this repository", async () => {
  const { contesto, definiti } = nuovoContesto();
  carica(contesto);
  const { card, titolo } = cardConAvviso(definiti);
  const { hass } = hassHacs({ admin: true, lista: LISTA_HACS });
  card.hass = hass;
  await new Promise((r) => setImmediate(r));
  assert.equal(titolo.figli.length, 1);
  assert.equal(titolo.figli[0].getAttribute("aria-label"), "Open Home Assistant updates");
});

test("selecting the HACS alert opens the Home Assistant Updates page and does not call HACS again", async () => {
  const { contesto, definiti, navigazioni, eventi } = nuovoContesto();
  carica(contesto);
  const { card, titolo } = cardConAvviso(definiti);
  const { hass, chiamate } = hassHacs({ admin: true, lista: LISTA_HACS });
  card.hass = hass;
  await new Promise((r) => setImmediate(r));
  const chiamateBase = chiamate.length;
  let fermato = false;
  let annullato = false;
  titolo.figli[0].ascoltatori.click({ stopPropagation: () => { fermato = true; }, preventDefault: () => { annullato = true; } });
  assert.deepEqual(navigazioni, ["/config/updates"]);
  assert.equal(eventi.length, 1);
  assert.equal(eventi[0].type, "location-changed");
  assert.ok(fermato && annullato);
  assert.equal(chiamate.length, chiamateBase);
});

test("the HACS alert is hidden when the permission data is missing", async () => {
  const { contesto, definiti } = nuovoContesto();
  carica(contesto);
  const { card, titolo } = cardConAvviso(definiti);
  const { hass, chiamate } = hassHacs({ admin: true, lista: LISTA_HACS });
  delete hass.user;
  card.hass = hass;
  await new Promise((r) => setImmediate(r));
  assert.equal(titolo.figli.length, 0);
  assert.ok(!chiamate.includes("hacs/repositories/list"));
});

test("the HACS alert is hidden for a user who is not an administrator", async () => {
  const { contesto, definiti } = nuovoContesto();
  carica(contesto);
  const { card, titolo } = cardConAvviso(definiti);
  const { hass, chiamate } = hassHacs({ admin: false, lista: LISTA_HACS });
  card.hass = hass;
  await new Promise((r) => setImmediate(r));
  assert.equal(titolo.figli.length, 0);
  assert.ok(!chiamate.includes("hacs/repositories/list"));
});

test("an update of another HACS repository does not show the alert", async () => {
  const { contesto, definiti } = nuovoContesto();
  carica(contesto);
  const { card, titolo } = cardConAvviso(definiti);
  const { hass } = hassHacs({ admin: true, lista: [LISTA_HACS[0], { ...LISTA_HACS[1], pending_upgrade: false }] });
  card.hass = hass;
  await new Promise((r) => setImmediate(r));
  assert.equal(titolo.figli.length, 0);
});

test("a state update of a HACS entity changes the alert without a reload", async () => {
  const { contesto, definiti } = nuovoContesto();
  carica(contesto);
  const { card, titolo } = cardConAvviso(definiti);
  const primo = hassHacs({ admin: true, lista: LISTA_HACS });
  card.hass = primo.hass;
  await new Promise((r) => setImmediate(r));
  assert.equal(titolo.figli.length, 1);

  const secondo = hassHacs({ admin: true, lista: [{ ...LISTA_HACS[1], pending_upgrade: false }], stato: "off" });
  card.hass = secondo.hass;
  await new Promise((r) => setImmediate(r));
  assert.equal(titolo.figli.length, 0);
  assert.equal(secondo.chiamate.filter((t) => t === "hacs/repositories/list").length, 1);
});

test("a failing HACS command hides the alert and does not throw", async () => {
  const { contesto, definiti } = nuovoContesto();
  carica(contesto);
  const { card, titolo } = cardConAvviso(definiti);
  const { hass } = hassHacs({ admin: true, lista: LISTA_HACS });
  const base = hass.callWS;
  hass.callWS = (msg) => (msg.type === "hacs/repositories/list" ? Promise.reject({ code: "unknown_command" }) : base(msg));
  card.hass = hass;
  await new Promise((r) => setImmediate(r));
  assert.equal(titolo.figli.length, 0);
});
