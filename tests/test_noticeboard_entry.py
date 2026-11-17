# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Sythos <sythos@gmail.com>
# Author: Sythos <sythos@gmail.com>
#
# Tests of the noticeboard read service with two mocked entries.
# Run: python -m unittest discover -s tests
import asyncio
import pathlib
import textwrap
import unittest
from types import SimpleNamespace

_BASE = pathlib.Path(__file__).resolve().parent.parent / "custom_components" / "cvv_dashboard"


class HomeAssistantError(Exception):
    pass


class FakeApi:
    def __init__(self, testo):
        self.testo = testo
        self.chiamate = []

    async def leggi_comunicazione(self, codice, pub_id):
        self.chiamate.append((codice, pub_id))
        return self.testo


class FakeCoordinator:
    def __init__(self, testo, letto=False, pub_id="100"):
        self.api = FakeApi(testo)
        self.data = {"noticeboard": [
            {"pubId": pub_id, "evtCode": "CF", "readStatus": letto, "cntTitle": "T", "text": ""}
        ]}
        self.aggiornamenti = 0

    def async_set_updated_data(self, data):
        self.aggiornamenti += 1


def _carica(istanze):
    """Run the real source of the service handler with stubs for Home Assistant."""
    sorgente = (_BASE / "__init__.py").read_text(encoding="utf-8")
    inizio = sorgente.index("    def _scelte(call")
    fine = sorgente.index("    hass.services.async_register(", inizio)
    codice = textwrap.dedent(sorgente[inizio:fine])
    spazio = {
        "hass": object(),
        "_coordinatori": lambda hass: istanze,
        "HomeAssistantError": HomeAssistantError,
        "ServiceCall": object,
    }
    exec(codice, spazio)
    return spazio["leggi_comunicazione"]


def _chiama(servizio, **dati):
    return asyncio.run(servizio(SimpleNamespace(data=dati)))


class NoticeboardEntryTests(unittest.TestCase):
    def setUp(self):
        self.a = FakeCoordinator("testo A", letto=False)
        self.b = FakeCoordinator("testo B", letto=True)
        self.servizio = _carica({"a": self.a, "b": self.b})

    def test_second_entry_is_read_when_selected(self):
        esito = _chiama(self.servizio, pub_id="100", entry_id="b")
        self.assertEqual(esito["testo"], "testo B")
        self.assertEqual(self.a.api.chiamate, [])
        self.assertEqual(self.a.aggiornamenti, 0)
        self.assertFalse(self.a.data["noticeboard"][0]["readStatus"])
        self.assertEqual(self.a.data["noticeboard"][0]["text"], "")
        self.assertEqual(len(self.b.api.chiamate), 1)
        self.assertEqual(self.b.data["noticeboard"][0]["text"], "testo B")

    def test_first_entry_is_read_when_selected(self):
        esito = _chiama(self.servizio, pub_id="100", entry_id="a")
        self.assertEqual(esito["testo"], "testo A")
        self.assertTrue(self.a.data["noticeboard"][0]["readStatus"])
        self.assertEqual(self.b.api.chiamate, [])
        self.assertEqual(self.b.aggiornamenti, 0)

    def test_missing_publication_does_not_touch_the_other_entry(self):
        altro = FakeCoordinator("testo", pub_id="200")
        servizio = _carica({"a": self.a, "b": altro})
        with self.assertRaises(HomeAssistantError):
            _chiama(servizio, pub_id="200", entry_id="a")
        self.assertEqual(altro.api.chiamate, [])
        self.assertEqual(altro.aggiornamenti, 0)
        self.assertEqual(altro.data["noticeboard"][0]["text"], "")

    def test_unknown_entry_is_an_error(self):
        with self.assertRaises(HomeAssistantError):
            _chiama(self.servizio, pub_id="100", entry_id="x")
        self.assertEqual(self.a.api.chiamate, [])
        self.assertEqual(self.b.api.chiamate, [])

    def test_entry_is_required_with_two_entries(self):
        with self.assertRaises(HomeAssistantError):
            _chiama(self.servizio, pub_id="100")
        self.assertEqual(self.a.api.chiamate, [])
        self.assertEqual(self.b.api.chiamate, [])

    def test_single_entry_needs_no_entry_id(self):
        servizio = _carica({"a": self.a})
        self.assertEqual(_chiama(servizio, pub_id="100")["testo"], "testo A")


class CardBindingTests(unittest.TestCase):
    def test_card_sends_the_entry_with_the_read_request(self):
        scheda = (_BASE / "www" / "cvv-dashboard-card.js").read_text(encoding="utf-8")
        self.assertIn("entry_id: b.dataset.entry", scheda)
        self.assertIn('data-entry="${this._esc(', scheda)

    def test_noticeboard_attributes_carry_the_entry(self):
        sensore = (_BASE / "sensor.py").read_text(encoding="utf-8")
        classe = sensore[sensore.index("class NoticeboardSensor"):sensore.index("class NotesSensor")]
        self.assertIn('"entry_id": self._entry_id', classe)


if __name__ == "__main__":
    unittest.main()
