# Changelog

All notable changes to Asta la Vista are listed here, newest first. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and versions follow
[Semantic Versioning](https://semver.org/).

The text under each version becomes the notes of its GitHub Release, so write it for the people
who use the app.

## [Unreleased]

### Added

- Press `?` to see the keyboard shortcuts available on the current page.
- A guide to the keyboard shortcuts, with a step-by-step purchase from the keyboard and the
  difference between dropping a call and undoing a purchase, in
  [docs/keyboard-shortcuts.md](https://github.com/fedeRizzi04/asta-la-vista/blob/main/docs/keyboard-shortcuts.md).

### Changed

- Asta la Vista has a new sticker-inspired look in both themes, with pastel role badges and
  bundled Bricolage Grotesque and Atkinson Hyperlegible fonts that work offline.
- Page headers are compact, so more of the screen goes to your data, and buttons, fields, role
  tabs and filters look and behave the same on every page. Role tabs can be switched with the
  arrow keys.
- Confirmations open as proper modal windows: Esc closes only the topmost one. When you confirm
  a deletion or a cancellation, the cursor starts on the safe choice (**Annulla**, or **Lascia
  stare**), so a stray Enter does not delete anything.
- The app remembers which panels you show or hide when you reload the page.
- The auction page is laid out as a control panel. The header stays on one line with the status
  and the actions (start, end, reopen, download the report). Below it come the teams, the call
  bar and the tiers or the free players, and the role and the view you chose are kept when you
  reload the page.
- The teams are on top of the auction page, side by side. **Rose** shows every roster (goalkeepers,
  defenders, midfielders and forwards) with the credits left and the maximum bid, and
  **Compatta** shows a bar of filled and empty slots for each role. Scroll the row with the arrows, hide it
  with **Squadre** (the same button brings it back), or click a team to see its whole roster,
  with prices and tiers, in a side panel.
- During an auction, the called player, the winner and the price are in one bar that stays at the
  top while you scroll, below the teams. Pick a player from the search (arrows and Enter) or
  with a click anywhere in the lists, without the page jumping, and fill in the winner (type the
  initials) and the price when the bidding ends: they always start empty.
- The auction player list is now the **Svincolati** view, one click away from the tiers. Filter by
  Mantra role, search by player or team, sort by quotation, tier or name, and choose whether to
  show the players already taken.
- During an auction, each tier shows the players left out of the total, and the players already
  taken stay in their place, crossed out, with who bought them and the price. Collapse a tier into
  a thin strip (the choice is remembered, and **Comprimi tutte** does it for all of them), or hide
  the taken players with **Nascondi presi**. One strategy at a time is shown, and **Fissa per
  l'asta** keeps working as before.
- The role shown in the tiers and in Svincolati is one at a time, goalkeepers first. Calling a
  player of another role switches to that role.
- The purchase registry opens in a side panel, from **Registro** or with `⌘J`. Search it, edit the
  winner and the price of a purchase (the cursor starts on the winner), or cancel a purchase after
  confirming. Esc closes the panel.
- **Annulla ultimo** (or `⌘Z`) cancels the most recent purchase, after asking you to confirm. A
  draft auction shows its setup instead of the call bar, and a finished one is read-only with a
  short summary, **Riapri asta** and **Scarica report** in the header.
- Keyboard shortcuts for the auction, listed with `?`: `⌘K` or `/` to search for a player,
  `⌘ invio` to go to the winner, `invio` in the price to register, Esc to drop the call, `P` `D`
  `C` `A` to switch role, `⌥1` and `⌥2` for the tiers and Svincolati (also while typing in a
  field), `⌘J` for the registry and `⌘Z` to undo the last purchase. A player can be called and
  registered with the keyboard alone. After a purchase, or after dropping the call with Esc, the
  cursor leaves the text fields, so `P` `D` `C` `A`, `?` and `⌥1` `⌥2` work at once; screen readers
  announce the purchase.
- The strategy page shows the players without a tier on the left and the tiers side by side on
  the right. Search the players, sort them by quotation, name or team, filter them by Mantra role
  and choose whether to show the ones already in a tier; inactive players stay visible and are
  flagged. Add a tier with **+ Nuova fascia**, rename it and change its colour right in its header,
  and reorder tiers by dragging the grip or with the left and right arrow keys.
- Drag players from the list to a tier, between tiers, or back to the list to take them out of
  their tier. Select several with `⇧` or `⌘` (or Space), then drag them together, press `1`-`9` to
  move them to that tier or `0` to take them out of it. Click a player to open its tier, maximum
  price and note: the price is also shown in credits, based on a reference budget you can change
  at the top (it is remembered and does not affect the strategy itself).
- The strategy name is edited in place and saves itself, like the rest of the page. Export and
  duplicate are in the **⋯** menu, and duplicating opens the copy.
- Creating a strategy opens it straight away. An empty strategy offers a set of default tiers
  (Top, Semitop, Terza fascia, Scommesse) or lets you create your own, and the strategies list has
  **Importa CSV** in a window, with the file format explained under **Formato CSV**. Each row has
  a **⋯** menu with export, duplicate and delete.
- The Listone filters by role with the counts in the tabs (**Tutti**, **P**, **D**, **C**, **A**),
  and the filters apply as soon as you change them or type in the search, with no button to press.
  The table header stays in view while you scroll, and you can sort by player, team or
  quotation. The import (CSV or XLSX) is under **Importa**, in a window, and the summary and the
  confirmation for a live auction work as before.
- The auctions list shows the auction in progress first, with **Riprendi**, and **Nuova asta**
  opens a window instead of a form that is always on the page.
- The home page shows the auction in progress, your first strategies and how many players each
  role has in the Listone, instead of the welcome banner.
- Accessibility pass on both themes: text fields in the dark theme have a clearly visible edge,
  secondary text on selected rows is readable, small controls are big enough to hit, tier names
  are headings, and with reduced motion enabled the transitions are turned off too.

### Fixed

- Notes, percentages and names typed on a strategy no longer risk being lost when you reload the
  page right away: pending changes are saved first, and two quick edits of the same player or tier
  are saved in order.
- Counts read correctly with one item ("1 acquisto", "1 fascia", "1 nuovo") instead of always using
  the plural.
- The confirmation shown when importing the Listone during a live auction, and the one for
  players missing from a strategy CSV, are now in Italian. Cancelling the first one no longer
  shows an error.
- In a narrow window the auction header wraps onto two rows instead of squeezing the title down to
  a few letters and splitting the status badge.
- Names are no longer cut down to a bare "…". Player surnames in the team rosters, fantasy team
  names, tier names and the strategy name take the room that prices and badges leave free: the
  rosters show about three teams at a time with room for long surnames, long team and tier names
  wrap onto a second line, the buyer's name gives way to the player's in the tiers, and the tier
  buttons of the strategy page go to a second row instead of shrinking. When a name is still too
  long, at least its first letters stay visible and the full name is in the tooltip. A long file
  name in the import windows no longer makes the window wider.
- The maximum price percentage of a player cannot go above 100%: a larger value, typed or
  pasted, is brought back to 100% before it is shown on the card or saved, and the credits follow.

## [0.4.1] - 2026-11-06

### Fixed

- The Windows installer no longer asks where to put the app: choosing a folder such as Program
  Files stopped the installation with "Errore 5: Accesso negato". The app now always goes in
  your user folder, and you can still pin its icon wherever you like.

## [0.4.0] - 2026-11-06

### Changed

- On Windows, the app now comes with an installer: it asks where to put the app, adds it to the
  Start menu (and to the desktop, if you want), and lets you uninstall it from **Settings →
  Apps**. To update, run the installer of the new version.
- The app opens faster on Windows, because it is no longer unpacked at every launch.
- If you used an earlier version on Windows, delete its `AstaLaVista-…-windows.exe` after
  installing this one: your data stays where it is.

## [0.3.0] - 2026-11-06

### Changed

- The desktop app opens in its own window instead of a browser tab, and shows in the Dock on
  macOS. Closing the window quits the app, after asking you to confirm.
- The icon in the system tray (Windows) and in the menu bar (macOS) is gone: **Apri cartella
  dati** is now in the window's **File** menu.
- Opening the app while it is already running brings its window to the front. If the copy that
  is running is an older version, the app tells you to close it first.
- Downloads, such as the final report, ask you where to save the file.
- The theme and the closed update banner were remembered by your browser: choose the theme again
  once, and the window remembers it from then on.
- On Windows, the window needs Microsoft Edge WebView2, which Windows 11 and an updated
  Windows 10 already have. If it is missing, the app tells you where to get it.

## [0.2.0] - 2026-11-06

### Added

- The app tells you when a new version is available: a banner under the header links to the
  download page. Close it and it stays hidden until the next version comes out.
- The update check is on by default in the desktop app only. It asks GitHub at most every few
  hours and stays silent when you are offline. Docker and source setups can turn it on with
  `UPDATE_CHECK=true`.

## [0.1.0] - 2026-11-06

First release, with a desktop app that needs neither Docker nor Python.

### Added

- Desktop app for Windows (x64) and macOS (Apple Silicon): download it, double-click it, and
  Asta la Vista opens in your browser.
- An icon in the system tray (Windows) or menu bar (macOS) to reopen the app, open the data
  folder, or quit.
- Your data is kept in your user folder and survives updates: each new version updates the
  database automatically when it starts.
- The app version is shown at the bottom of every page.
- Everything the app already did:
  - import the player list (Listone) from a `.csv` or `.xlsx` file;
  - strategies with custom tiers, notes and maximum spending percentages;
  - live Classic auctions with credits, slots and squads for every participant;
  - a final HTML report that opens in any browser;
  - a dark theme.

[Unreleased]: https://github.com/fedeRizzi04/asta-la-vista/compare/v0.4.1...HEAD
[0.4.1]: https://github.com/fedeRizzi04/asta-la-vista/compare/v0.4.0...v0.4.1
[0.4.0]: https://github.com/fedeRizzi04/asta-la-vista/compare/v0.3.0...v0.4.0
[0.3.0]: https://github.com/fedeRizzi04/asta-la-vista/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/fedeRizzi04/asta-la-vista/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/fedeRizzi04/asta-la-vista/releases/tag/v0.1.0
