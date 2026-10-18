# Risoluzione dei problemi

## CVV Dashboard non appare in HACS

Aggiungi `https://github.com/Sythos/Classeviva-Dashboard` come repository personalizzato. Seleziona la categoria **Integration**. Poi cerca **CVV Dashboard**.

## L'integrazione non si carica

1. Verifica che Home Assistant abbia la versione 2024.7.0 o successiva.
2. Apri **Impostazioni > Sistema > Registri** e cerca un errore di CVV Dashboard.
3. Verifica che HACS abbia completato il download.
4. Riavvia Home Assistant dopo l'installazione o un aggiornamento.
5. Apri **Impostazioni > Dispositivi e servizi** e controlla la voce dell'integrazione.

## Il login non riesce

- Verifica nome utente e password nell'app o nel sito ClasseViva.
- Se la password è cambiata, apri la richiesta di riautenticazione di Home Assistant e inserisci quella nuova.
- Non ripetere molti login errati. L'account può bloccarsi per circa 60 minuti.
- Un errore di connessione o della chiave API può richiedere una versione più recente di CVV Dashboard. Controlla gli aggiornamenti in HACS.

## La card mostra un errore di configurazione

Aggiorna CVV Dashboard all'ultima versione offerta da HACS e ricarica la pagina del browser. La versione 0.4.3 ha aggiunto una correzione per i dati di Home Assistant incompleti o ricevuti troppo presto al primo caricamento.

Se usi una voce manuale `panel_custom`, aggiorna il valore della versione in `module_url` e ricarica Home Assistant. La vecchia voce `panel_custom` può entrare in conflitto con l'opzione automatica del menu laterale se usa lo stesso percorso.

## Una vista della card è vuota

- Verifica che lo studente selezionato abbia dati per l'anno scelto.
- Imposta il valore corretto di `account` se hai configurato più studenti.
- Seleziona **Aggiorna** per richiedere nuovi dati.
- Alcuni dati appaiono solo dopo che la scuola li pubblica.

## Non compare l'avviso giallo di HACS

L'avviso richiede HACS, un account amministratore Home Assistant e un aggiornamento di CVV Dashboard segnalato da HACS. L'avviso è disponibile solo nelle versioni che includono questa funzione. Le release precedenti potrebbero non mostrarlo.

## Chiedi assistenza

Leggi i [registri di Home Assistant](https://www.home-assistant.io/docs/configuration/troubleshooting/) e crea una [issue GitHub](https://github.com/Sythos/Classeviva-Dashboard/issues) se il problema continua. Rimuovi nomi utente, password, token, nomi degli studenti e dati scolastici da registri e schermate prima di condividerli.
