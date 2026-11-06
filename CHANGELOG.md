# Changelog

All notable changes to Asta la Vista are listed here, newest first. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and versions follow
[Semantic Versioning](https://semver.org/).

The text under each version becomes the notes of its GitHub Release, so write it for the people
who use the app.

## [Unreleased]

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

[Unreleased]: https://github.com/fedeRizzi04/asta-la-vista/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/fedeRizzi04/asta-la-vista/releases/tag/v0.1.0
