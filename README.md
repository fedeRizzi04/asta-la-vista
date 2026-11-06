# Asta la Vista

[![Backend](https://github.com/fedeRizzi04/asta-la-vista/actions/workflows/backend.yml/badge.svg)](https://github.com/fedeRizzi04/asta-la-vista/actions/workflows/backend.yml)
[![Release](https://img.shields.io/github/v/release/fedeRizzi04/asta-la-vista?color=204c39)](https://github.com/fedeRizzi04/asta-la-vista/releases/latest)
[![License: MIT](https://img.shields.io/badge/license-MIT-204c39)](LICENSE)
[![Python 3.12+](https://img.shields.io/badge/python-3.12%2B-204c39?logo=python&logoColor=white)](backend/pyproject.toml)
[![Node 24+](https://img.shields.io/badge/node-24%2B-204c39?logo=node.js&logoColor=white)](frontend/package.json)
[![Svelte 5](https://img.shields.io/badge/svelte-5-204c39?logo=svelte&logoColor=white)](frontend/package.json)

Asta la Vista is a web app that assists you during a fantacalcio (Italian fantasy football)
auction. For now only the Classic mode is supported. Upload a player list in _.csv_ or _.xlsx_
format, with each player's role and team, and run the whole auction from there: no more
spreadsheets, or pen and paper.

The user interface is in Italian.

## Features

- **Player list (Listone)**: import the official fantacalcio.it file and keep track of every
  player's role, team, price and availability.
- **Strategies**: create custom global tiers (colour, order, maximum spending percentage) and
  assign each role's players to them, so you always know at a glance whom to buy and for how much.
- **Live auctions**: follow every participant's remaining credits, free slots and squad in real
  time while you record purchases. Your tiers stay visible, so you can see who has already been
  taken. A 360-degree view of each role shows the players already bought and those still
  available to call.
- **Final report**: when the auction ends, download an HTML summary. It opens in any browser,
  with no server or internet connection.

<p align="center">
  <img src="assets/screenshots/strategies.jpg" alt="Tier management" width="49%" />
  <img src="assets/screenshots/live-auction.jpg" alt="Auction in progress" width="49%" />
</p>

There is also a dark theme, for auctions that run late into the night (we know a thing or two
about that):

<p align="center">
  <img src="assets/screenshots/dark-theme.jpg" alt="Player list in the dark theme" width="70%" />
</p>

## Why

The project started as an experiment: building a whole application with a coding agent, guided
by careful planning. It also gives auctions a free, automated tool, instead of the usual sheet
of paper or spreadsheet (which sometimes isn't free either).

## Getting started

There are three ways to run Asta la Vista. They all run the same application.

| | Best for | You need |
|---|---|---|
| [Desktop app](#desktop-app) | Anyone: download and double-click | Windows 10/11 (64-bit) or a Mac with Apple Silicon |
| [Docker](#docker) | Running it in a container, or on a home server | Docker with the Compose plugin |
| [From source](#from-source) | Development | Python 3.12+, uv and Node.js 24+ |

### Desktop app

Download the latest version from the
[**Releases page**](https://github.com/fedeRizzi04/asta-la-vista/releases/latest):

- **Windows**: `AstaLaVista-<version>-windows-setup.exe`
- **macOS (Apple Silicon)**: `AstaLaVista-<version>-macos.zip`

The app opens in its own window, served by a small local server that runs on your computer.
Nothing is sent over the internet: your data stays on your computer.

The app is free and is not signed with a paid Apple or Microsoft developer certificate, so your
computer warns you the first time you open it. This is expected. You only need to allow it once.

#### Windows

1. Your browser may say the file "isn't commonly downloaded". Choose **Keep** (in Edge: **⋯ →
   Keep → Show more → Keep anyway**).
2. Double-click it. If you see **"Windows protected your PC"**, click **More info**, then
   **Run anyway**.
3. The installer puts the app in your user folder, so no administrator password is needed, and
   asks whether to add an icon to the desktop. At the end it can open the app.

From then on, open **Asta la Vista** from the Start menu, like any other app. You can delete
the downloaded installer.

The window uses Microsoft Edge WebView2, which is already part of Windows 11 and of an updated
Windows 10. If your PC lacks it, the app tells you so: install it from
[Microsoft's WebView2 page](https://developer.microsoft.com/microsoft-edge/webview2/) and open
the app again.

#### macOS

1. Double-click the downloaded `.zip` to extract **Asta la Vista**, then drag it into your
   **Applications** folder.
2. Open it. macOS will say it cannot verify the app: click **Done** (do not move it to the
   Trash).
3. Open **System Settings → Privacy & Security**, scroll down to the message about
   "Asta la Vista", and click **Open Anyway**. Confirm with your password.

If you are comfortable with the Terminal, this command does the same as steps 2–3:

```bash
xattr -dr com.apple.quarantine "/Applications/Asta la Vista.app"
```

#### Using the app

- Asta la Vista opens in **its own window**. Closing the window quits the app; it asks you
  first, because an auction may be in progress.
- **File → Apri cartella dati** opens the folder that holds your data. On macOS the menu is in
  the menu bar at the top of the screen; on Windows it is at the top of the window.
- Opening the app again while it is already running brings its window to the front. If the copy
  that is running is an older version, for example right after you downloaded an update, the
  app tells you to close it first.
- Downloads, such as the final report, ask you where to save the file.
- The version you are running is shown at the bottom of every page.

#### Your data

Your auctions, strategies and player lists are saved in a database file in this folder:

| System | Folder |
|---|---|
| macOS | `~/Library/Application Support/Asta la Vista` |
| Windows | `%APPDATA%\Asta la Vista` |

The folder contains:

- `asta-la-vista.sqlite3`: the database;
- `asta-la-vista.log`: a log file, useful when reporting a problem;
- `instance.json` and `instance.lock`: small files that stop the app from being started twice;
- on Windows, `webview`: what the window remembers, such as the theme you chose.

On macOS, the window keeps what it remembers in the system's own folders instead: see
[Uninstalling](#desktop-app-1).

To back up your data, quit the app and copy the folder.

#### Updating

When a new version is published, a banner at the top of the page tells you, with a link to its
download page. If you close the banner, it stays hidden until the next version comes out. To
find out, the app asks GitHub for the latest release at most every few hours. Nothing about you
or your auctions is sent, and when you are offline the app simply skips the check.

To update, quit the app and install the new version: on Windows, run its installer, which
replaces the old version where it is; on macOS, replace the old app in **Applications**. Your
data is kept: the new version updates the database automatically the first time it starts. If
an update on Windows is interrupted, for example cancelled while copying files, and the app no
longer opens, run the installer again: your data is not affected. What changed in each
version is listed in the [changelog](CHANGELOG.md).

### Docker

You need Docker with the Compose plugin. From the project root, run:

```bash
docker compose up --build
```

On the first start, Docker builds the image, creates the database and applies the migrations.
When the application is ready, open `http://localhost:5000`. Later you can start it with just
`docker compose up`. After you update the project, add `--build` again to rebuild the image.

To use a different port, for example `8080`:

```bash
HOST_PORT=8080 docker compose up
```

The SQLite database is stored in the Docker volume `app-data`, so auctions and strategies survive
`docker compose down` and image rebuilds. To delete them too, see [Uninstalling](#docker-1).

To be told when a new version is available, as the desktop app does, start it with:

```bash
UPDATE_CHECK=true docker compose up
```

### From source

You need:

- Python 3.12 or later
- [uv](https://docs.astral.sh/uv/)
- Node.js 24 or later

After cloning the repository, install the backend and create the local configuration:

```bash
cd backend
cp .env.example .env
uv sync
uv run alembic upgrade head
```

Then install the frontend:

```bash
cd ../frontend
npm install
```

The SQLite database is saved in the local folder `backend/instance`, which Git ignores.

After this first setup, you can prepare and start the whole application from the project root
with:

```bash
./bin/start
```

The script applies the migrations, re-syncs the dependencies whenever the lockfiles change, and
starts the backend and the frontend. The `APP_HOST` and `APP_PORT` settings in `backend/.env`
are used by both the local server and the frontend proxy. Set `UPDATE_CHECK=true` in the same
file to see the new-version banner. Do not run the script with `sudo`: the configuration and the
database must belong to your user.

#### Starting the backend manually

```bash
cd backend
uv run flask --app asta_la_vista.entrypoints.flask_app:create_app run --host 127.0.0.1
```

The backend answers on `http://127.0.0.1:5000`. The health check is at
`http://127.0.0.1:5000/api/health`.

#### Starting the frontend manually

In a second terminal:

```bash
cd frontend
npm run dev
```

The interface is available at `http://127.0.0.1:5173`. During development, requests to `/api`
are forwarded to the Flask backend.

#### Building the desktop app yourself

You can build the desktop app for the system you are on (macOS builds the `.app`, Windows the
`AstaLaVista` folder with `AstaLaVista.exe` inside) with:

```bash
./bin/build-desktop
```

The result is in `dist/desktop/`. On Windows, the release workflow then packs that folder into
the installer with [Inno Setup](https://jrsoftware.org/isinfo.php):
`iscc /DVersion=<version> desktop\installer.iss`. On macOS, open it with
`open "dist/desktop/Asta la Vista.app"`. To check a build automatically, run:

```bash
./bin/smoke-test-desktop "dist/desktop/Asta la Vista.app/Contents/MacOS/AstaLaVista"
```

The smoke test starts the app without its window (`--headless`) and with a temporary data
folder, checks the API and the frontend, stops the app and deletes the temporary folder. It
cannot see the window: for that, use the checklist in
[Releasing a new version](#releasing-a-new-version).

You can also run the desktop launcher without building it:

```bash
cd backend
uv run --group desktop python -m asta_la_vista.entrypoints.desktop
```

Both the build and this command use the same data folder as the downloaded app (see
[Your data](#your-data)). To keep test data separate, set `ASTA_LA_VISTA_DATA_DIR` to another
folder before starting it. Add `--headless` to start only the server, without the window, until
you press Ctrl+C.

## Preparing the player list

Before your first auction, Asta la Vista needs the list of players (the _listone_). You get it
from fantacalcio.it and import it once. You can import it again whenever it changes.

### Downloading the file

1. Log in to fantacalcio.it, then open the
   [quotations page](https://www.fantacalcio.it/quotazioni-fantacalcio). It shows the current
   season by default; the season selector lets you pick another one.
2. Click **Scarica**. This downloads the file, named like
   `Quotazioni_Fantacalcio_Stagione_2026_27.xlsx`. Do not edit it.

### Importing it

1. Open the **Listone** section of the app.
2. Choose the file and click **Importa**.
3. A message tells you how many players were added, updated or deactivated, and how many changed
   role. The counts per role are shown right below it, so you can check them at a glance.

### Importing it again

You can import a newer file at any time, for example when quotations or teams change after the
transfer market. Players are matched by their `Id`, so nothing already set up is lost:

- new players are added, and existing ones get their name, team, role and quotation updated;
- players missing from the new file are **deactivated**, not deleted. They disappear from the
  list, unless you tick **Mostra inattivi**;
- if a player changed role, the strategies that contain them follow the new role;
- if an auction is in progress, the app asks you to confirm before importing.

### Using another file

The app also accepts a _.csv_ file, or an _.xlsx_ file you built yourself, as long as it follows
the same layout as the official one:

- an _.xlsx_ file needs a sheet named `Tutti`;
- the header row must have the columns `Id`, `R` (role: `P`, `D`, `C` or `A`), `Nome` and
  `Squadra`. It can be among the first 10 rows, because the official file starts with a title;
- `Qt.A` (the current quotation, a whole number) and `RM` (the Mantra roles, separated by `;`)
  are optional;
- a _.csv_ file must be UTF-8, with `,` or `;` as separator;
- every `Id` must be unique, and no row can have an empty `Id`, `R`, `Nome` or `Squadra`.

If something is wrong with the file, the app tells you what instead of importing part of it.

## Uninstalling

Follow the section that matches how you used Asta la Vista. If you used more than one method,
follow each of them.

### Desktop app

1. **Quit the app**: close its window.
2. **Delete the app**:
   - macOS: drag **Asta la Vista** from **Applications** to the Trash, then empty the Trash. Also
     delete the downloaded `.zip`.
   - Windows: open **Settings → Apps → Installed apps**, find **Asta la Vista**, and choose
     **⋯ → Uninstall**. This keeps your data, which step 3 deletes.
3. **Delete your data** (database, log and instance files). This cannot be undone, so back up
   the folder first if you might want your auctions later.
   - macOS: in Finder, choose **Go → Go to Folder…**, type
     `~/Library/Application Support`, and move the **Asta la Vista** folder to the Trash. Then
     do the same for what the window remembers: the `io.github.federizzi04.astalavista` folder
     in `~/Library/WebKit` and in `~/Library/Caches`, and the
     `io.github.federizzi04.astalavista.plist` file in `~/Library/Preferences`. Or, in the
     Terminal:

     ```bash
     rm -rf ~/Library/Application\ Support/Asta\ la\ Vista \
       ~/Library/WebKit/io.github.federizzi04.astalavista \
       ~/Library/Caches/io.github.federizzi04.astalavista \
       ~/Library/Preferences/io.github.federizzi04.astalavista.plist
     ```

   - Windows: press **Win + R**, type `%APPDATA%`, press Enter, and delete the
     **Asta la Vista** folder. Or, in PowerShell:

     ```powershell
     Remove-Item -Recurse -Force "$env:APPDATA\Asta la Vista"
     ```

Asta la Vista writes nothing else on your computer.

### Built from source

The local builds and the desktop launcher store their data in the same folder as the downloaded
app, so start with steps 1 and 3 of [Desktop app](#desktop-app-1). If you set
`ASTA_LA_VISTA_DATA_DIR`, delete that folder as well. If you copied the built `.app` into
**Applications**, delete it there too. On macOS, the launcher started without building it keeps
what its window remembers under the name `python` instead:

```bash
rm -rf ~/Library/WebKit/python ~/Library/Caches/python
```

Then, everything else lives inside the cloned repository:

| Path | Contents |
|---|---|
| `backend/instance/` | database used by `./bin/start` and the manual backend |
| `backend/.env` | local configuration |
| `backend/.venv/` | Python dependencies |
| `frontend/node_modules/`, `frontend/.svelte-kit/`, `frontend/build/` | frontend dependencies and builds |
| `dist/`, `build/` | desktop app builds |

Deleting the repository folder removes all of them. To keep the code but free the space, run
this from the project root:

```bash
rm -rf backend/instance backend/.env backend/.venv \
  frontend/node_modules frontend/.svelte-kit frontend/build dist build
```

The tools also keep caches outside the repository. Other projects may use these caches too, so
removing them is optional:

| Tool | Cache | How to remove it |
|---|---|---|
| PyInstaller | macOS: `~/Library/Application Support/pyinstaller`; Windows: `%LOCALAPPDATA%\pyinstaller` | delete the folder |
| uv | downloaded packages | `uv cache clean` |
| npm | downloaded packages | `npm cache clean --force` |

### Docker

From the project root, run:

```bash
docker compose down --volumes --rmi local
```

This removes the container, the `app-data` volume with the database, and the image that Compose
built. To also free the space used by the base images and the build cache, run:

```bash
docker image rm node:24-alpine python:3.12-slim ghcr.io/astral-sh/uv:0.11.21
docker builder prune
```

Finally, delete the repository folder.

## How the app works

The backend is a Flask application that serves the JSON API under `/api` and the compiled
SvelteKit frontend. Data is stored in SQLite, and the database schema is managed with Alembic
migrations. The three ways of running it differ only in what surrounds that application:

| | Server | Database | Frontend |
|---|---|---|---|
| From source (`bin/start`) | Flask development server | `backend/instance/` | Vite development server, port 5173 |
| Docker | gunicorn | `app-data` volume | build served by Flask |
| Desktop | waitress, on `127.0.0.1` only | your user data folder | build bundled in the executable, served by Flask |

The desktop app is built with [PyInstaller](https://pyinstaller.org/), which packages Python,
the backend, the migrations and the compiled frontend into one folder: the `.app` on macOS, the
folder the installer copies on Windows. When it starts, it:

1. makes sure it is the only copy running; if another copy is running, it brings that copy's
   window to the front (and warns if that copy is an older version) and exits;
2. applies any pending migrations to the database in your data folder;
3. starts the server in a background thread, on port 47615, or on any free port if 47615 is
   taken;
4. opens the window on that server and waits until you close it, then stops the server.

The window comes from [pywebview](https://pywebview.flowrl.com/), which shows a web page with
the engine the operating system already has: WKWebView (the engine of Safari) on macOS and
WebView2 (the engine of Edge) on Windows. So the app does not bundle a browser, and the frontend
is the same one that Docker and the development setup serve. The window keeps its storage
between launches, which is how it remembers the theme and the closed update banner. That storage
belongs to the address of the page, port included, which is why the server prefers the same port
every time.

The desktop app also turns on the update check (`UPDATE_CHECK`). `GET /api/version` then adds
the latest release on GitHub to its answer, and the frontend shows the banner when that release
is newer. GitHub is asked in the background, at most every 6 hours (every minute after a failure,
such as being offline), and an API request waits for it at most 2 seconds. When the answer comes
later, the page still gets it: it asks again after a few seconds, every 15 minutes, when you come
back to the window and when the computer goes back online. The code is in
`backend/src/asta_la_vista/adapters/releases.py` and `frontend/src/lib/versionWatcher.ts`.

The code is in `backend/src/asta_la_vista/entrypoints/desktop/`, and the build recipe is in
`desktop/asta-la-vista.spec`.

## Application flow

1. Open the Listone section and import the CSV or XLSX file with the players. The file from
   [fantacalcio.it](https://www.fantacalcio.it/quotazioni-fantacalcio) works best: see
   [Preparing the player list](#preparing-the-player-list).
2. Create one or more strategies: define global tiers with their own order and colours, and
   assign players to the tiers for each role. For each player you can optionally add a note and
   a maximum spending percentage. During the auction, the percentage is converted into credits
   using the auction's starting budget.
3. Create the auction, with credits, slots, participants and, optionally, a strategy.
4. Start the auction and record each purchase. The screen updates every participant's remaining
   credits, maximum bid, slots and squad. The player panel lets you filter by role, sort by tier
   or price, and pick the next player to call.
5. When the auction ends, download the report in HTML format. It opens in any browser.

## Releasing a new version

The version number lives in one place: `version` in `backend/pyproject.toml`. The app reads it
at runtime and shows it in the page footer.

While you work, describe each user-visible change under `## [Unreleased]` in
[CHANGELOG.md](CHANGELOG.md). To release, turn that heading into the new version and date
(for example `## [0.2.0] - 2026-11-20`), add an empty `## [Unreleased]` above it, update the
links at the bottom of the file, then:

```bash
./bin/release-notes 0.2.0  # preview the release notes
cd backend
uv version --bump minor   # or patch / major: updates pyproject.toml and uv.lock
cd ..
git commit -am "release 0.2.0"
git tag v0.2.0
git push origin main v0.2.0
```

Before tagging, build the app (`./bin/build-desktop`), open it with a separate data folder
(`ASTA_LA_VISTA_DATA_DIR`) and check what the automatic tests cannot see:

- the window opens on the app, and the theme you choose is still there after reopening it;
- importing the listone works, and so do the strategy export and the final report download:
  each asks where to save the file, and the app stays on screen;
- **File → Apri cartella dati** opens the data folder;
- opening the app a second time brings the window to the front;
- closing the window asks for confirmation, then quits the app.

Windows needs the same check, on the installer. Start the [Release
workflow](.github/workflows/release.yml) by hand on your branch, from **Actions → Release → Run
workflow** or with `gh workflow run release.yml --ref <branch>`: it builds and tests both apps
without publishing anything. Then download `desktop-windows` from the run's page.

Pushing the tag starts the [Release workflow](.github/workflows/release.yml). It:

1. checks that the tag matches the version in `pyproject.toml`, and that `CHANGELOG.md` has a
   section for it;
2. builds the app on Windows and on macOS, and the installer on Windows;
3. installs the Windows app with that installer, then smoke-tests each build;
4. publishes a GitHub Release with both files, using that `CHANGELOG.md` section as its notes.

Once it is published, the desktop apps already installed show the new-version banner.

The users' databases must survive every update, so:

- never modify a migration that has already been released: add a new one instead;
- make sure every migration works on existing data, not just on an empty database.

## Checks

Run the backend tests:

```bash
cd backend
uv run --group desktop pytest
```

The desktop launcher tests need the `desktop` dependency group: without it they are skipped.

Check style and static errors:

```bash
uv run ruff check .
uv run ruff format --check .
```

Check the frontend:

```bash
cd frontend
npm run check
npm run lint
npm run build
```
