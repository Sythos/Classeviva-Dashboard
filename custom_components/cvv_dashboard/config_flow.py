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

"""Config flow (interfaccia grafica) per ClasseViva."""
from __future__ import annotations

from datetime import date

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import device_registry as dr, entity_registry as er
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.selector import (
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
    TextSelector,
    TextSelectorConfig,
    TextSelectorType,
)

from .api import CvvDashboardApi, CvvDashboardAuthError, CvvDashboardApiError, parse_anno
from .const import ANNO_ULTIMO, CONF_ANNO, CONF_PASSWORD, CONF_USERNAME, DOMAIN

# Quanti anni scolastici passati proporre nella tendina.
ANNI_PROPOSTI = 5


def _anni_disponibili() -> list[str]:
    """Elenco per la tendina: "ultimo" e gli ultimi anni scolastici.

    L'anno scolastico che inizia a settembre: prima di settembre l'anno "in
    corso" è ancora quello iniziato l'anno solare precedente.
    """
    oggi = date.today()
    inizio = oggi.year if oggi.month >= 9 else oggi.year - 1
    return [ANNO_ULTIMO] + [
        f"{a % 100:02d}/{(a + 1) % 100:02d}"
        for a in range(inizio, inizio - ANNI_PROPOSTI, -1)
    ]


def _schema(valori: dict | None = None) -> vol.Schema:
    valori = valori or {}
    return vol.Schema(
        {
            vol.Required(CONF_USERNAME, default=valori.get(CONF_USERNAME, "")): TextSelector(),
            vol.Required(CONF_PASSWORD, default=""): TextSelector(
                TextSelectorConfig(type=TextSelectorType.PASSWORD)
            ),
            # custom_value: oltre alle voci proposte si può scrivere l'anno a mano
            # ("25", "25/26", "2025/2026" vanno tutti bene).
            vol.Optional(CONF_ANNO, default=valori.get(CONF_ANNO, ANNO_ULTIMO)): SelectSelector(
                SelectSelectorConfig(
                    options=_anni_disponibili(),
                    custom_value=True,
                    mode=SelectSelectorMode.DROPDOWN,
                )
            ),
        }
    )


def _radice(student_id, anno: int | None) -> str:
    """Radice degli unique_id di un'istanza: lo studente, piu' l'anno se e' fissato.

    Deve restare uguale a CvvDashboardCoordinator.id_unico e all'unique_id
    che la configurazione guidata assegna alla config entry.
    """
    return f"{student_id}_{anno}" if anno is not None else str(student_id)


def _etichetta_anno(anno: int | None) -> str:
    return f"{anno % 100:02d}/{(anno + 1) % 100:02d}" if anno is not None else ANNO_ULTIMO


def _studente_della_entry(entry) -> str:
    """Identificativo dello studente, preso dall'unique_id della config entry."""
    return str(entry.unique_id or "").split("_")[0]


async def _prova_login(hass: HomeAssistant, username, password, anno: int | None):
    """Prova il login. Ritorna (api, None) se riesce, (None, codice_errore) se no."""
    api = CvvDashboardApi(async_get_clientsession(hass), username, password, anno)
    try:
        await api.login()
    except CvvDashboardAuthError:
        return None, "invalid_auth"
    except CvvDashboardApiError:
        return None, "cannot_connect"
    return api, None


def _sposta_registri(hass: HomeAssistant, entry, vecchia: str, nuova: str) -> None:
    """Porta entita' e dispositivo dell'istanza dal vecchio anno al nuovo.

    Gli unique_id e l'identificativo del dispositivo contengono l'anno: senza
    questo passaggio, cambiare anno creerebbe entita' nuove e lascerebbe quelle
    vecchie orfane, con gli id di dashboard e automazioni che cambiano.
    """
    registro_entita = er.async_get(hass)
    suffisso = f"_{vecchia}"
    for entita in er.async_entries_for_config_entry(registro_entita, entry.entry_id):
        if entita.unique_id.endswith(suffisso):
            registro_entita.async_update_entity(
                entita.entity_id,
                new_unique_id=entita.unique_id[: -len(vecchia)] + nuova,
            )
    registro_dispositivi = dr.async_get(hass)
    for dispositivo in dr.async_entries_for_config_entry(registro_dispositivi, entry.entry_id):
        if (DOMAIN, vecchia) in dispositivo.identifiers:
            identificativi = (set(dispositivo.identifiers) - {(DOMAIN, vecchia)}) | {(DOMAIN, nuova)}
            registro_dispositivi.async_update_device(
                dispositivo.id, new_identifiers=identificativi
            )


class CvvDashboardConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Setup guidato: chiede credenziali e anno scolastico, poi verifica il login."""

    VERSION = 2

    async def async_step_user(self, user_input=None):
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                anno = parse_anno(user_input.get(CONF_ANNO))
            except ValueError:
                errors[CONF_ANNO] = "anno_non_valido"
            else:
                api = CvvDashboardApi(
                    async_get_clientsession(self.hass),
                    user_input[CONF_USERNAME],
                    user_input[CONF_PASSWORD],
                    anno,
                )
                try:
                    await api.login()
                except CvvDashboardAuthError:
                    errors["base"] = "invalid_auth"
                except CvvDashboardApiError:
                    errors["base"] = "cannot_connect"
                else:
                    # Lo stesso studente può essere aggiunto più volte, purché su
                    # anni scolastici diversi: l'anno entra quindi nell'unique_id.
                    unico = api.student_id
                    if anno is not None:
                        unico = f"{unico}_{anno}"
                    await self.async_set_unique_id(unico)
                    self._abort_if_unique_id_configured()

                    etichetta = (
                        f" {anno % 100:02d}/{(anno + 1) % 100:02d}"
                        if anno is not None else ""
                    )
                    return self.async_create_entry(
                        title=f"CVV Dashboard - {api.first_name}{etichetta}",
                        data={
                            CONF_USERNAME: user_input[CONF_USERNAME],
                            CONF_PASSWORD: user_input[CONF_PASSWORD],
                            CONF_ANNO: anno,
                        },
                    )

        return self.async_show_form(
            step_id="user", data_schema=_schema(user_input), errors=errors
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Schermata Opzioni: cambio di password e anno senza ricreare l'istanza."""
        return CvvDashboardOptionsFlow(config_entry.entry_id)

    async def async_step_reauth(self, entry_data):
        """Home Assistant la avvia quando il registro rifiuta le credenziali."""
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(self, user_input=None):
        """Chiede la password nuova e verifica che sia dello stesso studente."""
        entry = self.hass.config_entries.async_get_entry(self.context["entry_id"])
        errors: dict[str, str] = {}

        if user_input is not None:
            anno = entry.data.get(CONF_ANNO)
            api, errore = await _prova_login(
                self.hass, entry.data[CONF_USERNAME], user_input[CONF_PASSWORD], anno
            )
            if errore:
                errors["base"] = errore
            elif str(api.student_id) != _studente_della_entry(entry):
                errors["base"] = "wrong_account"
            else:
                return self.async_update_reload_and_abort(
                    entry,
                    data={**entry.data, CONF_PASSWORD: user_input[CONF_PASSWORD]},
                    reason="reauth_successful",
                )

        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_PASSWORD, default=""): TextSelector(
                        TextSelectorConfig(type=TextSelectorType.PASSWORD)
                    )
                }
            ),
            description_placeholders={"username": entry.data[CONF_USERNAME]},
            errors=errors,
        )


class CvvDashboardOptionsFlow(config_entries.OptionsFlow):
    """Cambio di password e anno scolastico di un'istanza gia' configurata."""

    def __init__(self, entry_id: str) -> None:
        self._entry_id = entry_id

    async def async_step_init(self, user_input=None):
        entry = self.hass.config_entries.async_get_entry(self._entry_id)
        errors: dict[str, str] = {}
        anno_attuale = entry.data.get(CONF_ANNO)

        if user_input is not None:
            try:
                anno = parse_anno(user_input.get(CONF_ANNO))
            except ValueError:
                errors[CONF_ANNO] = "anno_non_valido"
            else:
                password = user_input.get(CONF_PASSWORD) or entry.data[CONF_PASSWORD]
                if password == entry.data[CONF_PASSWORD] and anno == anno_attuale:
                    return self.async_create_entry(data={})

                studente = _studente_della_entry(entry)
                nuova = _radice(studente, anno)
                altre = self.hass.config_entries.async_entries(DOMAIN)
                if any(e.entry_id != entry.entry_id and e.unique_id == nuova for e in altre):
                    errors[CONF_ANNO] = "already_configured"
                else:
                    api, errore = await _prova_login(
                        self.hass, entry.data[CONF_USERNAME], password, anno
                    )
                    if errore:
                        errors["base"] = errore
                    elif str(api.student_id) != studente:
                        errors["base"] = "wrong_account"
                    else:
                        if anno != anno_attuale:
                            _sposta_registri(
                                self.hass, entry, _radice(studente, anno_attuale), nuova
                            )
                        self.hass.config_entries.async_update_entry(
                            entry,
                            data={**entry.data, CONF_PASSWORD: password, CONF_ANNO: anno},
                            unique_id=nuova,
                            title=(
                                f"CVV Dashboard - {api.first_name}"
                                + (f" {_etichetta_anno(anno)}" if anno is not None else "")
                            ),
                        )
                        self.hass.async_create_task(
                            self.hass.config_entries.async_reload(entry.entry_id)
                        )
                        return self.async_create_entry(data={})

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Optional(CONF_PASSWORD, default=""): TextSelector(
                        TextSelectorConfig(type=TextSelectorType.PASSWORD)
                    ),
                    vol.Optional(
                        CONF_ANNO, default=_etichetta_anno(anno_attuale)
                    ): SelectSelector(
                        SelectSelectorConfig(
                            options=_anni_disponibili(),
                            custom_value=True,
                            mode=SelectSelectorMode.DROPDOWN,
                        )
                    ),
                }
            ),
            description_placeholders={"username": entry.data[CONF_USERNAME]},
            errors=errors,
        )
