# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Sythos <sythos@gmail.com>
# Author: Sythos <sythos@gmail.com>
#
# Tests of the download view and of the services with two students and made-up users.
# The real code runs. Home Assistant is replaced by small stubs.
# Run: python -m unittest discover -s tests
import asyncio
import importlib.util
import pathlib
import sys
import types
import unittest
from unittest import mock

_DIR = pathlib.Path(__file__).resolve().parent.parent / "custom_components" / "cvv_dashboard"
_PKG = "cvvflows"

_ENTITA = {}  # entry_id -> list of entity objects


class _Unauthorized(Exception):
    def __init__(self, context=None, permission=None):
        super().__init__("unauthorized")
        self.permission = permission


class _HAError(Exception):
    pass


class _Risposta(Exception):
    """Stands for web.Response (and for web.HTTPFound, which is raised)."""

    def __init__(self, body=None, status=200, text=None, **kwargs):
        super().__init__(text or body)
        self.status = status
        self.text = text
        self.body = body


class _Reindirizza(_Risposta):
    def __init__(self, location):
        super().__init__(status=302, text=location)
        self.location = location


class _Coordinatore:
    """Stands for CvvDashboardCoordinator: one student."""

    def __init__(self, nome):
        self.nome = nome
        self.data = {
            "noticeboard": [{"pubId": "7", "evtCode": "CF", "cntTitle": nome,
                             "pubDT": "2026-11-01", "attachments": []}],
            "scrutini": [{"descrizione": nome}],
        }
        self.api = mock.Mock()
        self.api.get_download_url = mock.AsyncMock(return_value=f"https://cdn.test/{nome}")
        self.api.leggi_comunicazione = mock.AsyncMock(return_value=f"testo {nome}")
        self.web = mock.Mock()
        self.web.async_scarica_scrutinio = mock.AsyncMock(return_value=(b"%PDF", "application/pdf"))
        self.async_testi_bacheca = mock.AsyncMock(return_value=1)
        self.async_request_refresh = mock.AsyncMock()
        self.async_set_updated_data = mock.Mock()


class _Entita:
    def __init__(self, entity_id, platform="cvv_dashboard", domain="sensor"):
        self.entity_id = entity_id
        self.platform = platform
        self.domain = domain


class _Utente:
    def __init__(self, leggibili, admin=False):
        self.is_admin = admin
        self.permissions = mock.Mock()
        self.permissions.check_entity = lambda entity_id, policy: (
            policy == "read" and entity_id in leggibili
        )


def _modulo(nome, **attributi):
    modulo = types.ModuleType(nome)
    modulo.__dict__.update(attributi)
    return modulo


def _carica():
    registro = _modulo(
        "homeassistant.helpers.entity_registry",
        async_get=lambda hass: None,
        async_entries_for_config_entry=lambda reg, entry_id: _ENTITA.get(entry_id, []),
    )
    web = _modulo("aiohttp.web", Response=_Risposta, HTTPFound=_Reindirizza, StreamResponse=object)
    helpers = _modulo("homeassistant.helpers", entity_registry=registro)
    stub = {
        "voluptuous": mock.MagicMock(),
        "aiohttp": _modulo("aiohttp", web=web),
        "aiohttp.web": web,
        "homeassistant": _modulo("homeassistant"),
        "homeassistant.auth": _modulo("homeassistant.auth"),
        "homeassistant.auth.permissions": _modulo("homeassistant.auth.permissions"),
        "homeassistant.auth.permissions.const": _modulo(
            "homeassistant.auth.permissions.const", POLICY_READ="read"
        ),
        "homeassistant.components": mock.MagicMock(),
        "homeassistant.components.frontend": mock.MagicMock(),
        "homeassistant.components.http": _modulo(
            "homeassistant.components.http", HomeAssistantView=object, StaticPathConfig=object
        ),
        "homeassistant.config_entries": mock.MagicMock(),
        "homeassistant.core": _modulo(
            "homeassistant.core", HomeAssistant=object, ServiceCall=object,
            SupportsResponse=mock.MagicMock(),
        ),
        "homeassistant.exceptions": _modulo(
            "homeassistant.exceptions", HomeAssistantError=_HAError, Unauthorized=_Unauthorized
        ),
        "homeassistant.helpers": helpers,
        "homeassistant.helpers.config_validation": mock.MagicMock(),
        "homeassistant.helpers.entity_registry": registro,
        "homeassistant.loader": mock.MagicMock(),
        _PKG: _modulo(_PKG),
    }
    stub[_PKG].__path__ = [str(_DIR)]
    for nome in ("coordinator", "sensor", "talks"):
        stub[f"{_PKG}.{nome}"] = mock.MagicMock()
    stub[f"{_PKG}.coordinator"].CvvDashboardCoordinator = _Coordinatore
    moduli = {}
    with mock.patch.dict(sys.modules, stub):
        for nome in ("const", "access", "download", "__init__"):
            nome_completo = _PKG if nome == "__init__" else f"{_PKG}.{nome}"
            spec = importlib.util.spec_from_file_location(
                nome_completo, _DIR / f"{nome}.py",
                submodule_search_locations=[str(_DIR)] if nome == "__init__" else None,
            )
            modulo = importlib.util.module_from_spec(spec)
            sys.modules[nome_completo] = modulo
            spec.loader.exec_module(modulo)
            moduli[nome] = modulo
    return moduli


_MODULI = _carica()
_DOMINIO = _MODULI["const"].DOMAIN


def _run(coro):
    return asyncio.run(coro)


class _Hass:
    def __init__(self, utenti):
        self.coord_a = _Coordinatore("A")
        self.coord_b = _Coordinatore("B")
        self.coord_b_anno = _Coordinatore("B2025")
        self.data = {
            _DOMINIO: {
                "entry_a": self.coord_a,
                "entry_b": self.coord_b,
                "_anni": {"entry_b:2025": {"coord": self.coord_b_anno}},
            }
        }
        self.auth = mock.Mock()
        self.auth.async_get_user = mock.AsyncMock(side_effect=lambda uid: utenti.get(uid))
        self.servizi = {}
        self.services = mock.Mock()
        self.services.has_service = lambda dominio, nome: False
        self.services.async_register = lambda dominio, nome, funzione, **kw: self.servizi.update(
            {nome: funzione}
        )


class _Chiamata:
    def __init__(self, dati, user_id):
        self.data = dati
        self.context = types.SimpleNamespace(user_id=user_id)


def _prepara():
    _ENTITA.clear()
    _ENTITA["entry_a"] = [_Entita("sensor.a_voti"), _Entita("sensor.a_bacheca")]
    _ENTITA["entry_b"] = [_Entita("sensor.b_voti"), _Entita("sensor.b_bacheca")]
    utenti = {
        "lettore_a": _Utente({"sensor.a_voti", "sensor.a_bacheca"}),
        "lettore_b": _Utente({"sensor.b_voti", "sensor.b_bacheca"}),
        "nessuno": _Utente(set()),
        "admin": _Utente(set(), admin=True),
    }
    return _Hass(utenti), utenti


class DownloadViewTests(unittest.TestCase):
    def setUp(self):
        self.hass, self.utenti = _prepara()
        self.vista = _MODULI["download"].CvvDashboardDownloadView(self.hass)

    def _get(self, utente, entry_id, **extra):
        query = {"entry_id": entry_id, "kind": "noticeboard", "evt": "CF", "pub": "7", "num": "1"}
        query.update(extra)
        richiesta = types.SimpleNamespace(query=query, get=lambda k, d=None: {"hass_user": utente}.get(k, d))
        try:
            return _run(self.vista.get(richiesta))
        except _Risposta as risposta:
            return risposta

    def test_reader_of_a_gets_a_and_not_b(self):
        utente = self.utenti["lettore_a"]
        ok = self._get(utente, "entry_a")
        self.assertEqual(ok.status, 302)
        self.assertEqual(ok.location, "https://cdn.test/A")
        negato = self._get(utente, "entry_b")
        self.assertEqual(negato.status, 403)
        self.hass.coord_b.api.get_download_url.assert_not_called()

    def test_year_key_uses_the_real_entry(self):
        self.assertEqual(self._get(self.utenti["lettore_b"], "entry_b:2025").status, 302)
        self.assertEqual(self._get(self.utenti["lettore_a"], "entry_b:2025").status, 403)
        self.hass.coord_b_anno.api.get_download_url.assert_called_once()

    def test_report_download_is_checked(self):
        negato = self._get(self.utenti["lettore_a"], "entry_b", kind="scrutinio", indice="0")
        self.assertEqual(negato.status, 403)
        self.hass.coord_b.web.async_scarica_scrutinio.assert_not_called()
        ok = self._get(self.utenti["lettore_b"], "entry_b", kind="scrutinio", indice="0")
        self.assertEqual(ok.status, 200)

    def test_user_without_permission_or_missing_user_is_denied(self):
        self.assertEqual(self._get(self.utenti["nessuno"], "entry_a").status, 403)
        self.assertEqual(self._get(None, "entry_a").status, 403)

    def test_admin_reads_both(self):
        admin = self.utenti["admin"]
        self.assertEqual(self._get(admin, "entry_a").status, 302)
        self.assertEqual(self._get(admin, "entry_b").status, 302)


class ServiceTests(unittest.TestCase):
    def setUp(self):
        self.hass, _ = _prepara()
        _MODULI["__init__"]._registra_servizi(self.hass)

    def _chiama(self, nome, dati, user_id):
        return _run(self.hass.servizi[nome](_Chiamata(dati, user_id)))

    def test_read_message_of_own_student(self):
        risultato = self._chiama("leggi_comunicazione", {"pub_id": "7", "entry_id": "entry_a"}, "lettore_a")
        self.assertEqual(risultato["testo"], "testo A")
        self.hass.coord_a.api.leggi_comunicazione.assert_awaited_once()

    def test_read_message_of_other_student_is_denied(self):
        with self.assertRaises(_Unauthorized):
            self._chiama("leggi_comunicazione", {"pub_id": "7", "entry_id": "entry_b"}, "lettore_a")
        self.hass.coord_b.api.leggi_comunicazione.assert_not_called()
        self.assertNotIn("text", self.hass.coord_b.data["noticeboard"][0])

    def test_read_message_without_entry_id_skips_unreadable_students(self):
        risultato = self._chiama("leggi_comunicazione", {"pub_id": "7"}, "lettore_b")
        self.assertEqual(risultato["testo"], "testo B")
        self.hass.coord_a.api.leggi_comunicazione.assert_not_called()

    def test_user_without_permission_is_denied_on_every_service(self):
        for nome in ("leggi_comunicazione", "carica_testi_bacheca", "aggiorna"):
            with self.subTest(servizio=nome):
                with self.assertRaises(_Unauthorized):
                    self._chiama(nome, {"pub_id": "7"} if nome == "leggi_comunicazione" else {}, "nessuno")
        self.hass.coord_a.api.leggi_comunicazione.assert_not_called()
        self.hass.coord_a.async_testi_bacheca.assert_not_called()
        self.hass.coord_a.async_request_refresh.assert_not_called()

    def test_load_texts_and_refresh_act_only_on_readable_students(self):
        self.assertEqual(self._chiama("carica_testi_bacheca", {}, "lettore_a"), {"completate": 1})
        self.hass.coord_a.async_testi_bacheca.assert_awaited_once()
        self.hass.coord_b.async_testi_bacheca.assert_not_called()
        self._chiama("aggiorna", {}, "lettore_b")
        self.hass.coord_b.async_request_refresh.assert_awaited_once()
        self.hass.coord_a.async_request_refresh.assert_not_called()

    def test_admin_and_calls_without_user_keep_full_access(self):
        self.assertEqual(self._chiama("carica_testi_bacheca", {}, "admin"), {"completate": 2})
        self.assertEqual(self._chiama("carica_testi_bacheca", {}, None), {"completate": 2})


if __name__ == "__main__":
    unittest.main()
