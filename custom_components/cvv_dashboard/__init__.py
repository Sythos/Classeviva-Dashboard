# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Sythos <sythos@gmail.com>
# Author: Sythos <sythos@gmail.com>
#
# MIT License
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""Integrazione CVV Dashboard per Home Assistant."""
from __future__ import annotations

import logging
from pathlib import Path

import voluptuous as vol

from homeassistant.auth.permissions.const import POLICY_READ
from homeassistant.components import websocket_api
from homeassistant.components.frontend import add_extra_js_url
from homeassistant.components.http import StaticPathConfig
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall, SupportsResponse, callback
from homeassistant.exceptions import HomeAssistantError, Unauthorized
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers import entity_registry as er
from homeassistant.loader import async_get_integration

from .const import CONF_ANNO, CONF_PASSWORD, CONF_USERNAME, DOMAIN
from .coordinator import CvvDashboardCoordinator
from .download import CvvDashboardDownloadView
from .sensor import card_data

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["sensor", "calendar"]

# La card Lovelace viaggia dentro l'integrazione e viene servita da qui.
CARD_URL_BASE = "/cvv_dashboard_static"
CARD_FILE = "cvv-dashboard-card.js"

SERVIZIO_LEGGI = "leggi_comunicazione"
SERVIZIO_TESTI = "carica_testi_bacheca"
SERVIZIO_AGGIORNA = "aggiorna"
SCHEMA_LEGGI = vol.Schema(
    {
        vol.Required("pub_id"): cv.string,
        vol.Optional("entry_id"): cv.string,
    }
)
SCHEMA_ISTANZA = vol.Schema({vol.Optional("entry_id"): cv.string})
WS_CARD_DATA = f"{DOMAIN}/card_data"
CARD_SENSOR_KEYS = ("media", "grades", "noticeboard", "notes", "scrutini", "agenda")


def leggi(dati: dict, chiave: str, default=None):
    """Legge un campo della configurazione ignorando maiuscole e minuscole.

    I nomi dei campi sono definiti da CONF_* in const.py e possono cambiare di
    forma ("username" -> "Username"): le configurazioni gia' salvate conservano
    pero' la vecchia scrittura, e senza questo passaggio andrebbero in KeyError.
    """
    if chiave in dati:
        return dati[chiave]
    voluta = chiave.lower()
    for nome, valore in dati.items():
        if nome.lower() == voluta:
            return valore
    return default


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Configura l'integrazione a partire da una config entry (UI)."""
    coordinator = CvvDashboardCoordinator(
        hass,
        leggi(entry.data, CONF_USERNAME),
        leggi(entry.data, CONF_PASSWORD),
        leggi(entry.data, CONF_ANNO),
    )
    # Primo refresh: se fallisce l'auth, HA mostra l'errore/avvia il reauth.
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    _registra_websocket(hass)
    await _registra_card(hass)

    # Registra una sola volta la vista per il download degli allegati.
    if not hass.data[DOMAIN].get("_download_view"):
        hass.http.register_view(CvvDashboardDownloadView(hass))
        hass.data[DOMAIN]["_download_view"] = True

    _registra_servizi(hass)

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def _registra_card(hass: HomeAssistant) -> None:
    """Serve il file JS della card e lo carica in ogni pagina del frontend."""
    if hass.data[DOMAIN].get("_card_registered"):
        return
    integrazione = await async_get_integration(hass, DOMAIN)
    cartella = Path(__file__).parent / "www"
    await hass.http.async_register_static_paths(
        [StaticPathConfig(CARD_URL_BASE, str(cartella), False)]
    )
    # Il parametro v cambia a ogni versione e aggira la cache del browser.
    add_extra_js_url(hass, f"{CARD_URL_BASE}/{CARD_FILE}?v={integrazione.version}")
    hass.data[DOMAIN]["_card_registered"] = True


def _coordinatori(hass: HomeAssistant) -> dict[str, CvvDashboardCoordinator]:
    """Le istanze configurate, escluse le chiavi di servizio interne."""
    return {
        k: v for k, v in hass.data.get(DOMAIN, {}).items()
        if isinstance(v, CvvDashboardCoordinator)
    }


@websocket_api.websocket_command(
    {
        vol.Required("type"): WS_CARD_DATA,
        vol.Required("entity_id"): cv.entity_id,
    }
)
@callback
def _ws_dati_card(hass: HomeAssistant, connection, msg: dict) -> None:
    """Return complete year data without storing it in sensor attributes."""
    entity = er.async_get(hass).async_get(msg["entity_id"])
    if (
        entity is None
        or entity.platform != DOMAIN
        or not entity.unique_id.startswith("cvv_grades_")
        or entity.config_entry_id is None
    ):
        connection.send_error(msg["id"], "entity_not_found", "Voti ClasseViva non trovati.")
        return

    if (
        not connection.user.is_admin
        and not connection.user.permissions.check_entity(entity.entity_id, POLICY_READ)
    ):
        raise Unauthorized(
            user_id=connection.user.id,
            entity_id=entity.entity_id,
            permission=POLICY_READ,
        )

    if not connection.user.is_admin:
        registry = er.async_get(hass)
        student_id = entity.unique_id.removeprefix("cvv_grades_")
        for key in CARD_SENSOR_KEYS:
            sensor_id = registry.async_get_entity_id(
                "sensor", DOMAIN, f"cvv_{key}_{student_id}"
            )
            sensor = registry.async_get(sensor_id) if sensor_id else None
            if sensor is None or sensor.config_entry_id != entity.config_entry_id:
                connection.send_error(
                    msg["id"], "entity_not_found", "Entita ClasseViva non trovata."
                )
                return
            if not connection.user.permissions.check_entity(sensor.entity_id, POLICY_READ):
                raise Unauthorized(
                    user_id=connection.user.id,
                    entity_id=sensor.entity_id,
                    permission=POLICY_READ,
                )

    coordinator = _coordinatori(hass).get(entity.config_entry_id)
    if coordinator is None or coordinator.data is None:
        connection.send_error(msg["id"], "entry_not_loaded", "Dati ClasseViva non disponibili.")
        return

    connection.send_result(msg["id"], card_data(coordinator, entity.config_entry_id))


def _registra_websocket(hass: HomeAssistant) -> None:
    """Register the card data command once for this Home Assistant instance."""
    if hass.data[DOMAIN].get("_websocket_registered"):
        return
    websocket_api.async_register_command(hass, _ws_dati_card)
    hass.data[DOMAIN]["_websocket_registered"] = True


def _registra_servizi(hass: HomeAssistant) -> None:
    """Registra i servizi dell'integrazione (una sola volta)."""
    if hass.services.has_service(DOMAIN, SERVIZIO_LEGGI):
        return

    def _scelte(call: ServiceCall) -> dict:
        """Istanze su cui agire: quella indicata, o tutte se non specificata."""
        istanze = _coordinatori(hass)
        entry_id = call.data.get("entry_id")
        if entry_id:
            scelte = {entry_id: istanze[entry_id]} if entry_id in istanze else {}
        else:
            scelte = istanze
        if not scelte:
            raise HomeAssistantError("Nessuna configurazione CVV Dashboard trovata.")
        return scelte

    async def leggi_comunicazione(call: ServiceCall) -> dict:
        """Scarica il testo di una comunicazione e la marca come letta.

        È l'equivalente di aprirla nell'app: il registro la segna come letta.
        Per questo l'aggiornamento automatico non lo fa da solo sulle non lette.
        """
        pub_id = str(call.data["pub_id"])

        for coordinator in _scelte(call).values():
            for c in (coordinator.data or {}).get("noticeboard", []):
                if str(c.get("pubId")) != pub_id:
                    continue
                testo = await coordinator.api.leggi_comunicazione(
                    c.get("evtCode"), c.get("pubId")
                )
                if testo is None:
                    raise HomeAssistantError(
                        f"Comunicazione {pub_id} non leggibile da ClasseViva."
                    )
                # Il testo viene messo nei dati in memoria ma NON si forza un
                # aggiornamento: rinfrescare qui farebbe sparire la comunicazione
                # dall'elenco "da leggere" nell'istante in cui la si apre, prima
                # di poterla leggere. Lo stato si allinea al prossimo giro o
                # premendo "Aggiorna".
                c["text"] = testo
                return {
                    "titolo": c.get("cntTitle"),
                    "data": (c.get("pubDT") or "")[:10],
                    "testo": testo,
                    "allegati": [a.get("fileName") for a in c.get("attachments", [])],
                }

        raise HomeAssistantError(f"Comunicazione {pub_id} non trovata in bacheca.")

    hass.services.async_register(
        DOMAIN,
        SERVIZIO_LEGGI,
        leggi_comunicazione,
        schema=SCHEMA_LEGGI,
        supports_response=SupportsResponse.OPTIONAL,
    )

    async def carica_testi_bacheca(call: ServiceCall) -> dict:
        """Scarica dal portale i testi mancanti SENZA segnare nulla come letto."""
        totale = 0
        for coordinator in _scelte(call).values():
            totale += await coordinator.async_testi_bacheca()
        return {"completate": totale}

    hass.services.async_register(
        DOMAIN,
        SERVIZIO_TESTI,
        carica_testi_bacheca,
        schema=SCHEMA_ISTANZA,
        supports_response=SupportsResponse.OPTIONAL,
    )

    async def aggiorna(call: ServiceCall) -> None:
        """Forza subito un aggiornamento, senza aspettare il ciclo periodico."""
        for coordinator in _scelte(call).values():
            await coordinator.async_request_refresh()

    hass.services.async_register(DOMAIN, SERVIZIO_AGGIORNA, aggiorna, schema=SCHEMA_ISTANZA)


async def async_migrate_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Aggiorna le configurazioni salvate da versioni precedenti."""
    if entry.version == 1:
        # La v2 aggiunge la scelta dell'anno scolastico: le vecchie configurazioni
        # seguono l'anno piu' recente, che e' il comportamento che avevano prima.
        # Le chiavi vengono anche riscritte nella forma attuale dei CONF_*.
        nuovi = {
            CONF_USERNAME: leggi(entry.data, CONF_USERNAME),
            CONF_PASSWORD: leggi(entry.data, CONF_PASSWORD),
            CONF_ANNO: leggi(entry.data, CONF_ANNO),
        }
        hass.config_entries.async_update_entry(entry, data=nuovi, version=2)
        _LOGGER.debug("Config entry %s migrata alla versione 2", entry.entry_id)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Rimuove l'integrazione."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
        if not _coordinatori(hass):
            for servizio in (SERVIZIO_LEGGI, SERVIZIO_TESTI, SERVIZIO_AGGIORNA):
                hass.services.async_remove(DOMAIN, servizio)
    return unload_ok
