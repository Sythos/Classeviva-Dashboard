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

"""Costanti per l'integrazione CVV Dashboard."""

DOMAIN = "cvv_dashboard"

CONF_USERNAME = "Username"
CONF_PASSWORD = "Password"
CONF_ANNO = "Anno"

# Valore che significa "usa l'anno piu' recente che l'account puo' vedere".
ANNO_ULTIMO = "Ultimo"

# Header estratti dall'app ufficiale Android (mitmproxy, ago 2026).
# ATTENZIONE: la chiave è "Tg1NWEwNGIgIC0K" e lo User-Agent "cvvs/5.12.02/android".
# Questi vengono cambiati periodicamente da Spaggiari: se il login inizia a dare
# errore "apikey.3" vanno ri-catturati da una nuova versione dell'app.
API_KEY = "Tg1NWEwNGIgIC0K"
USER_AGENT = "cvvs/5.12.02/android"

BASE_HOST = "web.spaggiari.eu"

# Il portale WEB legacy (voti) rifiuta gli header dell'app: serve un UA da browser.
WEB_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:154.0) Gecko/20100101 Firefox/154.0"
)

# Ogni quanto aggiornare i dati (i token durano 90 minuti, quindi 30 è comodo).
UPDATE_MINUTES = 30
