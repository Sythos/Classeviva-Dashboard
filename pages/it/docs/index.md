# CVV Dashboard

CVV Dashboard porta i dati di ClasseViva in Home Assistant. Aggiunge una card Lovelace, un pannello per gli studenti, sensori, calendari e azioni.

L'integrazione legge i dati dell'account che configuri. Home Assistant salva nome utente e password. Il token di accesso resta in memoria e viene rinnovato quando serve.

## Da dove iniziare

1. [Installa Home Assistant](install/home-assistant.md).
2. [Installa HACS](install/hacs.md).
3. [Installa e configura CVV Dashboard](install/cvv-dashboard.md).
4. [Aggiungi la card a una dashboard Lovelace](install/lovelace.md).
5. Leggi la guida per [un solo studente](guide/single-student.md) o per [due o più studenti](guide/multiple-students.md).

## Dati disponibili

- Medie generali e risultati dei periodi.
- Voti, materie e voti recenti.
- Comunicazioni scolastiche e allegati.
- Eventi, compiti, note dei docenti e prenotazioni delle aule.
- Annotazioni dei docenti, note disciplinari e scrutini pubblicati.
- Calendari di Home Assistant per ogni studente.

La pagina [Viste e simboli](guide/features.md) elenca ogni vista, simbolo e comando della card.

## Requisiti

- Home Assistant 2024.7.0 o versione successiva.
- HACS installato in Home Assistant.
- Un account ClasseViva valido, genitore o studente.

CVV Dashboard è un progetto indipendente. Non è affiliato né supportato da Gruppo Spaggiari.

## Assistenza

Per un problema di configurazione, leggi [Risoluzione dei problemi](guide/troubleshooting.md). Per segnalare un problema software, usa il [tracker delle issue GitHub](https://github.com/Sythos/Classeviva-Dashboard/issues).

Il codice sorgente e gli archivi delle release sono su [GitHub](https://github.com/Sythos/Classeviva-Dashboard).
