# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Sythos <sythos@gmail.com>
# Author: Sythos <sythos@gmail.com>
#
# Tests of the lessons helpers with made-up data. Run: python -m unittest discover -s tests
import importlib.util
import pathlib
import unittest
from datetime import date

_FILE = (
    pathlib.Path(__file__).resolve().parent.parent
    / "custom_components" / "cvv_dashboard" / "lessons.py"
)
_SPEC = importlib.util.spec_from_file_location("cvv_lessons", _FILE)
lessons = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(lessons)


class NormalizeTests(unittest.TestCase):
    def test_fields_are_mapped(self):
        body = {"lessons": [{
            "evtDate": "2026-10-30", "evtHPos": 2, "evtDuration": 1,
            "subjectDesc": "ITALIANO", "lessonType": "Lezione",
            "authorName": "ROSSI MARIA", "lessonArg": "  Accoglienza   e gioco libero ",
        }]}
        voce = lessons.normalizza(body)[0]
        self.assertEqual(voce["data"], "2026-10-30")
        self.assertEqual(voce["ora"], 2)
        self.assertEqual(voce["materia"], "ITALIANO")
        self.assertEqual(voce["docente"], "ROSSI MARIA")
        self.assertEqual(voce["argomento"], "Accoglienza e gioco libero")

    def test_compact_date_and_missing_fields(self):
        voce = lessons.normalizza([{"evtDate": "20261030"}])[0]
        self.assertEqual(voce["data"], "2026-10-30")
        self.assertEqual(voce["argomento"], "")

    def test_bad_shapes_give_empty_list(self):
        for body in (None, "x", {}, {"lessons": "x"}, [1, "a"]):
            self.assertEqual(lessons.normalizza(body), [])


class OrderTests(unittest.TestCase):
    def test_newest_first(self):
        voci = [
            {"data": "2026-10-29", "ora": 5},
            {"data": "2026-10-30", "ora": 1},
            {"data": "2026-10-30", "ora": 3},
        ]
        ordinate = lessons.ordina(voci)
        self.assertEqual(
            [(v["data"], v["ora"]) for v in ordinate],
            [("2026-10-30", 3), ("2026-10-30", 1), ("2026-10-29", 5)],
        )

    def test_range_is_last_week(self):
        inizio, fine = lessons.intervallo(date(2026, 10, 30))
        self.assertEqual(inizio, date(2026, 10, 24))
        self.assertEqual(fine, date(2026, 10, 30))


if __name__ == "__main__":
    unittest.main()
