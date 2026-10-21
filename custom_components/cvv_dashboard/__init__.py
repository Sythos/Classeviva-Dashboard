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

import asyncio
import logging
import time
from pathlib import Path

import voluptuous as vol

from homeassistant.auth.permissions.const import POLICY_READ
from homeassistant.components import frontend, panel_custom, websocket_api
from homeassistant.components.frontend import add_extra_js_url
from homeassistant.components.http import StaticPathConfig
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall, SupportsResponse
from homeassistant.exceptions import HomeAssistantError, Unauthorized
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers import entity_registry as er
from homeassistant.loader import async_get_integration

from .const import (
    CONF_ANNO,
    CONF_PASSWORD,
    CONF_SIDEBAR,
    CONF_USERNAME,
    DOMAIN,
    UPDATE_MINUTES,
)
from .coordinator import CvvDashboardCoordinator
from .download import CvvDashboardDownloadView
from .sensor import anno_effettivo, card_data

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["sensor", "calendar"]

# La card Lovelace viaggia dentro l'integrazione e viene servita da qui.
CARD_URL_BASE = "/cvv_dashboard_static"
CARD_FILE = "cvv-dashboard-card.js"

# Voce nel menu laterale, creata se almeno un'istanza ha l'opzione attiva.
PANEL_URL_PATH = "cvv-dashboard"
PANEL_ELEMENT = "cvv-dashboard-card-panel"

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
CARD_SENSOR_KEYS = ("media", "grades", "noticeboard", "notes", "scrutini", "agenda", "talks")

# Anni scelti al volo nella card: i dati restano in cache quanto un aggiornamento
# normale, e dopo un errore non si riprova prima di qualche minuto.
CACHE_ANNO_SECONDI = UPDATE_MINUTES * 60
ATTESA_DOPO_ERRORE = 300


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


CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Prepara il frontend all'avvio, prima di qualunque istanza e senza rete.

    La card deve essere nell'elenco degli script gia' quando il browser carica
    la prima pagina. Le istanze invece scaricano i dati dal registro, e possono
    metterci decine di secondi: se la card aspettasse loro, una pagina caricata
    nel frattempo non avrebbe lo script e mostrerebbe "Errore di configurazione".
    """
    await _prepara_frontend(hass)
    return True


async def _prepara_frontend(hass: HomeAssistant) -> None:
    """Registra card, comando WebSocket e vista di download, una volta sola."""
    hass.data.setdefault(DOMAIN, {})
    _registra_websocket(hass)
    await _registra_card(hass)
    if not hass.data[DOMAIN].get("_download_view"):
        hass.http.register_view(CvvDashboardDownloadView(hass))
        hass.data[DOMAIN]["_download_view"] = True


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
    # Gia' fatto da async_setup: qui non fa nulla, ma copre un avvio senza di esso.
    await _prepara_frontend(hass)
    # Le opzioni (voce nel menu laterale) si applicano senza ricaricare l'istanza.
    entry.async_on_unload(entry.add_update_listener(_opzioni_cambiate))
    await _aggiorna_pannello(hass)

    _registra_servizi(hass)

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def _opzioni_cambiate(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Applica la scelta della voce nel menu laterale quando cambiano le opzioni."""
    await _aggiorna_pannello(hass)


async def _aggiorna_pannello(hass: HomeAssistant, escludi: str | None = None) -> None:
    """Crea o toglie la voce nel menu laterale.

    La voce c'e' se almeno un'istanza (esclusa `escludi`, quella che si sta
    scaricando) ha l'opzione attiva. Se esiste gia' una pagina con lo stesso
    indirizzo, per esempio messa a mano in configuration.yaml, non la tocca.
    """
    desiderata = any(
        e.options.get(CONF_SIDEBAR, False)
        for e in hass.config_entries.async_entries(DOMAIN)
        if e.entry_id != escludi
    )
    dati = hass.data.setdefault(DOMAIN, {})
    presente = bool(dati.get("_pannello"))
    if desiderata and not presente:
        if PANEL_URL_PATH in (hass.data.get("frontend_panels") or {}):
            _LOGGER.warning(
                "La pagina %s esiste gia': la voce automatica nel menu laterale non viene creata",
                PANEL_URL_PATH,
            )
            return
        integrazione = await async_get_integration(hass, DOMAIN)
        await panel_custom.async_register_panel(
            hass,
            webcomponent_name=PANEL_ELEMENT,
            frontend_url_path=PANEL_URL_PATH,
            module_url=f"{CARD_URL_BASE}/{CARD_FILE}?v={integrazione.version}",
            sidebar_title="CVV Dashboard",
            sidebar_icon="mdi:school",
            require_admin=False,
            config={},
        )
        dati["_pannello"] = True
    elif not desiderata and presente:
        frontend.async_remove_panel(hass, PANEL_URL_PATH)
        dati["_pannello"] = False


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
        vol.Optional("anno"): vol.All(int, vol.Range(min=2000, max=2099)),
    }
)
@websocket_api.async_response
async def _ws_dati_card(hass: HomeAssistant, connection, msg: dict) -> None:
    """Return complete year data without storing it in sensor attributes.

    Con `anno` diverso da quello dell'istanza i dati dell'anno vengono scaricati
    al volo (e messi in cache) con la stessa sessione dell'istanza.
    """
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

    anno = msg.get("anno")
    if anno is None or anno == anno_effettivo(coordinator):
        connection.send_result(msg["id"], card_data(coordinator, entity.config_entry_id))
        return

    try:
        chiave, coordinatore_anno = await _coordinatore_anno(
            hass, entity.config_entry_id, coordinator, anno
        )
    except HomeAssistantError as err:
        connection.send_error(msg["id"], "anno_non_disponibile", str(err))
        return
    connection.send_result(msg["id"], card_data(coordinatore_anno, chiave))


async def _coordinatore_anno(
    hass: HomeAssistant,
    entry_id: str,
    base: CvvDashboardCoordinator,
    anno: int,
) -> tuple[str, CvvDashboardCoordinator]:
    """Coordinatore di un anno non configurato, con i dati aggiornati o in cache.

    Non fa login in piu': usa token, sessione del portale e blocco dell'istanza
    principale. Chiede solo anni che il portfolio elenca, mai anni inventati.
    """
    if anno not in base.api.anni_disponibili():
        raise HomeAssistantError("Anno scolastico non disponibile per questo account.")

    chiave = f"{entry_id}:{anno}"
    anni = hass.data[DOMAIN].setdefault("_anni", {})
    voce = anni.get(chiave)
    if voce is None:
        username, password = base.api.credenziali
        voce = anni[chiave] = {
            "coord": CvvDashboardCoordinator(
                hass, username, password, anno, condiviso=base
            ),
            "ts": None,
            "errore": None,
            "lock": asyncio.Lock(),
        }

    coordinatore = voce["coord"]
    async with voce["lock"]:
        adesso = time.monotonic()
        fresco = voce["ts"] is not None and adesso - voce["ts"] < CACHE_ANNO_SECONDI
        if not fresco:
            if (
                coordinatore.data is None
                and voce["errore"] is not None
                and adesso - voce["errore"] < ATTESA_DOPO_ERRORE
            ):
                raise HomeAssistantError(
                    "Dati dell'anno non disponibili. Riprova tra qualche minuto."
                )
            await coordinatore.async_refresh()
            if coordinatore.last_update_success:
                voce["ts"] = adesso
                voce["errore"] = None
            else:
                voce["errore"] = adesso
                if coordinatore.data is None:
                    raise HomeAssistantError("Dati dell'anno non disponibili.")
    return chiave, coordinatore


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
                # di poterla leggere. Il portale la segna come letta: lo stesso
                # stato va in memoria e ai sensori, senza nuova richiesta. La card
                # tiene visibile la comunicazione aperta finche' non si cambia vista.
                c["text"] = testo
                c["readStatus"] = True
                coordinator.async_set_updated_data(coordinator.data)
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
        anni = hass.data[DOMAIN].get("_anni", {})
        for chiave in [k for k in anni if k.startswith(f"{entry.entry_id}:")]:
            anni.pop(chiave, None)
        if not _coordinatori(hass):
            for servizio in (SERVIZIO_LEGGI, SERVIZIO_TESTI, SERVIZIO_AGGIORNA):
                hass.services.async_remove(DOMAIN, servizio)
        await _aggiorna_pannello(hass, escludi=entry.entry_id)
    return unload_ok
