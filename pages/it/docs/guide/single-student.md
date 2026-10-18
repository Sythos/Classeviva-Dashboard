# Usa CVV Dashboard con un solo studente

Per un solo studente, aggiungi una voce di integrazione CVV Dashboard e una card.

## Configura lo studente

Segui [Installa CVV Dashboard](../install/cvv-dashboard.md). Inserisci l'account ClasseViva dello studente. Home Assistant crea i sensori e i calendari per quell'account.

Per mostrare il pannello a tutto schermo, attiva **Mostra nel menu laterale** nelle opzioni dell'integrazione. Poi apri **CVV Dashboard** nel menu laterale.

## Aggiungi la card

Usa la card in una dashboard Lovelace:

~~~yaml
type: custom:cvv-dashboard-card
~~~

Se hai configurato un solo studente, la card rileva l'account. Imposta `vista` per mostrare una sola vista, per esempio `voti` o `agenda`.

## Scegli l'anno scolastico

Usa **Automatico** per seguire l'anno in corso. Usa il menu dell'anno per aprire un altro anno reso disponibile da ClasseViva. Leggi [Anno scolastico](school-year.md) per le regole sulle date e le opzioni.

## Funzioni

- Consulta medie, voti, comunicazioni, compiti, eventi e note dei docenti.
- Scarica pagelle e pagellini pubblicati.
- Usa i quattro calendari Home Assistant dello studente.
- Aggiorna i dati o carica il testo delle comunicazioni senza segnarle come lette.

La pagina [Viste e simboli](features.md) spiega ogni vista e comando.
