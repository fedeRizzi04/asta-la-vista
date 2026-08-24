# Asta la Vista

Asta la Vista è una web app pensata per assisterti durante l'asta del fantacalcio (per ora viene supportata solamente la modalità Classic). E' possibile caricare un listone in formato _.csv_ o _.xlsx_ contenente i giocatori (con relativi ruoli e squadre). A partire da questo listone sono presenti le seguenti funzionalità: 

- creazione di un'asta con partecipanti, in cui è possibile seguire in tempo reale lo stato dell'asta, visualizzando i giocatori acquistati da ogni partecipante insieme ai crediti rimanenti
- creazione di strategie (o fasce), le quali sono visualizzabili durante lo svolgimento delle aste in modo tale da capire quali dei giocatori inseriti nelle fasce sono stati già acquistati e quali invece sono ancora disponibili


## Motivazione

Il progetto nasce dal desiderio di provare a sviluppare interamente un'applicazione affidandosi ad un coding agent attraverso un lavoro di planning curato. Oltre a questo, durante le aste finalmente si potrà usare uno strumento gratuito e automatizzato, diverso dal solito foglio di carta o documento excel. 

## Requisiti

- Python 3.12 o successivo
- [uv](https://docs.astral.sh/uv/)

Docker non è necessario.

## Installazione

Clonare il repository, entrare nella cartella del progetto e creare la configurazione locale:

```bash
cp .env.example .env
uv sync
```

Il database SQLite verrà salvato nella cartella locale `instance`, esclusa da Git.

## Avvio del backend

```bash
uv run flask --app asta_la_vista.entrypoints.flask_app:create_app run --host 127.0.0.1
```

Il backend risponde su `http://127.0.0.1:5000`. L'endpoint di controllo è disponibile su
`http://127.0.0.1:5000/api/health`.

## Verifiche

Eseguire i test backend:

```bash
uv run pytest
```

Controllare stile ed errori statici:

```bash
uv run ruff check .
uv run ruff format --check .
```

Il frontend non avrà una suite di test automatizzata; verranno comunque verificati typecheck,
lint e build di produzione.

