# Installa CVV Dashboard

Usa HACS per installare CVV Dashboard. L'integrazione installa anche la card Lovelace. Non devi aggiungere una risorsa separata per la card.

## Aggiungi il repository a HACS

1. Apri **HACS** in Home Assistant.
2. Apri il menu in alto a destra e seleziona **Repository personalizzati**.
3. Inserisci questo indirizzo:

   `https://github.com/Sythos/Classeviva-Dashboard`

4. Seleziona **Integration** come categoria.
5. Aggiungi il repository. Cerca **CVV Dashboard**.
6. Apri l'elemento e seleziona **Download**.
7. Riavvia Home Assistant.

Puoi anche usare il [collegamento My Home Assistant](https://my.home-assistant.io/redirect/hacs_repository/?owner=Sythos&repository=Classeviva-Dashboard&category=integration) per aprire il repository in HACS.

## Aggiungi l'integrazione

1. Apri **Impostazioni > Dispositivi e servizi**.
2. Seleziona **Aggiungi integrazione**.
3. Cerca **CVV Dashboard**.
4. Inserisci il nome utente e la password di ClasseViva.
5. Lascia l'anno su **Ultimo** per usare l'ultimo anno con dati. Potrai cambiarlo dopo.
6. Invia il modulo e attendi che Home Assistant verifichi l'account.

Home Assistant salva nome utente e password. CVV Dashboard conserva il token di accesso in memoria e lo rinnova quando scade. I dati si aggiornano ogni 30 minuti.

## Mostra il pannello dello studente

Per aggiungere **CVV Dashboard** al menu laterale di Home Assistant:

1. Apri **Impostazioni > Dispositivi e servizi**.
2. Seleziona **CVV Dashboard**.
3. Apri **Configura**.
4. Attiva **Mostra nel menu laterale**.

Attiva questa opzione su una sola istanza. Il pannello può mostrare tutti gli studenti configurati.

## Aggiorna l'integrazione

Apri HACS, seleziona **CVV Dashboard** e installa l'aggiornamento disponibile. Riavvia Home Assistant quando HACS te lo chiede.

Alcune release possono mostrare un **!** giallo prima del nome dello studente quando HACS segnala un aggiornamento per questo repository. Seleziona il simbolo per aprire CVV Dashboard in HACS. Il simbolo non installa l'aggiornamento.

## Se il repository è già nell'elenco

Se HACS mostra CVV Dashboard nel suo elenco normale, puoi installarlo da lì. Se non lo trovi, segui i passaggi per il repository personalizzato.
