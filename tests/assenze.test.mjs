// SPDX-License-Identifier: MIT
// Copyright (c) 2026 Sythos <sythos@gmail.com>
// Author: Sythos <sythos@gmail.com>
//
// Tests of the Assenze e Ritardi view of the card. They use made-up data only.

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

function nuovaScheda(items, assente = false) {
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
  card.setConfig({ vista: "assenze" });
  const da = items.filter((x) => !x.giustificata).length;
  const ent = assente ? {} : { assenze: { state: String(da), attributes: { items, da_giustificare: da } } };
  return { card, ent };
}

test("the view shows the newest record first with a text status", () => {
  const { card, ent } = nuovaScheda([
    { data: "2026-10-01", ora: "", tipo: "assenza", giustificata: true, motivo: "Malattia" },
    { data: "2026-10-05", ora: 2, tipo: "ritardo", giustificata: false, motivo: "" },
    { data: "2026-10-05", ora: 4, tipo: "uscita", giustificata: false, motivo: "" },
  ]);
  const html = card._vistaAssenze(ent);
  assert.ok(html.indexOf("Uscita") < html.indexOf("Ritardo"));
  assert.ok(html.indexOf("Ritardo") < html.indexOf("Assenza"));
  assert.match(html, /Giustificata/);
  assert.match(html, /Da giustificare/);
  assert.match(html, /Malattia/);
  assert.doesNotMatch(html, /<button|<a /);
});

test("the view escapes the reason text", () => {
  const { card, ent } = nuovaScheda([
    { data: "2026-10-01", tipo: "assenza", giustificata: true, motivo: "<img src=x onerror=1>" },
  ]);
  assert.doesNotMatch(card._vistaAssenze(ent), /<img/);
});

test("the view shows the empty and error states", () => {
  const vuota = nuovaScheda([]);
  assert.match(vuota.card._vistaAssenze(vuota.ent), /Nessuna assenza, ritardo o uscita per questo anno scolastico/);
  const errore = nuovaScheda([], true);
  assert.match(errore.card._vistaAssenze(errore.ent), /Assenze non disponibili/);
});

test("the tab counter shows the records that need justification and hides zero", () => {
  const { card, ent } = nuovaScheda([{ data: "2026-10-01", tipo: "assenza", giustificata: false }]);
  assert.match(card._contatore("assenze", ent), /tag nuovo">1</);
  const zero = nuovaScheda([{ data: "2026-10-01", tipo: "assenza", giustificata: true }]);
  assert.equal(zero.card._contatore("assenze", zero.ent), "");
});
