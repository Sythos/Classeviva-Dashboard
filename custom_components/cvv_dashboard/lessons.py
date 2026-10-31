# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Sythos <sythos@gmail.com>
# Author: Sythos <sythos@gmail.com>
"""Lezioni (argomenti svolti): normalizzazione e ordine, senza dipendenze di rete."""
from __future__ import annotations

from datetime import date, timedelta

# Giorni letti all'indietro, oggi compreso: l'ultima settimana.
GIORNI_INDIETRO = 6


def intervallo(oggi: date) -> tuple[date, date]:
    """Primo e ultimo giorno letti: gli ultimi 6 giorni e oggi."""
    return oggi - timedelta(days=GIORNI_INDIETRO), oggi


def _data_iso(valore) -> str:
    testo = str(valore or "")[:10]
    if len(testo) == 8 and testo.isdigit():
        return f"{testo[:4]}-{testo[4:6]}-{testo[6:]}"
    return testo


def _testo(valore) -> str:
    return " ".join(str(valore or "").split())


def normalizza(body) -> list[dict]:
    """Porta le lezioni a un elenco uniforme, senza fermarsi sui campi mancanti."""
    if isinstance(body, dict):
        lezioni = body.get("lessons")
    else:
        lezioni = body
    if not isinstance(lezioni, list):
        return []
    out = []
    for e in lezioni:
        if not isinstance(e, dict):
            continue
        ora = e.get("evtHPos")
        durata = e.get("evtDuration")
        out.append(
            {
                "data": _data_iso(e.get("evtDate")),
                "ora": ora if isinstance(ora, int) else _testo(ora),
                "durata": durata if isinstance(durata, int) else _testo(durata),
                "materia": _testo(e.get("subjectDesc")),
                "tipo": _testo(e.get("lessonType")),
                "docente": _testo(e.get("authorName")),
                "argomento": _testo(e.get("lessonArg")),
            }
        )
    return out


def ora_ordine(ora) -> int:
    """Chiave numerica dell'ora di una lezione: vuota o non numerica vale 0."""
    try:
        return int(str(ora).split(":")[0])
    except (TypeError, ValueError):
        return 0


def ordina(voci: list[dict]) -> list[dict]:
    """Prima la piu' recente: per la stessa data, l'ora piu' alta."""
    return sorted(
        voci,
        key=lambda v: (str(v.get("data") or ""), ora_ordine(v.get("ora"))),
        reverse=True,
    )
