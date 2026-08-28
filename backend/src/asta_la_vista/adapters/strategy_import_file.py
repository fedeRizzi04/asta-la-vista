import csv
import io
from collections.abc import Iterable

from asta_la_vista.domain.commands import TierImportRow
from asta_la_vista.exceptions import ValidationError

# The neutral contract this feature owns. Any source platform (e.g. a fantasy
# football guide site) must be converted to this shape by a separate script
# before it reaches asta-la-vista — this module has no knowledge of any
# external platform's own export format.
COLUMNS = ("Nome", "Fascia", "MaxPrezzo%", "Note")


def parse_strategy_import_file(content: bytes, filename: str) -> tuple[TierImportRow, ...]:
    if not filename.lower().endswith(".csv"):
        raise ValidationError("Only .csv files are supported")
    try:
        text = content.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise ValidationError("The CSV file must use UTF-8 encoding") from exc
    try:
        dialect = csv.Sniffer().sniff(text[:4096], delimiters=",;")
    except csv.Error:
        dialect = csv.excel
    rows = csv.reader(io.StringIO(text), dialect)
    headers, data = _find_headers(rows)
    return _rows_to_entries(headers, data)


def _find_headers(rows: Iterable[Iterable[object]]) -> tuple[list[str], Iterable[Iterable[object]]]:
    iterator = iter(rows)
    for row_number, row in enumerate(iterator, start=1):
        values = [str(value).strip() if value is not None else "" for value in row]
        if all(column in values for column in COLUMNS):
            return values, iterator
        if row_number == 10:
            break
    raise ValidationError("Required columns Nome, Fascia, MaxPrezzo% and Note were not found")


def _rows_to_entries(
    headers: list[str], rows: Iterable[Iterable[object]]
) -> tuple[TierImportRow, ...]:
    positions = {column: headers.index(column) for column in COLUMNS}

    def cell(values: list[object], column: str) -> str:
        position = positions[column]
        if position >= len(values) or values[position] is None:
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
