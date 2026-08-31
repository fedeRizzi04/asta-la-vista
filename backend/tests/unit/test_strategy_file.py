import pytest

from asta_la_vista.adapters.strategy_file import (
    StrategyExportRow,
    parse_strategy_import_file,
    render_strategy_export_file,
)
from asta_la_vista.domain.commands import TierImportRow
from asta_la_vista.exceptions import ValidationError


def test_parses_tiered_and_note_only_rows():
    content = (
        b"Nome,Fascia,MaxPrezzo%,Note\n"
        b"Lautaro,Top,5.8,Rigorista\n"
        b"Some Backup,,,Da monitorare a fine mercato\n"
    )

    rows = parse_strategy_import_file(content, "fasce.csv")

    assert rows == (
        TierImportRow("Lautaro", "Top", "Rigorista", 5.8),
        TierImportRow("Some Backup", "", "Da monitorare a fine mercato", None),
    )


def test_accepts_semicolon_separated_csv():
    content = b"Nome;Fascia;MaxPrezzo%;Note\nSvilar;Top;;\n"

    rows = parse_strategy_import_file(content, "fasce.csv")

    assert rows == (TierImportRow("Svilar", "Top", "", None),)


def test_zero_maximum_price_percentage_is_treated_as_unset():
    content = b"Nome,Fascia,MaxPrezzo%,Note\nSvilar,Top,0,\n"

    rows = parse_strategy_import_file(content, "fasce.csv")

    assert rows[0].maximum_price_percentage is None


def test_rejects_files_without_the_required_columns():
    with pytest.raises(ValidationError):
        parse_strategy_import_file(b"Nome,Note\nSvilar,Titolare\n", "fasce.csv")


def test_rejects_a_row_without_a_player_name():
    with pytest.raises(ValidationError):
        parse_strategy_import_file(b"Nome,Fascia,MaxPrezzo%,Note\n,Top,,\n", "fasce.csv")


def test_rejects_non_csv_files():
    with pytest.raises(ValidationError):
        parse_strategy_import_file(b"irrelevant", "fasce.xlsx")


def test_rejects_an_invalid_maximum_price_percentage():
    with pytest.raises(ValidationError):
        parse_strategy_import_file(
            b"Nome,Fascia,MaxPrezzo%,Note\nSvilar,Top,invalid,\n", "fasce.csv"
        )


def test_the_color_column_is_optional():
    content = b"Nome,Fascia,MaxPrezzo%,Note\nSvilar,Top,,\n"

    rows = parse_strategy_import_file(content, "fasce.csv")

    assert rows == (TierImportRow("Svilar", "Top", "", None, ""),)


def test_reads_the_color_column_when_present_whatever_its_position():
    content = b"Colore,Nome,Fascia,MaxPrezzo%,Note\n#EF4444,Svilar,Top,,\n"

    rows = parse_strategy_import_file(content, "fasce.csv")

    assert rows == (TierImportRow("Svilar", "Top", "", None, "#ef4444"),)


def test_rejects_a_color_that_is_not_hexadecimal():
    content = b"Nome,Fascia,Colore,MaxPrezzo%,Note\nSvilar,Top,rosso,,\n"

    with pytest.raises(ValidationError, match="Colore"):
        parse_strategy_import_file(content, "fasce.csv")


def test_renders_an_import_compatible_utf8_csv_with_escaped_values():
    content = render_strategy_export_file(
        (
            StrategyExportRow("Martínez, L.", "Top", "#ef4444", None, 'Rigorista, detto "Toro"'),
            StrategyExportRow("Svilar", "", None, 3.2, "Da monitorare"),
        )
    )

    assert content.startswith(b"\xef\xbb\xbf")
    assert parse_strategy_import_file(content, "strategia.csv") == (
        TierImportRow("Martínez, L.", "Top", 'Rigorista, detto "Toro"', None, "#ef4444"),
        TierImportRow("Svilar", "", "Da monitorare", 3.2, ""),
    )
