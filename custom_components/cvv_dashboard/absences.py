# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Sythos <sythos@gmail.com>
# Author: Sythos <sythos@gmail.com>
"""Assenze, ritardi e uscite: normalizzazione e ordine, senza dipendenze di rete."""
from __future__ import annotations

# I codici sono quelli dei client pubblici e non sono confermati sul registro reale.
_TIPI = {"ABA0": "assenza", "ABR0": "ritardo", "ABU0": "uscita"}


def _data_iso(valore) -> str:
    testo = str(valore or "")[:10]
    if len(testo) == 8 and testo.isdigit():
        return f"{testo[:4]}-{testo[4:6]}-{testo[6:]}"
    return testo


def normalizza(body) -> list[dict]:
    """Porta gli eventi a un elenco uniforme, senza fermarsi sui campi mancanti."""
    if isinstance(body, dict):
        eventi = body.get("events")
        if eventi is None:
            eventi = body.get("absences")
    else:
        eventi = body
    if not isinstance(eventi, list):
        return []
    out = []
    for e in eventi:
        if not isinstance(e, dict):
            continue
        codice = str(e.get("evtCode") or "")
        ora = e.get("evtHPos")
        if ora in (None, ""):
            valore = e.get("evtValue")
            ora = valore if isinstance(valore, str) and ":" in valore else ""
        out.append(
            {
                "data": _data_iso(e.get("evtDate")),
                "ora": ora,
                "tipo": _TIPI.get(codice.upper(), "altro"),
                "giustificata": bool(e.get("isJustified")),
                "motivo": str(e.get("justifReasonDesc") or ""),
                "codice": codice,
            }
        )
    return out


def ora_ordine(ora) -> int:
    """Chiave numerica dell'ora di un evento: vuota o non numerica vale 0."""
    try:
        return int(str(ora).split(":")[0])
    except (TypeError, ValueError):
        return 0


def ordina(voci: list[dict]) -> list[dict]:
    """Prima il piu' recente: per la stessa data, l'ora piu' alta."""
    return sorted(
        voci,
        key=lambda v: (str(v.get("data") or ""), ora_ordine(v.get("ora"))),
        reverse=True,
    )
