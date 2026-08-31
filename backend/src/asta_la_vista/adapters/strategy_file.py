import csv
import io
import re
from collections.abc import Iterable
from dataclasses import dataclass

from asta_la_vista.domain.commands import TierImportRow
from asta_la_vista.exceptions import ValidationError

# The neutral contract this feature owns. Any source platform (e.g. a fantasy
# football guide site) must be converted to this shape by a separate script
# before it reaches asta-la-vista — this module has no knowledge of any
# external platform's own export format.
REQUIRED_COLUMNS = ("Nome", "Fascia", "MaxPrezzo%", "Note")
# The export always writes the tier colour so a round trip keeps it, but files
# prepared by hand may leave the column out.
COLOR_COLUMN = "Colore"
EXPORT_COLUMNS = ("Nome", "Fascia", COLOR_COLUMN, "MaxPrezzo%", "Note")
HEX_COLOR = re.compile(r"^#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{6})$")


@dataclass(frozen=True)
class StrategyExportRow:
    player_name: str
    tier_name: str
    tier_color: str | None
    maximum_price_percentage: float | None
    note: str


@dataclass(frozen=True)
class StrategyExport:
    name: str
    rows: tuple[StrategyExportRow, ...]


def parse_strategy_import_file(content: bytes, filename: str) -> tuple[TierImportRow, ...]:
    if not filename.lower().endswith(".csv"):
        raise ValidationError("Only .csv files are supported")
    try:
        text = content.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise ValidationError("The CSV file must use UTF-8 encoding") from exc
    try:
        # Only the delimiter is sniffed: letting the Sniffer pick the whole
        # dialect made it guess quoting rules that mangle quoted notes, which
        # is exactly what our own export writes.
        delimiter = csv.Sniffer().sniff(text[:4096], delimiters=",;").delimiter
    except csv.Error:
        delimiter = ","
    rows = csv.reader(io.StringIO(text), delimiter=delimiter)
    headers, data = _find_headers(rows)
    return _rows_to_entries(headers, data)


def render_strategy_export_file(rows: Iterable[StrategyExportRow]) -> bytes:
    output = io.StringIO(newline="")
    writer = csv.writer(output)
    writer.writerow(EXPORT_COLUMNS)
    for row in rows:
        writer.writerow(
            (
                row.player_name,
                row.tier_name,
                row.tier_color or "",
                row.maximum_price_percentage if row.maximum_price_percentage is not None else "",
                row.note,
            )
        )
    return output.getvalue().encode("utf-8-sig")


def _find_headers(rows: Iterable[Iterable[object]]) -> tuple[list[str], Iterable[Iterable[object]]]:
    iterator = iter(rows)
    for row_number, row in enumerate(iterator, start=1):
        values = [str(value).strip() if value is not None else "" for value in row]
        if all(column in values for column in REQUIRED_COLUMNS):
            return values, iterator
        if row_number == 10:
            break
    raise ValidationError("Required columns Nome, Fascia, MaxPrezzo% and Note were not found")


def _rows_to_entries(
    headers: list[str], rows: Iterable[Iterable[object]]
) -> tuple[TierImportRow, ...]:
    positions = {column: headers.index(column) for column in REQUIRED_COLUMNS}
    if COLOR_COLUMN in headers:
        positions[COLOR_COLUMN] = headers.index(COLOR_COLUMN)

    def cell(values: list[object], column: str) -> str:
        position = positions.get(column)
        if position is None or position >= len(values) or values[position] is None:
            return ""
        return str(values[position]).strip()

    entries: list[TierImportRow] = []
    for row in rows:
        values = list(row)
        if not any(value is not None and str(value).strip() for value in values):
            continue
        name = cell(values, "Nome")
        if not name:
            raise ValidationError("A row is missing the player name")
        entries.append(
            TierImportRow(
                name=name,
                fascia=cell(values, "Fascia"),
                note=cell(values, "Note"),
                maximum_price_percentage=_parse_percentage(cell(values, "MaxPrezzo%")),
                colore=_parse_color(cell(values, COLOR_COLUMN)),
            )
        )
    if not entries:
        raise ValidationError("The tier list is empty")
    return tuple(entries)


def _parse_percentage(value: str) -> float | None:
    if not value:
        return None
    try:
        percentage = round(float(value), 1)
    except ValueError as exc:
        raise ValidationError("MaxPrezzo% must be a number") from exc
    # A price cap of 0% isn't meaningful; treat it the same as "not set".
    return percentage if percentage > 0 else None


def _parse_color(value: str) -> str:
    if not value:
        return ""
    if not HEX_COLOR.match(value):
        raise ValidationError("Colore must be a hex color like #ef4444")
    return value.lower()
