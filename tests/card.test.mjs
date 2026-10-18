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
    addEventListener() {}
  }
  const finestra = { customCards: [] };
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
    localStorage: { getItem: () => null, setItem() {}, removeItem() {} },
    document: { createElement: () => new Elemento() },
    console: { info() {}, error() {}, warn() {}, log() {} },
  };
  vm.createContext(contesto);
  return { contesto, definiti, finestra };
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
