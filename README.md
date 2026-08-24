# Asta la Vista

Asta la Vista è una web app locale per preparare e seguire aste Classic del fantacalcio.
Gestisce il listone, le strategie a fasce, i partecipanti, gli acquisti, i crediti residui e gli
slot ancora disponibili.

Il progetto è anche una prova pratica: l'applicazione viene realizzata interamente con un coding
agent, partendo da requisiti discussi in anticipo e da un piano mantenuto durante lo sviluppo.

## Stato del progetto

Il progetto è in fase iniziale. Al momento è disponibile soltanto la base del backend Flask; le
istruzioni verranno aggiornate insieme alle funzionalità.

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

