# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Sythos <sythos@gmail.com>
# Author: Sythos <sythos@gmail.com>
#
# Tests of the absences helpers with made-up data. Run: python -m unittest discover -s tests
import importlib.util
import pathlib
import unittest

_FILE = (
    pathlib.Path(__file__).resolve().parent.parent
    / "custom_components" / "cvv_dashboard" / "absences.py"
)
_SPEC = importlib.util.spec_from_file_location("cvv_absences", _FILE)
absences = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(absences)

_INIT = _FILE.parent / "__init__.py"


def _evento(codice, data, **extra):
    return {"evtCode": codice, "evtDate": data, "isJustified": False, **extra}


class NormalizeTests(unittest.TestCase):
    def test_three_types_and_unknown_code(self):
        body = {"events": [
            _evento("ABA0", "2026-10-01"),
            _evento("ABR0", "2026-10-02"),
            _evento("ABU0", "2026-10-03"),
            _evento("XYZ9", "2026-10-04"),
        ]}
        voci = absences.normalizza(body)
        self.assertEqual([v["tipo"] for v in voci], ["assenza", "ritardo", "uscita", "altro"])
        self.assertEqual(voci[3]["codice"], "XYZ9")

    def test_justified_reason_and_hour(self):
        body = {"events": [
            _evento("ABR0", "2026-10-02", isJustified=True, justifReasonDesc="Visita", evtHPos=2),
            _evento("ABU0", "2026-10-03", evtValue="11:30"),
        ]}
        primo, secondo = absences.normalizza(body)
        self.assertTrue(primo["giustificata"])
        self.assertEqual(primo["motivo"], "Visita")
        self.assertEqual(primo["ora"], 2)
        self.assertFalse(secondo["giustificata"])
        self.assertEqual(secondo["ora"], "11:30")

    def test_missing_fields_and_bad_bodies(self):
        self.assertEqual(absences.normalizza({"events": [{}]})[0]["tipo"], "altro")
        for body in (None, "x", {}, {"events": "x"}, [1, None]):
            self.assertEqual(absences.normalizza(body), [])

    def test_compact_date(self):
        self.assertEqual(absences.normalizza([_evento("ABA0", "20261001")])[0]["data"], "2026-10-01")

    def test_empty_list(self):
        self.assertEqual(absences.normalizza({"events": []}), [])


class SortTests(unittest.TestCase):
    def test_newest_first_then_highest_hour(self):
        voci = [
            {"data": "2026-10-01", "ora": 1},
            {"data": "2026-10-05", "ora": ""},
            {"data": "2026-10-01", "ora": 3},
        ]
        ordinate = absences.ordina(voci)
        self.assertEqual(
            [(v["data"], v["ora"]) for v in ordinate],
            [("2026-10-05", ""), ("2026-10-01", 3), ("2026-10-01", 1)],
        )


class WiringTests(unittest.TestCase):
    def test_permission_key_and_kept_section(self):
        self.assertIn('"absences"', _INIT.read_text(encoding="utf-8"))
        coord = (_FILE.parent / "coordinator.py").read_text(encoding="utf-8")
        self.assertIn('"assenze"', coord)


if __name__ == "__main__":
    unittest.main()
