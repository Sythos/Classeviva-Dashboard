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

"""Controllo del permesso di lettura dell'utente su un'istanza (uno studente)."""
from __future__ import annotations

from homeassistant.auth.permissions.const import POLICY_READ
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

from .const import DOMAIN


def id_istanza(chiave: str | None) -> str | None:
    """Toglie l'anno da una chiave "<entry_id>:<anno>"."""
    if not chiave:
        return None
    return str(chiave).split(":", 1)[0]


def puo_leggere(hass: HomeAssistant, user, entry_id: str | None) -> bool:
    """True se l'utente puo' leggere tutte le entita' sensore dell'istanza.

    Gli admin passano sempre. Un utente assente o un'istanza senza entita'
    sono negati: l'entry_id da solo non e' mai un permesso.
    """
    if user is None or not entry_id:
        return False
    if user.is_admin:
        return True
    entita = [
        e
        for e in er.async_entries_for_config_entry(er.async_get(hass), entry_id)
        if e.platform == DOMAIN and e.domain == "sensor"
    ]
    if not entita:
        return False
    return all(user.permissions.check_entity(e.entity_id, POLICY_READ) for e in entita)
