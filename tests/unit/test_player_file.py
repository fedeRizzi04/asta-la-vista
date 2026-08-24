import csv
import io

import pytest
from openpyxl import Workbook

from asta_la_vista.adapters.player_file import parse_player_file
from asta_la_vista.domain.commands import PlayerRow
from asta_la_vista.exceptions import ValidationError


def test_parses_the_official_excel_columns_from_the_tutti_sheet():
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Tutti"
    sheet.append(["Quotazioni Fantacalcio", None, None, None, None])
    sheet.append(["Id", "R", "RM", "Nome", "Squadra", "Qt.A"])
    sheet.append([5841, "P", "Por", "Svilar", "Roma", 18])
    sheet.append([2764, "A", "Pc", "Martinez L.", "Inter", 35])
    content = io.BytesIO()
    workbook.save(content)

    players = parse_player_file(content.getvalue(), "players.xlsx")

    assert players == (
        PlayerRow("5841", "Svilar", "Roma", "P"),
        PlayerRow("2764", "Martinez L.", "Inter", "A"),
    )


def test_parses_comma_or_semicolon_separated_csv():
    content = io.StringIO()
    writer = csv.writer(content, delimiter=";")
    writer.writerow(["Id", "R", "Nome", "Squadra"])
    writer.writerow([5841, "P", "Svilar", "Roma"])

    players = parse_player_file(content.getvalue().encode(), "players.csv")

    assert players == (PlayerRow("5841", "Svilar", "Roma", "P"),)


def test_rejects_files_without_the_required_columns():
    with pytest.raises(ValidationError):
        parse_player_file(b"name,team\nPlayer,Team", "players.csv")
