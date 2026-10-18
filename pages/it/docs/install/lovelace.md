# Aggiungi la card a Lovelace

CVV Dashboard aggiunge la card a Home Assistant quando si carica l'integrazione. Non aggiungere una risorsa manuale in **Impostazioni > Dashboard > Risorse**.

## Aggiungi una card

1. Apri la dashboard dove vuoi la card.
2. Entra in modalità modifica.
3. Seleziona **Aggiungi card**.
4. Seleziona la card CVV Dashboard oppure apri l'editor YAML manuale.
5. Usa questa configurazione minima:

~~~yaml
type: custom:cvv-dashboard-card
~~~

Senza altre opzioni, la card mostra tutte le viste per l'account studente rilevato.

## Scegli una vista

Usa l'opzione `vista` per mostrare una sola vista:

~~~yaml
type: custom:cvv-dashboard-card
vista: agenda
~~~

I valori validi sono `medie`, `voti`, `bacheca`, `agenda`, `note`, `scrutini`, `compiti` e `combo`.

## Usa una vista a tutta larghezza

Per mostrare una sola card su tutta la larghezza, imposta la vista come **Panel**. In YAML, usa `type: panel` per la vista:

~~~yaml
views:
  - title: Scuola
    type: panel
    cards:
      - type: custom:cvv-dashboard-card
        vista: combo
~~~

Per una vista con Sections, imposta la larghezza della card con `grid_options`:

~~~yaml
type: custom:cvv-dashboard-card
grid_options:
  columns: 12
~~~

## Mostra più di uno studente

Usa una card Grid e aggiungi una card CVV Dashboard per ogni studente. Per un esempio completo, leggi [Due o più studenti](../guide/multiple-students.md).

## Cambia le opzioni della card

L'editor visuale può impostare l'anno scolastico e mostrare o nascondere il selettore dell'anno. Usa YAML per impostare account, vista, titolo, animazioni o altre opzioni della card. Leggi [Viste e simboli](../guide/features.md) e [Anno scolastico](../guide/school-year.md).

Per mostrare tutti gli studenti in un'unica pagina a tutto schermo, usa il pannello laterale. Vedi [Due o più studenti](../guide/multiple-students.md).
