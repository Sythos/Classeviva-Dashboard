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
lascia vuoto cio' che non trova. I nomi si confrontano senza distinguere
maiuscole e minuscole. La risposta degli slot puo' essere annidata
(docente -> frames -> orari liberi): `unisci` la espande. Se la risposta ha dati
che il parser non riconosce, `unisci` solleva `RispostaNonRiconosciuta`.
Da verificare con una sessione reale.
"""
from __future__ import annotations

import re
from datetime import date, timedelta

# oggi piu' 27 giorni: 28 giorni di calendario in tutto
GIORNI_AVANTI = 27

STATO_DISPONIBILE = "disponibile"
STATO_PRENOTATO = "prenotato"


class RispostaNonRiconosciuta(ValueError):
    """La risposta ha dati, ma il parser non ne ricava nessun colloquio."""


# Nomi candidati dei campi (non confermati)
_CHIAVI_DATA = ("data", "date", "day", "start", "begin", "dateTime", "datetime", "frameDate")
_CHIAVI_INIZIO = (
    "ora_inizio", "startTime", "timeStart", "from", "start", "begin", "hourStart",
    "frameTimeFrom", "timeFrom",
)
_CHIAVI_FINE = ("ora_fine", "endTime", "timeEnd", "to", "end", "hourEnd", "frameTimeTo", "timeTo")
_CHIAVI_DOCENTE = ("docente", "teacherName", "teacher", "teacherDesc", "name")
_CHIAVI_MATERIA = ("materia", "subjects", "subject", "subjectDesc")
_CHIAVI_AULA = ("aula", "room", "place", "location", "framePlace")
_CHIAVI_ORARI_LIBERI = ("freeSlotTimeRange", "freeSlots")
_CHIAVI_LINK = ("link", "url", "meetingUrl", "meetingLink", "remoteUrl")
_CHIAVI_NOTE = ("note", "notes", "description", "desc", "message")
_CHIAVI_MODO = ("modalita", "mode", "type", "talkType", "remote")
_CHIAVI_ID = ("id", "frameId", "talkId", "slotId")
_CHIAVI_DOCENTE_ID = ("teacherId", "docente_id", "idTeacher")
_CHIAVI_PRENOTATO = ("prenotato", "booked", "isBooked", "reserved", "taken")
_LISTE_SLOT = ("teacher", "teachers", "frames", "slots", "items")
_LISTE_PRENOTATI = ("talks", "mytalks", "items", "bookings")


def intervallo(oggi: date) -> tuple[date, date]:
    """Primo e ultimo giorno mostrati: oggi e i 27 giorni dopo."""
    return oggi, oggi + timedelta(days=GIORNI_AVANTI)


def formato_richiesta(giorno: date) -> str:
    """Data nel formato AAAAMMGG usato nel percorso della richiesta."""
    return giorno.strftime("%Y%m%d")


def _prima(voce: dict, chiavi: tuple[str, ...]):
    minuscole = {str(k).lower(): v for k, v in voce.items()}
    for chiave in chiavi:
        valore = minuscole.get(chiave.lower())
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


def _materia(valore) -> str:
    """Materie come testo unico: accetta un testo o un elenco di testi e oggetti."""
    if not isinstance(valore, list):
        valore = [valore]
    nomi = []
    for v in valore:
        if isinstance(v, dict):
            v = _prima(v, ("subjectDesc", "description", "desc", "name", "materia"))
        nome = _testo(v)
        if nome and nome not in nomi:
            nomi.append(nome)
    return ", ".join(nomi)


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
        "materia": _materia(_prima(voce, _CHIAVI_MATERIA)),
        "stato": stato or (STATO_PRENOTATO if prenotato else STATO_DISPONIBILE),
        "modalita": modo,
        "aula": _testo(_prima(voce, _CHIAVI_AULA)),
        "link": _testo(_prima(voce, _CHIAVI_LINK)),
        "note": _testo(_prima(voce, _CHIAVI_NOTE)),
    }


def _elenco(corpo, chiavi: tuple[str, ...]) -> list:
    """Voci di una risposta: l'elenco principale o gli elenchi sotto le chiavi note.

    Solleva `RispostaNonRiconosciuta` se la risposta ha contenuto ma nessuna chiave nota.
    """
    if corpo in (None, "", [], {}):
        return []
    if isinstance(corpo, list):
        return corpo
    if isinstance(corpo, dict):
        minuscole = {str(k).lower(): v for k, v in corpo.items()}
        trovate = [minuscole[c.lower()] for c in chiavi if isinstance(minuscole.get(c.lower()), list)]
        if trovate:
            return [voce for elenco in trovate for voce in elenco]
    raise RispostaNonRiconosciuta("nessun elenco noto nella risposta")


def _orari(voce: dict) -> list[dict]:
    """Un frame con orari liberi diventa una voce per ogni orario libero."""
    liberi = _prima(voce, _CHIAVI_ORARI_LIBERI)
    if not isinstance(liberi, list):
        liberi = [liberi] if liberi else []
    risultato = []
    for libero in liberi:
        if isinstance(libero, dict):
            ora_inizio = _ora(_prima(libero, _CHIAVI_INIZIO))
            ora_fine = _ora(_prima(libero, _CHIAVI_FINE))
        else:
            ore = re.findall(r"\d{1,2}[:.]\d{2}", _testo(libero))
            ora_inizio = _ora(ore[0]) if ore else ""
            ora_fine = _ora(ore[1]) if len(ore) > 1 else ""
        if ora_inizio:
            # senza id: l'id del frame vale per tutto il gruppo di orari
            copia = {k: v for k, v in voce.items() if str(k).lower() not in ("id", "frameid")}
            copia["ora_inizio"] = ora_inizio
            copia["ora_fine"] = ora_fine
            risultato.append(copia)
    return risultato or [voce]


def _appiattisci(voci: list) -> list:
    """Espande docente -> frames -> orari liberi in voci piatte, con docente e materia."""
    piatte = []
    for voce in voci:
        if not isinstance(voce, dict):
            piatte.append(voce)
            continue
        frames = {str(k).lower(): v for k, v in voce.items()}.get("frames")
        if not isinstance(frames, list):
            piatte.extend(_orari(voce))
            continue
        for frame in frames:
            if not isinstance(frame, dict):
                piatte.append(frame)
                continue
            unita = dict(frame)
            for chiave in _CHIAVI_DOCENTE + _CHIAVI_MATERIA + _CHIAVI_DOCENTE_ID:
                valore = _prima(voce, (chiave,))
                if valore is not None and _prima(frame, (chiave,)) is None:
                    unita[chiave] = valore
            piatte.extend(_orari(unita))
    return piatte


def _leggi(voci: list, stato: str | None = None) -> list[dict]:
    candidate = _appiattisci(voci)
    lette = [v for v in (normalizza(c, stato) for c in candidate) if v]
    if candidate and not lette:
        raise RispostaNonRiconosciuta("voci senza data riconosciuta")
    return lette


def unisci(corpo_slot, corpo_prenotati) -> list[dict]:
    """Un solo elenco con gli slot liberi e quelli prenotati, senza doppioni.

    Solleva `RispostaNonRiconosciuta` se una risposta ha dati che non si leggono.
    """
    voci = _leggi(_elenco(corpo_slot, _LISTE_SLOT))
    prenotati = _elenco(corpo_prenotati, _LISTE_PRENOTATI)
    if isinstance(corpo_slot, dict):
        # la risposta degli slot puo' avere anche i colloqui prenotati
        extra = {str(k).lower(): v for k, v in corpo_slot.items()}.get("talks")
        if isinstance(extra, list):
            prenotati = prenotati + extra

    for prenotata in _leggi(prenotati, STATO_PRENOTATO):
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
