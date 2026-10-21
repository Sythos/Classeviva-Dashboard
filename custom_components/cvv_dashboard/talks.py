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

"""Colloqui con i docenti: intervallo di date, unione e ordinamento degli slot.

Solo funzioni pure, senza Home Assistant, cosi' si provano da sole.

ATTENZIONE: i nomi dei campi della risposta del registro NON sono confermati su
una risposta reale. `normalizza` accetta piu' nomi possibili per ogni campo e
lascia vuoto cio' che non trova. Da verificare con una sessione reale.
"""
from __future__ import annotations

import re
from datetime import date, timedelta

# oggi piu' 27 giorni: 28 giorni di calendario in tutto
GIORNI_AVANTI = 27

STATO_DISPONIBILE = "disponibile"
STATO_PRENOTATO = "prenotato"

# Nomi candidati dei campi (non confermati)
_CHIAVI_DATA = ("data", "date", "day", "start", "begin", "dateTime", "datetime")
_CHIAVI_INIZIO = ("ora_inizio", "startTime", "timeStart", "from", "start", "begin", "hourStart")
_CHIAVI_FINE = ("ora_fine", "endTime", "timeEnd", "to", "end", "hourEnd")
_CHIAVI_DOCENTE = ("docente", "teacherName", "teacher", "teacherDesc", "name")
_CHIAVI_AULA = ("aula", "room", "place", "location")
_CHIAVI_LINK = ("link", "url", "meetingUrl", "meetingLink", "remoteUrl")
_CHIAVI_NOTE = ("note", "notes", "description", "desc", "message")
_CHIAVI_MODO = ("modalita", "mode", "type", "talkType", "remote")
_CHIAVI_ID = ("id", "frameId", "talkId", "slotId")
_CHIAVI_DOCENTE_ID = ("teacherId", "docente_id", "idTeacher")
_CHIAVI_PRENOTATO = ("prenotato", "booked", "isBooked", "reserved", "taken")
_LISTE_SLOT = ("frames", "slots", "items", "teachers", "talks")
_LISTE_PRENOTATI = ("talks", "mytalks", "items", "bookings")


def intervallo(oggi: date) -> tuple[date, date]:
    """Primo e ultimo giorno mostrati: oggi e i 27 giorni dopo."""
    return oggi, oggi + timedelta(days=GIORNI_AVANTI)


def formato_richiesta(giorno: date) -> str:
    """Data nel formato AAAAMMGG usato nel percorso della richiesta."""
    return giorno.strftime("%Y%m%d")


def _prima(voce: dict, chiavi: tuple[str, ...]):
    for chiave in chiavi:
        valore = voce.get(chiave)
        if valore not in (None, "", [], {}):
            return valore
    return None


def _testo(valore) -> str:
    if valore is None or isinstance(valore, (dict, list, bool)):
        return ""
    return str(valore).strip()


def _data_ora(valore) -> tuple[str, str]:
    """Da un testo data/ora ricava (AAAA-MM-GG, HH:MM); vuoto se non riconosce."""
    testo = _testo(valore)
    m = re.match(r"^(\d{4})-?(\d{2})-?(\d{2})(?:[T ](\d{2}):(\d{2}))?", testo)
    if m:
        try:
            iso = date(int(m.group(1)), int(m.group(2)), int(m.group(3))).isoformat()
        except ValueError:
            return "", ""
        ora = f"{m.group(4)}:{m.group(5)}" if m.group(4) else ""
        return iso, ora
    return "", ""


def _ora(valore) -> str:
    testo = _testo(valore)
    m = re.search(r"(\d{1,2})[:.](\d{2})", testo)
    if m:
        return f"{int(m.group(1)):02d}:{m.group(2)}"
    return ""


def normalizza(voce, stato: str | None = None) -> dict | None:
    """Porta una voce del registro nello schema dell'integrazione."""
    if not isinstance(voce, dict):
        return None
    iso, ora_data = _data_ora(_prima(voce, _CHIAVI_DATA))
    inizio = _ora(_prima(voce, _CHIAVI_INIZIO)) or ora_data
    if not iso:
        return None
    modo_grezzo = _prima(voce, _CHIAVI_MODO)
    modo = ""
    if modo_grezzo is True or str(modo_grezzo).lower() in ("remote", "remoto", "distance", "a distanza"):
        modo = "distanza"
    elif modo_grezzo is False or str(modo_grezzo).lower() in ("presence", "presenza", "in presenza", "local"):
        modo = "presenza"
    prenotato = bool(_prima(voce, _CHIAVI_PRENOTATO))
    return {
        "id": _testo(_prima(voce, _CHIAVI_ID)),
        "docente_id": _testo(_prima(voce, _CHIAVI_DOCENTE_ID)),
        "data": iso,
        "ora_inizio": inizio,
        "ora_fine": _ora(_prima(voce, _CHIAVI_FINE)),
        "docente": _testo(_prima(voce, _CHIAVI_DOCENTE)),
        "stato": stato or (STATO_PRENOTATO if prenotato else STATO_DISPONIBILE),
        "modalita": modo,
        "aula": _testo(_prima(voce, _CHIAVI_AULA)),
        "link": _testo(_prima(voce, _CHIAVI_LINK)),
        "note": _testo(_prima(voce, _CHIAVI_NOTE)),
    }


def _elenco(corpo, chiavi: tuple[str, ...]) -> list:
    if isinstance(corpo, list):
        return corpo
    if isinstance(corpo, dict):
        for chiave in chiavi:
            if isinstance(corpo.get(chiave), list):
                return corpo[chiave]
    return []


def unisci(corpo_slot, corpo_prenotati) -> list[dict]:
    """Un solo elenco con gli slot liberi e quelli prenotati, senza doppioni."""
    voci: list[dict] = []
    for grezza in _elenco(corpo_slot, _LISTE_SLOT):
        voce = normalizza(grezza)
        if voce:
            voci.append(voce)

    for grezza in _elenco(corpo_prenotati, _LISTE_PRENOTATI):
        prenotata = normalizza(grezza, STATO_PRENOTATO)
        if not prenotata:
            continue
        for i, voce in enumerate(voci):
            stessa_id = prenotata["id"] and voce["id"] == prenotata["id"]
            stesso_posto = (
                voce["data"] == prenotata["data"]
                and voce["ora_inizio"] == prenotata["ora_inizio"]
                and voce["docente"] == prenotata["docente"]
            )
            if stessa_id or stesso_posto:
                # il dettaglio della prenotazione vale piu' dello slot generico
                voci[i] = {
                    **voce,
                    **{k: v for k, v in prenotata.items() if v},
                    "stato": STATO_PRENOTATO,
                }
                break
        else:
            voci.append(prenotata)
    return voci


def filtra_ordina(voci: list[dict], oggi: date) -> list[dict]:
    """Tiene solo gli slot dell'intervallo e li ordina per data e ora, crescenti."""
    primo, ultimo = intervallo(oggi)
    prima, dopo = primo.isoformat(), ultimo.isoformat()
    dentro = [v for v in voci or [] if prima <= (v.get("data") or "") <= dopo]
    return sorted(dentro, key=lambda v: (v.get("data") or "", v.get("ora_inizio") or ""))
