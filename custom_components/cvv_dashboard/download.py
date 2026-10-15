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

"""Vista HTTP che permette di scaricare gli allegati di ClasseViva dal browser.

Gli allegati (bacheca, file dei docenti) richiedono il token Z-Auth-Token, quindi
un semplice <a href> non funzionerebbe. Questa vista, protetta dall'auth di Home
Assistant, chiede a Spaggiari l'URL reale (cdndoc, con token AUTH in query) e ci
reindirizza il browser. Le URL firmate vengono generate nei sensori.
"""
from __future__ import annotations

import logging
import re

from aiohttp import web

from homeassistant.components.http import HomeAssistantView
from homeassistant.core import HomeAssistant

from .const import BASE_HOST, DOMAIN

_LOGGER = logging.getLogger(__name__)

DOWNLOAD_URL = "/api/cvv_dashboard/download"


class CvvDashboardDownloadView(HomeAssistantView):
    """Reindirizza al file reale su cdndoc.spaggiari.eu."""

    url = DOWNLOAD_URL
    name = "api:cvv_dashboard:download"
    requires_auth = True  # accetta anche le URL firmate (async_sign_path)

    def __init__(self, hass: HomeAssistant) -> None:
        self.hass = hass

    async def get(self, request: web.Request) -> web.StreamResponse:
        q = request.query
        entry_id = q.get("entry_id")
        kind = q.get("kind")

        coordinator = self.hass.data.get(DOMAIN, {}).get(entry_id)
        # Sotto DOMAIN ci sono anche valori che non sono coordinatori (es. flag).
        if coordinator is None or not hasattr(coordinator, "api"):
            return web.Response(status=404, text="Integrazione ClasseViva non trovata")

        api = coordinator.api
        try:
            if kind == "noticeboard":
                real = await api.get_download_url(
                    "noticeboard", evt=q.get("evt"), pub=q.get("pub"), num=q.get("num")
                )
            elif kind == "didactics":
                real = await api.get_download_url("didactics", content_id=q.get("cid"))
            elif kind == "scrutinio":
                return await self._scrutinio(coordinator, q.get("indice"))
            else:
                return web.Response(status=400, text="Tipo allegato non valido")
        except Exception as err:  # noqa: BLE001
            _LOGGER.warning("Download ClasseViva fallito: %s", err)
            return web.Response(status=502, text="Errore ClasseViva")

        if not real:
            return web.Response(status=404, text="Allegato non disponibile")
        # 302 verso il file reale (cdndoc si autentica da solo con la query AUTH)
        raise web.HTTPFound(real)

    async def _scrutinio(self, coordinator, indice) -> web.StreamResponse:
        """Consegna il PDF di una pagella.

        Qui non basta un redirect: l'URL del documento vale solo con il cookie di
        sessione del portale, quindi il file va scaricato e ritrasmesso.
        Scaricarlo NON registra la presa visione, che sul portale è un passaggio
        distinto e volutamente non automatizzato.
        """
        try:
            documenti = (coordinator.data or {}).get("scrutini", [])
            posizione = int(indice)
            if posizione < 0:
                raise IndexError(posizione)
            documento = documenti[posizione]
        except (TypeError, ValueError, IndexError):
            return web.Response(status=404, text="Documento non trovato")

        contenuto, tipo = await coordinator.web.async_scarica_scrutinio(documento)
        if not contenuto:
            return web.Response(status=502, text="Documento non disponibile da ClasseViva")

        # Nell'intestazione solo caratteri ASCII stampabili, senza virgolette.
        nome = "".join(
            c for c in (documento.get("descrizione") or "documento")
            if c.isascii() and c.isprintable() and c != '"'
        ).strip() or "documento"
        mime = (tipo or "application/pdf").split(";")[0].strip()

        if mime == "text/html":
            # I pagellini sono pagine, non PDF: senza un <base> i loro CSS e le
            # immagini (indirizzi relativi al portale) non verrebbero caricati.
            host = documento.get("host") or BASE_HOST
            base = f'<base href="https://{host}/sol/app/default/">'.encode()
            testo = contenuto
            apertura = re.search(rb"<head[\s>]", testo, re.IGNORECASE)
            if apertura:
                chiusura = testo.find(b">", apertura.start())
                testo = testo[: chiusura + 1] + base + testo[chiusura + 1 :]
            else:
                testo = base + testo
            # La pagina viene dal portale ma e' servita dall'indirizzo di Home
            # Assistant: "sandbox" le toglie script e accesso alla sessione di HA.
            return web.Response(
                body=testo,
                content_type="text/html",
                charset="utf-8",
                headers={
                    "Content-Security-Policy": "sandbox",
                    "X-Content-Type-Options": "nosniff",
                },
            )

        return web.Response(
            body=contenuto,
            content_type=mime,
            headers={"Content-Disposition": f'inline; filename="{nome}.pdf"'},
        )
