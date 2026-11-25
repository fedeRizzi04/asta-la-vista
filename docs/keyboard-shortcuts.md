# Keyboard shortcuts

During an auction the bidding moves fast, and reaching for the mouse costs seconds. Asta la Vista
can be driven almost entirely from the keyboard: this page explains how.

Press `?` on any page to see the shortcuts that work on that page (there is no button for it,
only the key). Hovering over a button or a field also shows its key in the tooltip.

- [The words used here](#the-words-used-here)
- [Buying a player with the keyboard only](#buying-a-player-with-the-keyboard-only)
- [All the shortcuts of the auction page](#all-the-shortcuts-of-the-auction-page)
- [The three ways to undo](#the-three-ways-to-undo)
- [The strategy page](#the-strategy-page)
- [The symbols on the keys](#the-symbols-on-the-keys)
- [Good to know](#good-to-know)

## The words used here

The **call** is the player being auctioned right now. When you search for a player and choose one,
the player is "called": their name, role, club, tier and maximum price appear in the **call bar**,
the bar that stays at the top of an auction while you scroll. It holds:

- the search field (**Search by player or club**);
- the called player;
- the **Winner** field;
- the **Price** field;
- the **Record** button, which records the purchase.

Calling a player does not record anything. You record the purchase later, when the bidding ends and
you know who won and at what price.

## Buying a player with the keyboard only

This is the whole sequence for one player, with the macOS keys. On Windows and Linux, read `⌘` as
`Ctrl`.

1. Press `⌘K` (or `/`). The cursor goes to the search field.
2. Type a few letters of the name (or of the club). A list of players that can still be bought
   appears.
3. Move through the list with `↑` and `↓`, and press `return` to call the highlighted player. The
   first one of the list is already highlighted.
4. When the bidding ends, press `⌘ return`. The cursor goes to the **Winner** field.
5. Type the first letters of the participant's name and press `return` to choose the highlighted
   one. The cursor goes to the **Price** field.
6. Type the price and press `return`. The purchase is recorded and the call bar is emptied. The
   cursor is no longer in a text field (it rests on the call bar), so `P` `D` `C` `A`, `?` and
   `⌥1` `⌥2` work at once: you may be the one calling the next player and need the strategy
   first. For the next player press `⌘K` or `/` again, or `tab`, which goes to the search field.
   Screen readers announce the purchase.

If you make a mistake before step 6, see [the three ways to undo](#the-three-ways-to-undo).

## All the shortcuts of the auction page

The "panel label" is the text you see in the `?` panel, here in English. With the app in Italian
the panel is in Italian too, and `return` (`Enter` on Windows and Linux) is written `invio`
(`Invio`). The macOS keys are the ones the panel shows on a Mac, the other column is for Windows
and Linux.

| Panel label | macOS | Windows / Linux | What it does |
|---|---|---|---|
| “Show keyboard shortcuts” | `?` | `?` | Opens the panel with the shortcuts of the current page. It works on every page. |
| “Search for a player” | `⌘K` or `/` | `Ctrl+K` or `/` | Moves the cursor to the search field and selects what is already there, so you can type over it. Only in a live auction. |
| “Go to the winner” | `⌘ return` | `Ctrl+Enter` | Moves the cursor to the **Winner** field. It needs a called player (without one, the field is disabled and nothing happens). It only moves the cursor: it does not choose anyone and does not record anything. |
| “Cancel the call” | `esc` | `Esc` | Removes the called player from the call bar and empties the search field, along with the winner and the price you may have typed. The cursor leaves the text fields, as after a purchase. Only in a live auction. It never touches a purchase that was already recorded. See [below](#the-three-ways-to-undo). |
| “Show goalkeepers”, “Show defenders”, “Show midfielders”, “Show forwards” | `P` `D` `C` `A` | `P` `D` `C` `A` | Shows the tiers or the free players of one role (one role at a time). |
| “Tiers view” | `⌥1` | `Alt+1` | Shows the tiers. Once the auction has started. It works from a field too, and types nothing in it. |
| “Free players view” | `⌥2` | `Alt+2` | Shows the free players. Once the auction has started. It works from a field too, and types nothing in it. |
| “Open or close the purchase registry” | `⌘J` | `Ctrl+J` | Opens the purchase registry in the side panel, or closes it if it is open. Once the auction has started. |
| “Undo the last purchase” | `⌘Z` | `Ctrl+Z` | Asks you to confirm, then cancels the most recent purchase and gives the credits back. Only in a live auction. See [below](#the-three-ways-to-undo). |

Some keys have no line in the panel because they belong to a field, and only work inside it:

| Where | Keys | What they do |
|---|---|---|
| The search field | `↑` `↓` | Move through the results (the first press opens the list if it was closed). |
| The search field | `return` | Calls the highlighted player. |
| The search field | `tab` | When the list is open and something is typed, it does the same as `return`. |
| The **Winner** field | `↑` `↓` | Move through the participants. The list opens as soon as the cursor is in the field. |
| The **Winner** field | `return` or `tab` | Chooses the highlighted participant and moves the cursor to the price. |
| The **Price** field | `return` | Records the purchase. It needs a participant and a price. |
| A search field, a winner field | `esc` | If the list of results is open, it closes the list and nothing else. The next `esc` is the one that removes the call. |
| The search field of **Free players** | `esc` | If the field has text, it empties the field and nothing else. From the empty field, `esc` removes the call. |
| The tabs (roles, **Tiers** and **Free players**) | `←` `→`, `Home` `End` | Move to another tab and show it. |
| A **⋯** menu | `↑` `↓`, `esc` | Move through the items, close the menu. |

A few more things happen on their own:

- Calling a player of another role switches the lists to that role.
- A team whose slots for the called player's role are already full is shown dimmed in the list of
  winners. You can still choose it.

## The three ways to undo

They look alike, so here is what each one does and does not do.

**“Cancel the call”, `esc`: you called the wrong player.**
It removes the player from the call bar and empties the search, the winner and the price. Nothing
was recorded yet, so there is nothing to give back. It never touches a purchase that is already in
the registry. When the list of results is open, the first `esc` only closes the list, and the
second one removes the call. After it the cursor leaves the text fields, as after a purchase, so
the keys of the page work at once: press `⌘K` or `/` to go back to the search.

**“Undo the last purchase”, `⌘Z`: you recorded a purchase you did not want.**
It does not act at once: a window asks you to confirm, naming the player, the participant and the
price. The cursor starts on **Keep purchase**, so pressing `return` by mistake changes nothing. Only
**Cancel purchase** cancels the purchase, and the credits become available again. It always
refers to the most recent purchase of the whole auction. To cancel an older one, or to correct a
price or a winner, use the registry (`⌘J`).

**`⌘Z` while you are typing: it undoes the typing.**
In a field that contains text (the search, the winner, the price) `⌘Z` is left to the browser, which
undoes what you typed, as everywhere else. The purchase is not touched. The shortcut of the
auction works from an empty field, or when the cursor is not in a field.

## The strategy page

On the strategy page the keys work on players and tiers. Click on a player to open their details
(tier, maximum price and note), or use the keyboard.

**Moving around the list**

Each list of players (the **No tier** one on the left and every tier) is one stop for the
`tab` key. Once inside:

| Keys | What they do |
|---|---|
| `↑` `↓` | Move to the previous or next player of the same list, and select only that one. |
| `Home` `End` | The same, to the first or the last player of the list. |
| `⇧` with `↑` `↓` `Home` `End` | Extend the selection from the player you started from. |
| `⌘` or `Ctrl` with `↑` `↓` `Home` `End` | Move without changing the selection. |
| `Space` | Add or remove the player with the cursor to or from the selection. |
| `return` | Select that player alone and open their details. The cursor goes to the **Tier** field. |

With the mouse: a click opens the details of the player, `⇧` and a click selects everything
in between, `⌘` (`Ctrl` on Windows) and a click adds or removes one player.

**Moving players between tiers**

| Panel label | Keys | What they do |
|---|---|---|
| ‘Move to “name”’ | `1` to `9` | Moves the selected players to the first, second... ninth tier, in the order they are shown, from left to right. With nothing selected it moves the player with the cursor, if you reached it with the keyboard. There is no key for the tenth tier and beyond: use the buttons that appear above the lists when something is selected, or drag. |
| “Remove from tier” | `0` | Takes the same players out of their tier, back to **No tier**. |
| “Clear selection” | `esc` | Clears the selection. It appears in the panel only while something is selected. |

`esc` has three more jobs here: while you drag a player it cancels the drag; with the details of a
player open it closes them (the selection stays, and a second `esc` clears it); in the search field
above the list on the left, if the field has text, it empties the field and nothing else (from the
empty field, `esc` clears the selection).

**Tiers and names**

- To reorder the tiers, press `tab` until the grip (⠿) of a tier has the cursor, then `←` or `→`
  moves the tier by one place. You can also drag the grip.
- In the name of a strategy or of a tier, `return` confirms the name.
- The tabs of the roles work with `←` `→` and `Home` `End`, as on the auction page.

## The symbols on the keys

| What you see | Key | Notes |
|---|---|---|
| `⌘` | Command | On Windows and Linux the same shortcuts use `Ctrl`. |
| `⌥` | Option | `Alt` on Windows and Linux. |
| `⇧` | Shift | `Shift` on Windows and Linux. |
| `esc` | Escape | `Esc` on Windows and Linux. |
| `return` | Return, or Enter | The big key at the end of the row of letters. On Windows and Linux it is written `Enter`. On a keyboard with a numeric keypad, the `Enter` of the keypad works too. |
| `↑` `↓` `←` `→` | The arrow keys | |
| `tab` | Tab | |

On a Mac the symbols are written next to each other (`⌘K`), and a word is separated by a space
(`⌘ return`). On Windows and Linux the keys are joined with `+` (`Ctrl+Enter`).

## Good to know

**When the shortcuts are ignored**

- **While you type in a field** (a search, the winner, the price, a name, a note, a drop-down), the
  keys that do not need `⌘` or `Ctrl` are ignored, so that you can write: `/`, `?`, `P` `D` `C` `A`,
  `1` to `9`, `0`. The shortcuts with `⌘` or `Ctrl`, those with `⌥` (`Alt`), and `esc`, still work:
  you can switch between the tiers and the free players from the search, the winner or the price.
  `⌥1` types « on an Italian Mac keyboard, and the shortcut keeps it from being typed.
- **While a window is open** (the registry panel, a confirmation, the panel of the shortcuts) all
  the shortcuts are ignored, except `⌘J`, which closes the registry. `esc` closes the window on
  top, and only that one.
- Holding a key down does not repeat the shortcut, and nothing happens while you are composing
  accented characters or text with an input method.
- A shortcut that is not available at the moment (for instance `⌘Z` in a draft or a finished
  auction, or `⌘Z` in a live one that has no purchases yet) does nothing. The ones that depend on
  the state of the auction are not even listed in the panel.

**Keyboard layouts**

- The keys with a letter or a digit (`K`, `J`, `Z`, `P` `D` `C` `A`, `1` to `9`, `0`) are
  recognised by the character the key types, and only when `Shift` is not pressed. So on a layout
  where a digit needs `Shift` (the French one, for example) the digits of the top row do not
  trigger `1` to `9`; the digits of the numeric keypad should.
- `/` and `?` work whether or not your layout needs `Shift` to type them.
- `⌥1` and `⌥2` follow the position of the key and not the character, because `⌥` changes the
  characters on a Mac. They are the keys of the digits 1 and 2 on the top row. On Windows, `AltGr`
  is read as `Ctrl+Alt`, so it never triggers a shortcut by accident.

**The browser's own shortcuts**

`⌘K` and `⌘J` (`Ctrl+K` and `Ctrl+J` on Windows and Linux) are also used by some browsers, for
example for the search bar and for the list of downloads. When Asta la Vista handles one of its own
shortcuts, it asks the browser not to do its own action. When the shortcut is not available (for
instance `⌘K` on the strategy page, or `⌘J` in a draft auction), nothing is intercepted and the
browser does what it always does. Whether a given browser lets a page take over a combination is
the browser's decision.

Only macOS has been tried so far, in Chrome. The Windows and Linux column is written from the
code and has not been tested.
