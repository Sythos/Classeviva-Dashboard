# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Sythos <sythos@gmail.com>
# Author: Sythos <sythos@gmail.com>
#
# Tests of the noticeboard read with made-up hosts, tokens and responses.
# Run: python -m unittest discover -s tests
import asyncio
import importlib.util
import pathlib
import sys
import types
import unittest

_DIR = (
    pathlib.Path(__file__).resolve().parent.parent
    / "custom_components" / "cvv_dashboard"
)


class _ClientError(Exception):
    pass


def _carica_api():
    """Load api.py as a package module, with a stub of aiohttp if it is missing."""
    try:
        import aiohttp  # noqa: F401
    except ImportError:
        stub = types.ModuleType("aiohttp")
        stub.ClientError = _ClientError
        stub.ClientSession = object
        sys.modules["aiohttp"] = stub
    pacchetto = types.ModuleType("cvv_pkg")
    pacchetto.__path__ = [str(_DIR)]
    sys.modules["cvv_pkg"] = pacchetto
    spec = importlib.util.spec_from_file_location("cvv_pkg.api", _DIR / "api.py")
    modulo = importlib.util.module_from_spec(spec)
    sys.modules["cvv_pkg.api"] = modulo
    spec.loader.exec_module(modulo)
    return modulo


api = _carica_api()
BASE_HOST = api.BASE_HOST


class _Risposta:
    def __init__(self, status, corpo):
        self.status = status
        self._corpo = corpo

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        return False

    async def json(self, content_type=None):
        return self._corpo


class _Sessione:
    """Fake session: answers by host and records every POST."""

    def __init__(self, risposte):
        self._risposte = risposte
        self.chiamate = []

    def post(self, url, headers=None):
        host = url.split("/")[2]
        self.chiamate.append((host, headers))
        return self._risposte[host]


def _client(sessione, anno):
    c = api.CvvDashboardApi(sessione, "utente", "password", anno)
    c.token = "token-corrente"
    c.token_ap = "token-storico"
    c.student_id = "1"
    c.newest_yy = 2026
    return c


def _esegui(coro):
    return asyncio.run(coro)


class NoticeboardReadTests(unittest.TestCase):
    def test_fixed_past_year_falls_back_to_current_server(self):
        sessione = _Sessione({
            "web25.spaggiari.eu": _Risposta(404, None),
            BASE_HOST: _Risposta(200, {"item": {"text": "testo"}}),
        })
        c = _client(sessione, 2025)
        self.assertEqual(_esegui(c.leggi_comunicazione("CF", 7)), "testo")
        self.assertEqual(
            [h for h, _ in sessione.chiamate], ["web25.spaggiari.eu", BASE_HOST]
        )

    def test_failure_on_every_server_gives_none_and_no_cache(self):
        sessione = _Sessione({
            "web25.spaggiari.eu": _Risposta(404, None),
            BASE_HOST: _Risposta(404, None),
        })
        c = _client(sessione, 2025)
        self.assertIsNone(_esegui(c.leggi_comunicazione("CF", 7)))
        self.assertEqual(c._testi, {})

    def test_current_year_does_not_repeat_current_server(self):
        sessione = _Sessione({BASE_HOST: _Risposta(404, None)})
        c = _client(sessione, None)
        self.assertIsNone(_esegui(c.leggi_comunicazione("CF", 7)))
        self.assertEqual([h for h, _ in sessione.chiamate], [BASE_HOST])

    def test_cache_path_makes_no_request(self):
        sessione = _Sessione({})
        c = _client(sessione, 2025)
        c._testi["7"] = "in cache"
        self.assertEqual(_esegui(c.leggi_comunicazione("CF", 7)), "in cache")
        self.assertEqual(sessione.chiamate, [])

    def test_year_plan_keeps_only_the_historical_server(self):
        c = _client(_Sessione({}), 2025)
        self.assertEqual(
            [h for h, _a, _s in c.piani_anno()], ["web25.spaggiari.eu"]
        )


if __name__ == "__main__":
    unittest.main()
