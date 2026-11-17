# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Sythos <sythos@gmail.com>
# Author: Sythos <sythos@gmail.com>
#
# Tests of the read permission check with two students and made-up users.
# Run: python -m unittest discover -s tests
import asyncio
import importlib.util
import pathlib
import sys
import types
import unittest
from unittest import mock

_DIR = pathlib.Path(__file__).resolve().parent.parent / "custom_components" / "cvv_dashboard"

_ENTITA = {}  # entry_id -> list of entity objects


def _stub(nome, **attributi):
    modulo = types.ModuleType(nome)
    modulo.__dict__.update(attributi)
    sys.modules[nome] = modulo
    return modulo


class _Entita:
    def __init__(self, entity_id, entry_id, platform="cvv_dashboard", domain="sensor"):
        self.entity_id = entity_id
        self.config_entry_id = entry_id
        self.platform = platform
        self.domain = domain


def _carica():
    for nome in (
        "homeassistant", "homeassistant.auth", "homeassistant.auth.permissions",
        "homeassistant.auth.permissions.const", "homeassistant.core",
        "homeassistant.helpers", "homeassistant.helpers.entity_registry",
        "homeassistant.components", "homeassistant.components.http", "aiohttp",
    ):
        _stub(nome)
    sys.modules["homeassistant.auth.permissions.const"].POLICY_READ = "read"
    sys.modules["homeassistant.core"].HomeAssistant = object
    registro = sys.modules["homeassistant.helpers.entity_registry"]
    registro.async_get = lambda hass: None
    registro.async_entries_for_config_entry = lambda reg, entry_id: _ENTITA.get(entry_id, [])
    sys.modules["homeassistant.helpers"].entity_registry = registro
    _stub("cvvtest")
    sys.modules["cvvtest"].__path__ = [str(_DIR)]
    for nome in ("const", "access"):
        spec = importlib.util.spec_from_file_location(f"cvvtest.{nome}", _DIR / f"{nome}.py")
        modulo = importlib.util.module_from_spec(spec)
        sys.modules[f"cvvtest.{nome}"] = modulo
        spec.loader.exec_module(modulo)
    return sys.modules["cvvtest.access"]


access = _carica()


class _Utente:
    def __init__(self, leggibili, admin=False):
        self.is_admin = admin
        self.permissions = mock.Mock()
        self.permissions.check_entity = lambda entity_id, policy: (
            policy == "read" and entity_id in leggibili
        )


def setUpModule():
    _ENTITA.clear()
    _ENTITA["entry_a"] = [_Entita("sensor.a_voti", "entry_a"), _Entita("sensor.a_bacheca", "entry_a")]
    _ENTITA["entry_b"] = [_Entita("sensor.b_voti", "entry_b"), _Entita("sensor.b_bacheca", "entry_b")]


class IdIstanzaTests(unittest.TestCase):
    def test_strips_year(self):
        self.assertEqual(access.id_istanza("entry_a:2025"), "entry_a")
        self.assertEqual(access.id_istanza("entry_a"), "entry_a")
        self.assertIsNone(access.id_istanza(None))


class PuoLeggereTests(unittest.TestCase):
    def test_reader_of_a_only(self):
        utente = _Utente({"sensor.a_voti", "sensor.a_bacheca"})
        self.assertTrue(access.puo_leggere(None, utente, "entry_a"))
        self.assertFalse(access.puo_leggere(None, utente, "entry_b"))

    def test_partial_permission_is_denied(self):
        utente = _Utente({"sensor.a_voti"})
        self.assertFalse(access.puo_leggere(None, utente, "entry_a"))

    def test_admin_reads_all(self):
        admin = _Utente(set(), admin=True)
        self.assertTrue(access.puo_leggere(None, admin, "entry_a"))
        self.assertTrue(access.puo_leggere(None, admin, "entry_b"))

    def test_missing_user_or_entry_is_denied(self):
        self.assertFalse(access.puo_leggere(None, None, "entry_a"))
        self.assertFalse(access.puo_leggere(None, _Utente(set(), admin=True), None))
        self.assertFalse(access.puo_leggere(None, _Utente({"x"}), "entry_unknown"))


class SourceWiringTests(unittest.TestCase):
    """The view and the services must call the check before they return data."""

    def test_download_view_checks_before_api(self):
        testo = (_DIR / "download.py").read_text(encoding="utf-8")
        self.assertIn("puo_leggere(self.hass, request.get(\"hass_user\")", testo)
        self.assertLess(testo.index("puo_leggere("), testo.index("api = coordinator.api"))
        self.assertIn("status=403", testo)

    def test_services_use_the_filtered_choice(self):
        testo = (_DIR / "__init__.py").read_text(encoding="utf-8")
        self.assertEqual(testo.count("await _scelte(call)"), 3)
        self.assertIn("puo_leggere(hass, user, k)", testo)
        self.assertNotIn(" _scelte(call).values()", testo)
        self.assertNotIn("= _scelte(call)", testo)


if __name__ == "__main__":
    unittest.main()
