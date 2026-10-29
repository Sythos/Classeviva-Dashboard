# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Sythos <sythos@gmail.com>
# Author: Sythos <sythos@gmail.com>
#
# Tests of the Agenda state with a fake portal. Run: python -m unittest discover -s tests
import asyncio
import importlib.util
import pathlib
import sys
import types
import unittest

_DIR = pathlib.Path(__file__).resolve().parent.parent / "custom_components" / "cvv_dashboard"


def _carica_web():
    """Load web.py as part of a small package, with a stub of aiohttp."""
    if "aiohttp" not in sys.modules:
        stub = types.ModuleType("aiohttp")
        stub.ClientError = Exception
        sys.modules["aiohttp"] = stub
    pacchetto = types.ModuleType("cvv_agenda_pkg")
    pacchetto.__path__ = [str(_DIR)]
    sys.modules["cvv_agenda_pkg"] = pacchetto
    for nome in ("const", "web"):
        spec = importlib.util.spec_from_file_location(f"cvv_agenda_pkg.{nome}", _DIR / f"{nome}.py")
        modulo = importlib.util.module_from_spec(spec)
        sys.modules[f"cvv_agenda_pkg.{nome}"] = modulo
        spec.loader.exec_module(modulo)
    return sys.modules["cvv_agenda_pkg.web"]


web = _carica_web()

PIANI = [("web.example", 2026, False), ("web25.example", 2025, True)]
EVENTO = {
    "evento_id": 1, "start": "2025-10-05T00:00:00", "end": "2025-10-05T00:00:00",
    "allDay": True, "title": "Test", "tipo": "nota", "nota_2": "Test",
}


def _api(risposte):
    """Web API with a fake `_con_sessione`: one answer for each host."""
    api = web.CvvDashboardWebApi.__new__(web.CvvDashboardWebApi)

    async def sessione(host, storico, azione, label="pagina", *, segna=True):
        return risposte[host]

    api._con_sessione = sessione
    api._scarica_eventi = lambda host, anno: None
    return api


def _esegui(api):
    return asyncio.run(api.async_fetch_agenda(PIANI))


class AgendaStateTests(unittest.TestCase):
    def test_all_requests_failed_gives_error(self):
        risultato = _esegui(_api({"web.example": None, "web25.example": None}))
        self.assertEqual(risultato["stato"], "errore")
        self.assertEqual(risultato["agenda"], [])

    def test_empty_answer_is_valid(self):
        risultato = _esegui(_api({"web.example": [], "web25.example": []}))
        self.assertEqual(risultato["stato"], "ok")
        self.assertEqual(risultato["agenda"], [])

    def test_failed_current_year_and_events_of_previous_year(self):
        api = _api({"web.example": None, "web25.example": [EVENTO]})
        risultato = _esegui(api)
        self.assertEqual(risultato["stato"], "ok")
        self.assertEqual(risultato["anno_inizio"], 2025)

    def test_events_of_current_year_keep_the_year(self):
        risultato = _esegui(_api({"web.example": [EVENTO], "web25.example": None}))
        self.assertEqual(risultato["stato"], "ok")
        self.assertEqual(risultato["anno_inizio"], 2026)


if __name__ == "__main__":
    unittest.main()
