# Usa CVV Dashboard con due o più studenti

Aggiungi una voce di integrazione per ogni studente. Ogni voce ha i propri sensori e calendari. La card può mostrare un solo studente o un gruppo.

## Trova il valore dell'account

L'opzione `account` usa la parte dell'account nell'ID di un'entità CVV Dashboard. Per trovarla:

1. Apri **Strumenti per sviluppatori > Stati**.
2. Trova un sensore che inizia con `sensor.cvv_dashboard_`.
3. Usa come valore di `account` la parte dell'account mostrata nell'ID.

L'editor visuale della card può proporre gli anni scolastici dei sensori Voti configurati. Non seleziona l'account. Imposta il valore dell'account in YAML.

## Mostra gli studenti in una dashboard Lovelace

Usa una card Grid e aggiungi una card CVV Dashboard per ogni studente. Aggiungi altre card per gruppi più grandi.

~~~yaml
type: grid
columns: 2
square: false
cards:
  - type: custom:cvv-dashboard-card
    account: student_one
    vista: combo
  - type: custom:cvv-dashboard-card
    account: student_two
    vista: combo
~~~

Puoi impostare una `vista` diversa per ogni card. Per esempio, mostra `agenda` per uno studente e `voti` per l'altro.

## Usa il pannello a tutto schermo

Attiva **Mostra nel menu laterale** su una sola voce di integrazione. Il pannello mostra tutti gli studenti configurati. Seleziona il nome di uno studente per aprire i suoi dati. Home Assistant ricorda la scelta nel browser.

Per scegliere l'ordine degli studenti o impostare i nomi visualizzati, aggiungi un elenco `studenti` a una voce manuale `panel_custom`:

~~~yaml
panel_custom:
  - name: cvv-dashboard-card-panel
    url_path: cvv-dashboard
    sidebar_title: CVV Dashboard
    sidebar_icon: mdi:school
    module_url: /cvv_dashboard_static/cvv-dashboard-card.js?v=0.4.4
    config:
      vista: combo
      studenti:
        - account: student_one
          nome: Studente Uno
        - account: student_two
          nome: Studente Due
~~~

Sostituisci i valori degli account con quelli negli ID delle entità. Dopo un aggiornamento, cambia `v=0.4.4` con la versione installata, così il browser carica il file aggiornato.

Se ometti `studenti`, il pannello mostra tutti gli account configurati in ordine alfabetico. Non usare sia l'opzione automatica del menu laterale sia un pannello manuale con lo stesso percorso.

## Avviso di aggiornamento HACS

In una versione che supporta questa funzione, HACS può mostrare un **!** giallo prima del nome dello studente in ogni card e nel selettore degli studenti. Selezionalo per aprire la pagina CVV Dashboard in HACS. HACS deve segnalare un aggiornamento e l'utente Home Assistant deve avere i diritti di amministratore. Le release precedenti potrebbero non avere questa funzione.

## Anni scolastici separati

Non serve una seconda voce di integrazione solo per guardare un altro anno. Usa il selettore dell'anno. Aggiungi un'altra voce per lo stesso account solo se vuoi sensori e calendari separati per un anno specifico.
