<p align="center">
  <img src="https://raw.githubusercontent.com/Sythos/Classeviva-Dashboard/main/docs/banner.jpg" width="800" alt="CVV Dashboard: il registro ClasseViva dentro Home Assistant">
</p>

# CVV Dashboard

[![HACS Custom](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)
[![Versione](https://img.shields.io/github/v/release/Sythos/Classeviva-Dashboard?label=versione&style=flat)](https://github.com/Sythos/Classeviva-Dashboard/releases)
[![Validation](https://github.com/Sythos/Classeviva-Dashboard/actions/workflows/validate.yml/badge.svg?branch=main&event=push)](https://github.com/Sythos/Classeviva-Dashboard/actions/workflows/validate.yml)

[![Apri il repository in HACS su My Home Assistant](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=Sythos&repository=Classeviva-Dashboard&category=integration)

[User guide in English](https://sythos.github.io/Classeviva-Dashboard/en/) · [Guida utente in italiano](https://sythos.github.io/Classeviva-Dashboard/it/)

Integrazione per **Home Assistant** che porta il registro elettronico **ClasseViva**
(Gruppo Spaggiari) in una dashboard completa: medie, voti, bacheca, agenda, annotazioni,
scrutini e compiti, più i calendari integrati in Home Assistant.

> Progetto indipendente, non affiliato né supportato da Gruppo Spaggiari.
> Accede solo ai dati del proprio account, come farebbe l'app ufficiale.

## Cos'è la Dashboard

CVV Dashboard raccoglie in un'unica **card Lovelace** tutto ciò che il registro mostra su
più pagine. La card trova da sola le entità dell'integrazione: non serve indicare nessun
`entity_id`.

| Scheda | Contenuto |
|---|---|
| **Medie** | Media generale in un grafico con quadrimestri |
| **Voti** | Cerchio con la media generale, barra per materia, ultimi voti; clic sulla materia per il dettaglio |
| **Bacheca** | Comunicazioni con testo e allegati, filtro "solo da leggere"; il testo HTML è mostrato formattato (link in una nuova scheda, senza script) |
| **Agenda** | Eventi e annotazioni raggruppati per giorno |
| **Annotazioni** | Annotazioni dei docenti e note disciplinari |
| **Scrutini** | Pagelle e pagellini pubblicati, scaricabili |
| **Compiti** | Compiti assegnati, raggruppati per giorno |

Il colore va in modo continuo dal rosso al verde in base al voto, con animazioni di
ingresso e un layout che si adatta alla larghezza della card. Sotto i 460 px le schede
mostrano le sole icone.

## Novità dall'inizio

- **0.1.0, la prima versione.** Integrazione e card in un solo pacchetto HACS: medie, voti, bacheca,
  agenda, annotazioni, scrutini e compiti. Quattro calendari per studente in Home Assistant, servizi per
  aggiornare i dati e leggere le comunicazioni, allegati con link firmati e una pagina a schermo intero
  per il menu laterale.
- **0.2.x, il selettore dell'anno scolastico.** Un menu a tendina nella card cambia anno: *Automatico*
  segue l'anno in corso (il nuovo anno parte il 1° settembre) e la scelta resta nel browser. Gli anni
  passati si scaricano al momento, senza un secondo login e senza aggiungere l'account più volte.
- **0.3.0, password e anno senza ricreare niente.** Se la password cambia, Home Assistant chiede quella
  nuova (riautenticazione). Le opzioni cambiano password e anno di uno studente e le entità mantengono gli
  stessi id.
- **0.4.0, voce automatica nel menu laterale.** Un interruttore nelle opzioni aggiunge la pagina CVV
  Dashboard al menu, senza toccare `configuration.yaml` e senza riavviare. Immagini del brand più leggere.
- **0.4.1, niente più "Errore di configurazione" all'avvio.** La card si registra appena parte Home
  Assistant, prima che l'integrazione scarichi i dati: una pagina aperta in quel momento non perde più le card.
- **0.4.2, bacheca.** Una comunicazione aperta perde l'etichetta "Da leggere" e resta nell'elenco dei
  "solo da leggere" finché non cambi vista, così fai in tempo a leggerla.
- **0.4.3, primo caricamento.** La card non mostra più "Errore di configurazione" se la pagina le passa i dati
  di Home Assistant troppo presto o in parte.
- **0.4.4, agenda.** L'agenda mostra gli eventi da oggi in poi, in ordine di data e di ora. Le date passate sono nascoste.
- **0.4.5, avviso di aggiornamento.** Un "!" giallo accanto al nome dello studente indica un aggiornamento HACS di questa integrazione. Lo vede solo un amministratore.

Il dettaglio di ogni versione, in inglese, è nel [changelog](CHANGELOG.md).

## Requisiti

> **Login requirement:** CVV Dashboard uses the standard ClasseViva user name and password. It works only if your school allows this login method. It does not work if your school requires SPID or CIE.
>
> **Requisito di accesso:** CVV Dashboard usa l'accesso standard a ClasseViva con nome utente e password. Funziona solo se l'istituto consente questo metodo e non impone l'accesso tramite SPID o CIE.

> **HACS deve essere già installato** in Home Assistant. Questa integrazione si installa
> solo tramite HACS: senza HACS segui la procedura manuale più sotto.

- Home Assistant 2024.7.0 o successivo.
- [HACS](https://hacs.xyz) installato e configurato.
- Un account ClasseViva (genitore o studente).

## Installazione

### HACS

Clicca il pulsante per aprire il repository nel tuo HACS:

[![Apri il repository in HACS su My Home Assistant](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=Sythos&repository=Classeviva-Dashboard&category=integration)

Oppure, a mano:

1. HACS → menu ⋮ → *Repository personalizzati*.
2. Incolla l'URL di questo repository, categoria **Integration**.
3. Cerca **CVV Dashboard**, installa e riavvia Home Assistant.
4. *Impostazioni → Dispositivi e servizi → Aggiungi integrazione → CVV Dashboard*.

La card Lovelace è inclusa nell'integrazione e viene caricata da sola: non serve
registrare nessuna risorsa.

### Manuale

Copia `custom_components/cvv_dashboard/` in `<config>/custom_components/`, riavvia
Home Assistant e aggiungi l'integrazione come al punto 4.

## Configurazione

| Campo | Descrizione |
|---|---|
| Username | email o codice utente del registro |
| Password | password del registro (salvata solo in Home Assistant) |
| Seleziona Anno | `Ultimo` per l'anno più recente con dati, oppure un anno preciso |

L'anno accetta i formati `25/26`, `2025/2026` o `25`, sempre interpretato come anno di
**inizio**. L'anno scolastico va dal 1° settembre al 31 agosto.

Per guardare gli anni passati nella card **non serve** aggiungere l'account più volte: vedi
[Cambiare anno scolastico](#cambiare-anno-scolastico). Aggiungere lo stesso account su un
anno preciso resta utile solo se vuoi sensori e calendari separati per quell'anno (ogni
istanza crea un dispositivo distinto).

### Accesso al registro e token

- L'integrazione fa il login da sola con utente e password salvati e ottiene un **token di accesso**,
  che il registro fa durare circa 90 minuti.
- Quando il token **scade** (o il registro lo rifiuta) l'integrazione lo **rigenera da sola**, rifacendo
  il login: non devi fare niente e non devi mai inserire un token. I dati si aggiornano ogni 30 minuti.
- Il token resta solo in memoria. In Home Assistant si salvano soltanto utente e password.
- Se la password è cambiata sul registro, il login non riesce più: parte la riautenticazione descritta qui sotto.

### Cambiare password o anno

- **Password cambiata sul registro:** quando il registro rifiuta la password salvata, Home Assistant
  mostra una notifica *Riautenticazione*. Inserisci la password nuova: l'integrazione la prova,
  verifica che l'account sia lo stesso studente e la salva, senza ricreare niente.
- **Cambiare password o anno di un'istanza esistente:** *Impostazioni → Dispositivi e servizi →
  CVV Dashboard → Configura*. Lascia la password vuota per tenere quella attuale. Cambiando anno,
  entità e dispositivo mantengono gli stessi id, quindi dashboard e automazioni continuano a funzionare.
- La password viene provata sul registro prima di essere salvata. L'integrazione rifiuta un account
  di un altro studente e un anno già usato da un'altra istanza.

For full installation and configuration steps, see the [user guide](https://sythos.github.io/Classeviva-Dashboard/).

## Configurabilità della card

```yaml
type: custom:cvv-dashboard-card
```

Opzioni comuni:

| Opzione | Valori | Default |
|---|---|---|
| `vista` | `medie`, `voti`, `bacheca`, `agenda`, `note`, `scrutini`, `compiti`, `combo` | `combo` |
| `account` | parte dell'entity_id, se hai più studenti | — |
| `anno_scolastico` | anno configurato, ad esempio `"26/27"` | più recente |
| `titolo` | testo dell'intestazione (`""` per nasconderla) | nome dello studente |
| `animazioni` | `true` / `false` | `true` |
| `selettore_anno` | `true` / `false`: mostra il menu per cambiare anno | `true` |
| `versione` | `true` mostra la versione della card in fondo | `false` |

### Cambiare anno scolastico

In alto a destra la card mostra un **menu a tendina con l'anno scolastico**, quando ce n'è
più di uno:

- **Automatico** segue l'anno in corso. Il nuovo anno parte il **1° settembre**: fino al
  31 agosto vale l'anno iniziato a settembre precedente. Se quell'anno non è disponibile
  si usa il più recente.
- Gli anni offerti sono quelli delle istanze configurate più quelli che il registro elenca
  per lo studente. Se il registro ne elenca uno solo, il menu propone l'anno in corso e
  quello appena concluso.
- La scelta resta nel browser. Nella pagina del menu laterale vale per tutti gli studenti.
- Un anno che non ha un'istanza viene scaricato **al momento**, riusando il login già
  attivo, e tenuto in cache per 30 minuti: non servono altri accessi al registro. Il
  primo caricamento di un anno passato può richiedere qualche secondo.
- `anno_scolastico` nella configurazione resta l'anno di partenza. Con
  `selettore_anno: false` il menu sparisce e vale solo `anno_scolastico`.

```yaml
type: custom:cvv-dashboard-card
account: anna
anno_scolastico: "25/26"   # anno di partenza, poi si cambia dal menu
```

Solo per `vista: medie`:

| Opzione | Valori | Default |
|---|---|---|
| `layout` | `auto`, `verticale`, `orizzontale` | `auto` |
| `dimensione` | diametro del cerchio in px | `170` |
| `periodi` | `true` / `false`, linee dei quadrimestri | `true` |
| `massimo` | voto massimo della scala | `10` |

Esempi:

```yaml
type: custom:cvv-dashboard-card
vista: medie
layout: verticale
dimensione: 190
```

```yaml
type: custom:cvv-dashboard-card
vista: compiti
account: anna
anno_scolastico: "26/27"
```

L'editor visuale della card propone gli anni disponibili tra le istanze configurate.

### Voce nel menu laterale

**Modo semplice:** *Impostazioni → Dispositivi e servizi → CVV Dashboard → Configura* e attiva
**Mostra nel menu laterale**. La voce *CVV Dashboard* compare subito, senza riavviare e senza
toccare `configuration.yaml`. Basta attivarla su una sola istanza: vale per tutti gli studenti,
e si toglie disattivando l'opzione. Se hai già una pagina con indirizzo `cvv-dashboard` messa a
mano (vedi sotto), l'integrazione non la tocca e non crea la voce automatica: scegli una delle due.

**A mano**, per personalizzare titolo, icona o le opzioni della pagina, aggiungi a
`configuration.yaml`:

```yaml
panel_custom:
  - name: cvv-dashboard-card-panel
    url_path: cvv-dashboard
    sidebar_title: CVV Dashboard
    sidebar_icon: mdi:school
    module_url: /cvv_dashboard_static/cvv-dashboard-card.js?v=0.4.5
    config:
      vista: combo
      anno_scolastico: "26/27"
      dimensione: 200
```

In cima alla pagina c'è un pulsante per ogni studente configurato; la scelta è ricordata
dal browser. Con `studenti` si decide quali account mostrare e in che ordine; ogni voce
è un account oppure una coppia `account` e `nome` per cambiare il nome mostrato:

```yaml
studenti:
  - anna
  - account: luca
    nome: Lu
```

Senza `studenti` compaiono tutti, in ordine alfabetico. Dopo un aggiornamento cambia il
numero dopo `?v=` e riavvia, altrimenti il browser può usare la versione in cache.

## Uso in Panorama (Lovelace)

Con **Lovelace** la card si può mettere in una vista di tipo **Panorama** (una sola card a
tutta larghezza, `type: panel` in YAML). Per mostrare due studenti affiancati usa uno
stack orizzontale:

```yaml
views:
  - title: Panoramica
    type: panel
    cards:
      - type: horizontal-stack
        cards:
          - type: custom:cvv-dashboard-card
            account: luca
            vista: agenda
          - type: custom:cvv-dashboard-card
            account: giulia
            vista: voti
```

Per allargare la card in una vista a **sezioni** usa:

```yaml
type: custom:cvv-dashboard-card
grid_options:
  columns: 12
```

## Integrazione con il calendario di Home Assistant

L'integrazione crea **quattro calendari per studente**, così nel calendario di Home
Assistant ognuno ha il suo colore:

- **Agenda**: riepilogo di compiti e annotazioni
- **Compiti**: solo i compiti assegnati
- **Note dei docenti**: annotazioni, avvisi, aule virtuali
- **Prenotazioni aula**: solo le prenotazioni d'aula

Si attivano dalle caselle a sinistra nella pagina *Calendario* e si possono usare in
qualunque card `calendar`:

```yaml
type: calendar
initial_view: dayGridMonth
entities:
  - entity: calendar.cvv_dashboard_nome_compiti
    color: "#D7D765"
  - entity: calendar.cvv_dashboard_nome_note_dei_docenti
    color: "#A5D7FD"
  - entity: calendar.cvv_dashboard_nome_prenotazioni_aula
    color: "#55f74f"
```

Controlla i nomi esatti delle entità in *Strumenti per sviluppatori → Stati*.

## Sensori e servizi

| Entità | Stato | Attributi principali |
|---|---|---|
| Media | media generale | `per_materia`, `per_periodo`, `anno` |
| Voti | numero di voti | `items`, `insufficienze` |
| Agenda | eventi in agenda | `items` (compiti e annotazioni) |
| Bacheca | comunicazioni non lette | `items` con testo e allegati; `omesse` |
| Note | note e annotazioni | `items`, `da_leggere` |
| Scrutini | documenti pubblicati | `items` con `download_url` |
| File Docenti | file condivisi | `items` per docente |

| Servizio | Cosa fa |
|---|---|
| `cvv_dashboard.aggiorna` | forza subito il download dei dati |
| `cvv_dashboard.carica_testi_bacheca` | scarica i testi mancanti **senza** segnarli come letti |
| `cvv_dashboard.leggi_comunicazione` | apre una comunicazione e ne restituisce il testo (**la segna come letta**) |

Gli allegati si scaricano da `/api/cvv_dashboard/download` con URL firmate valide 12 ore.
Aprire una pagella da qui **non** registra la presa visione.

## Screenshot

### Vista Panorama con due studenti

![Vista Panorama](https://raw.githubusercontent.com/Sythos/Classeviva-Dashboard/main/docs/screenshots/panoramica.jpeg)

Due card affiancate in una vista Panorama, una per studente, ognuna con le sue schede. Si vedono le
**Medie**: il cerchio con la media generale e la barra del periodo. In alto a destra di ogni card c'è il
menu dell'anno scolastico.

### Voti

![Scheda Voti](https://raw.githubusercontent.com/Sythos/Classeviva-Dashboard/main/docs/screenshots/voti.jpeg)

La scheda **Voti**: media generale, una barra per ogni materia con il numero di voti e gli ultimi voti,
colorati dal rosso al verde in base al valore. In alto la barra degli studenti, a destra il menu
dell'anno con **Automatico (26/27)**.

### Bacheca

![Scheda Bacheca](https://raw.githubusercontent.com/Sythos/Classeviva-Dashboard/main/docs/screenshots/bacheca.jpeg)

La scheda **Bacheca**: le comunicazioni con data, titolo, un'anteprima del testo con *Leggi tutto* e lo
stato "in corso". Sopra l'elenco ci sono *Solo da leggere*, *Carica testi* e *Aggiorna*.

### Selettore dell'anno

![Selettore dell'anno scolastico](https://raw.githubusercontent.com/Sythos/Classeviva-Dashboard/main/docs/screenshots/selettore_anno.jpeg)

Il menu a tendina in alto a destra della card cambia l'anno scolastico. **Automatico (26/27)** segue
l'anno in corso; sotto ci sono gli anni disponibili, per esempio **26/27 · in corso** e **25/26**.

### Calendario di Home Assistant

![Calendario di Home Assistant](https://raw.githubusercontent.com/Sythos/Classeviva-Dashboard/main/docs/screenshots/calendario.jpeg)

La pagina *Calendario* di Home Assistant con i calendari di ClasseViva: per ogni studente Agenda,
Compiti, Note dei docenti e Prenotazioni aula, attivabili con le caselle a sinistra. Verifiche, note e
compiti compaiono nella vista mensile, ognuno nel colore del proprio calendario. A sinistra, nel menu,
la voce **CVV Dashboard**.

## Note

- I dati si aggiornano ogni 30 minuti.
- La chiave API in `const.py` è quella dell'app Android ufficiale. Spaggiari la cambia
  periodicamente: se il login dà errore `apikey.3` va ricatturata da una versione recente
  dell'app.
- Troppi tentativi di login sbagliati bloccano l'account per circa 60 minuti.
- Alcune azioni registrano la lettura sul registro. L'integrazione le compie solo se le
  chiedi, con il servizio `leggi_comunicazione`.
- Il banner, gli screenshot e la documentazione non fanno parte della release HACS: l'archivio
  installato contiene solo `custom_components/cvv_dashboard`.

## Licenza

[MIT](LICENSE)

## Crediti

Per l'accesso al registro è stato usato il codice API di
[Davitekk](https://github.com/Davitekk), autore dell'idea originale di integrazione e
card per ClasseViva su Home Assistant, rilasciato con licenza MIT.
