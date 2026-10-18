# Calendari, sensori e servizi

CVV Dashboard aggiunge sensori e quattro calendari per ogni studente configurato.

## Calendari

| Calendario | Contenuti |
|---|---|
| Agenda | Compiti e note, escluse le prenotazioni delle aule. |
| Compiti | Compiti assegnati. |
| Note dei docenti | Note dei docenti, comunicazioni ed eventi delle aule virtuali. |
| Prenotazioni aula | Prenotazioni delle aule. |

Attiva i calendari in **Calendario** in Home Assistant. Puoi usare i loro ID anche in una card Calendario Lovelace. Trova gli ID esatti in **Strumenti per sviluppatori > Stati**.

## Sensori

| Sensore | Dati |
|---|---|
| Media | Media generale, media per materia, media dei periodi e anno. |
| Voti | Numero di voti, voti e numero di insufficienze. |
| Agenda | Eventi, compiti e note. |
| Bacheca | Comunicazioni non lette, testi, allegati e comunicazioni omesse. |
| Note | Annotazioni dei docenti e note disciplinari. |
| Scrutini | Pagelle pubblicate e link di download. |
| File Docenti | File condivisi dai docenti. |

Gli attributi possono contenere dati scolastici personali. Non pubblicarli in una issue.

## Servizi

| Servizio | Azione |
|---|---|
| `cvv_dashboard.aggiorna` | Richiede subito un aggiornamento dei dati. |
| `cvv_dashboard.carica_testi_bacheca` | Carica i testi mancanti. Non segna le comunicazioni come lette. |
| `cvv_dashboard.leggi_comunicazione` | Carica il testo completo e segna la comunicazione come letta nel registro ClasseViva. |

Se hai più di uno studente o anno configurato, scegli l'account corretto quando il servizio lo richiede.

## Allegati e pagelle

CVV Dashboard fornisce link firmati per scaricare gli allegati delle comunicazioni. Ogni link resta valido 12 ore. Aprire una pagella dalla card non registra la presa visione.

Aprire una comunicazione con **Leggi tutto** la segna come letta. Usa **Carica testi** per caricare il testo mancante senza cambiare lo stato di lettura.
