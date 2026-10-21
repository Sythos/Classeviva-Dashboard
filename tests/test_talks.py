# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Sythos <sythos@gmail.com>
# Author: Sythos <sythos@gmail.com>
#
# Tests of the talks helpers with made-up data. Run: python -m unittest discover -s tests
import importlib.util
import pathlib
import unittest
from datetime import date, timedelta

_FILE = (
    pathlib.Path(__file__).resolve().parent.parent
    / "custom_components" / "cvv_dashboard" / "talks.py"
)
_SPEC = importlib.util.spec_from_file_location("cvv_talks", _FILE)
talks = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(talks)

OGGI = date(2026, 10, 21)


def _voce(giorni, ora="09:00", docente="Docente A", stato="disponibile"):
    return {
        "data": (OGGI + timedelta(days=giorni)).isoformat(),
        "ora_inizio": ora, "docente": docente, "stato": stato,
    }


class RangeTests(unittest.TestCase):
    def test_range_is_28_days(self):
        primo, ultimo = talks.intervallo(OGGI)
        self.assertEqual(primo, OGGI)
        self.assertEqual((ultimo - primo).days, 27)

    def test_filter_edges(self):
        voci = [_voce(-1), _voce(0), _voce(27), _voce(28)]
        giorni = [v["data"] for v in talks.filtra_ordina(voci, OGGI)]
        self.assertEqual(giorni, [_voce(0)["data"], _voce(27)["data"]])

    def test_range_moves_after_midnight(self):
        voci = [_voce(0), _voce(28)]
        domani = OGGI + timedelta(days=1)
        giorni = [v["data"] for v in talks.filtra_ordina(voci, domani)]
        self.assertEqual(giorni, [_voce(28)["data"]])

    def test_request_date_format(self):
        self.assertEqual(talks.formato_richiesta(OGGI), "20261021")

    def test_sort_by_date_then_time(self):
        voci = [_voce(2, "10:00"), _voce(1, "11:00"), _voce(1, "09:00")]
        ordinate = talks.filtra_ordina(voci, OGGI)
        self.assertEqual(
            [(v["data"], v["ora_inizio"]) for v in ordinate],
            [(_voce(1)["data"], "09:00"), (_voce(1)["data"], "11:00"), (_voce(2)["data"], "10:00")],
        )

    def test_empty_list(self):
        self.assertEqual(talks.filtra_ordina([], OGGI), [])
        self.assertEqual(talks.unisci(None, None), [])


class MergeTests(unittest.TestCase):
    def test_booked_talk_marks_the_slot(self):
        slot = {"frames": [
            {"id": 1, "teacherName": "Docente A", "date": "2026-10-22", "startTime": "09:00"},
            {"id": 2, "teacherName": "Docente B", "date": "2026-10-23", "startTime": "10:00"},
        ]}
        prenotati = {"talks": [
            {"id": 1, "teacherName": "Docente A", "date": "2026-10-22", "startTime": "09:00",
             "room": "Aula 3", "url": "https://example.org/m"},
        ]}
        voci = talks.unisci(slot, prenotati)
        self.assertEqual(len(voci), 2)
        self.assertEqual(voci[0]["stato"], "prenotato")
        self.assertEqual(voci[0]["aula"], "Aula 3")
        self.assertEqual(voci[1]["stato"], "disponibile")
        self.assertEqual(voci[1]["aula"], "")

    def test_booked_talk_without_slot_is_added(self):
        voci = talks.unisci({"frames": []}, {"talks": [
            {"teacherName": "Docente C", "date": "2026-10-24T15:30:00"},
        ]})
        self.assertEqual(voci[0]["stato"], "prenotato")
        self.assertEqual(voci[0]["ora_inizio"], "15:30")

    def test_missing_fields_stay_empty(self):
        voci = talks.unisci({"frames": [{"date": "2026-10-22"}]}, None)
        self.assertEqual(voci[0]["docente"], "")
        self.assertEqual(voci[0]["link"], "")

    def test_entry_without_date_is_dropped(self):
        self.assertEqual(talks.unisci({"frames": [{"teacherName": "X"}]}, None), [])


if __name__ == "__main__":
    unittest.main()
