# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Sythos <sythos@gmail.com>
# Author: Sythos <sythos@gmail.com>

"""Normalize read-only homework data from ClasseViva."""
from __future__ import annotations

from datetime import time

TIPO_COMPITI = "compiti"


def _date(value) -> str | None:
    if not isinstance(value, str):
        return None
    value = value.strip()
    if len(value) < 10:
        return None
    return value[:10]


def _time(value) -> str | None:
    if not isinstance(value, str):
        return None
    try:
        return time.fromisoformat(value.strip()).isoformat(timespec="seconds")
    except ValueError:
        return None


def normalizza(
    compiti: list[dict] | None,
    agenda: list[dict] | None = None,
) -> list[dict]:
    """Return homework events and keep agenda homework that has no match."""
    eventi: list[dict] = []
    identificativi: set[str] = set()

    for voce in compiti or []:
        if not isinstance(voce, dict):
            continue
        identificativo = voce.get("evtId") or voce.get("homeworkId")
        chiave = str(identificativo) if identificativo is not None else ""
        if chiave and chiave in identificativi:
            continue
        scadenza = _date(
            voce.get("expiryDate")
            or voce.get("evtDatetimeBegin")
            or voce.get("assignmentDate")
        )
        if not scadenza:
            continue

        ora = _time(voce.get("expiryTime"))
        if not ora and isinstance(voce.get("evtDatetimeBegin"), str):
            inizio = voce["evtDatetimeBegin"]
            ora = _time(inizio.split("T", 1)[1]) if "T" in inizio else None
        inizio_compito = f"{scadenza}T{ora}" if ora else scadenza
        eventi.append(
            {
                "evtId": identificativo,
                "homeworkId": identificativo,
                "evtCode": "AGHW",
                "evtDatetimeBegin": inizio_compito,
                "evtDatetimeEnd": inizio_compito,
                "isFullDay": not bool(ora),
                "subjectDesc": voce.get("subjectDesc") or "",
                "notes": voce.get("homeworkDesc") or voce.get("notes") or "",
                "authorName": voce.get("teacherName") or voce.get("authorName") or "",
                "tipo": TIPO_COMPITI,
                "assignmentDate": _date(voce.get("assignmentDate")),
                "homeworkDone": voce.get("homeworkDone"),
            }
        )
        if chiave:
            identificativi.add(chiave)

    for voce in agenda or []:
        if not isinstance(voce, dict):
            continue
        tipo = str(voce.get("tipo") or "").lower()
        if tipo != TIPO_COMPITI and voce.get("evtCode") != "AGHW":
            continue

        identificativo = voce.get("homeworkId") or voce.get("evtId")
        chiave = str(identificativo) if identificativo is not None else ""
        if chiave and chiave in identificativi:
            continue

        inizio = voce.get("evtDatetimeBegin") or voce.get("evtDate")
        if not _date(inizio):
            continue
        evento = dict(voce)
        evento.update(
            {
                "evtDatetimeBegin": inizio,
                "evtDatetimeEnd": voce.get("evtDatetimeEnd") or inizio,
                "isFullDay": bool(voce.get("isFullDay", True)),
                "evtCode": "AGHW",
                "homeworkId": identificativo,
                "tipo": TIPO_COMPITI,
            }
        )
        eventi.append(evento)
        if chiave:
            identificativi.add(chiave)

    return sorted(
        eventi,
        key=lambda item: item.get("evtDatetimeBegin") or "",
    )


def per_card(eventi: list[dict]) -> list[dict]:
    """Build the compact fields used by the Lovelace homework view."""
    return [
        {
            "inizio": evento.get("evtDatetimeBegin"),
            "fine": evento.get("evtDatetimeEnd"),
            "materia": evento.get("subjectDesc"),
            "note": evento.get("notes") or "",
            "autore": evento.get("authorName") or "",
            "tipo": "Compiti",
            "pubblicato": evento.get("assignmentDate"),
            "completato": evento.get("homeworkDone"),
        }
        for evento in eventi
    ]
