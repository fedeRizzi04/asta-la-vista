# Asta la Vista

Asta la Vista è una web app pensata per assisterti durante l'asta del fantacalcio (per ora viene supportata solamente la modalità Classic). E' possibile caricare un listone in formato _.csv_ o _.xlsx_ contenente i giocatori (con relativi ruoli e squadre). A partire da questo listone sono presenti le seguenti funzionalità: 

- creazione di un'asta con partecipanti, in cui è possibile seguire in tempo reale lo stato dell'asta, visualizzando i giocatori acquistati da ogni partecipante insieme ai crediti rimanenti
- creazione di strategie (o fasce), le quali sono visualizzabili durante lo svolgimento delle aste in modo tale da capire quali dei giocatori inseriti nelle fasce sono stati già acquistati e quali invece sono ancora disponibili


## Motivazione

Il progetto nasce dal desiderio di provare a sviluppare interamente un'applicazione affidandosi ad un coding agent attraverso un lavoro di planning curato. Oltre a questo, durante le aste finalmente si potrà usare uno strumento gratuito e automatizzato, diverso dal solito foglio di carta o documento excel. 

## Requisiti

- Python 3.12 o successivo
- [uv](https://docs.astral.sh/uv/)
- Node.js 24 o successivo

## Installazione

Clonare il repository ed entrare nella cartella del progetto. Installare il backend e creare la
configurazione locale:

```bash
cd backend
cp .env.example .env
uv sync
uv run alembic upgrade head
```

Installare poi il frontend:

```bash
cd ../frontend
npm install
```

Il database SQLite verrà salvato nella cartella locale `backend/instance`, esclusa da Git.

## Avvio rapido

Dopo la prima installazione è possibile preparare e avviare l'intera applicazione con un solo
comando, eseguito dalla cartella principale del progetto:

```bash
./bin/start
```

Lo script applica le migrazioni, installa le dipendenze mancanti e avvia backend e frontend. Per
fermare entrambi i processi premere `Ctrl+C`.

## Avvio del backend

```bash
cd backend
uv run flask --app asta_la_vista.entrypoints.flask_app:create_app run --host 127.0.0.1
```

Il backend risponde su `http://127.0.0.1:5000`. L'endpoint di controllo è disponibile su
`http://127.0.0.1:5000/api/health`.

## Avvio del frontend

In un secondo terminale:

```bash
cd frontend
npm run dev
```

L'interfaccia è disponibile su `http://127.0.0.1:5173`. Durante lo sviluppo, le richieste a
`/api` vengono inoltrate automaticamente al backend Flask.

## Flusso dell'applicazione

1. Aprire la sezione Listone e importare il file CSV o XLSX con i calciatori.
2. Creare una o più strategie, definendo liberamente fasce, ordine e colori per ciascun ruolo.
3. Creare l'asta indicando crediti, slot, partecipanti ed eventualmente una strategia.
4. Avviare l'asta e registrare ogni acquisto. La schermata aggiorna crediti residui, puntata
   massima, slot e rosa di ogni partecipante.
5. Al termine dell'asta scaricare il resoconto in formato HTML, apribile direttamente su Linux e
   macOS con qualsiasi browser.

## Verifiche

Eseguire i test backend:

```bash
cd backend
uv run pytest
```

Controllare stile ed errori statici:

```bash
uv run ruff check .
uv run ruff format --check .
```

Per controllare il frontend:

```bash
cd frontend
npm run check
npm run lint
npm run build
```
