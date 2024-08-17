import heapq
from copy import deepcopy

import gspread
from gspread_formatting import CellFormat, Color, TextFormat
from gspread_formatting.batch_update_requests import format_cell_range
from oauth2client.service_account import ServiceAccountCredentials

from models.logger import Logger

SCOPE = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive",
]

log = Logger.getInstance().getLogger()


class GoogleSheets:
    """
    Google Sheets API object.
    """

    def __init__(self, creds_fname, fname, worksheet_num=0):
        creds = ServiceAccountCredentials.from_json_keyfile_name(creds_fname, SCOPE)
        client = gspread.authorize(creds)
        self.sheet = client.open(fname)
        self.sheet_instance = self.sheet.get_worksheet(worksheet_num)

    def search_player(self, name):
        return self.sheet_instance.find(name)

    def update_player_score(self, row, col, value):
        return self.sheet_instance.update_cell(row, col, value)

    def update_players_score(self, cell_list):
        self.sheet_instance.update_cells(cell_list)

    def update_worksheet_num(self, num):
        self.sheet_instance = self.sheet.get_worksheet(num)

    def update_rank_table(self, heap=[], start_cell="A2", data=[]):
        if len(data) != 0:
            self.sheet_instance.update(start_cell, data)
        elif len(heap) != 0:
            self.build_rank_table_data(heap)
            self.sheet_instance.update(start_cell, self.ranked_data)

    def build_rank_table_data(self, heap):
        self.heap = deepcopy(heap)
        self.ranked_data = []
        rank = 1

        while self.heap:
            player = heapq.heappop(self.heap).val

            log.info("{0}: {1}".format(rank, player.get_name()))
            self.ranked_data.append(
                [
                    player.get_team_name(),
                    player.get_name(),
                    player.get_total_win(),
                    player.get_total_loss(),
                    player.get_total_draw(),
                    player.get_total_h2h_points(),
                    rank,
                ]
            )
            rank += 1

    def reset_row_highlight(self, row):
        fmt = CellFormat(
            backgroundColor=Color(1, 1, 1),
            textFormat=TextFormat(bold=False, foregroundColor=Color(0, 0, 0)),
        )

        format_cell_range(self.sheet_instance, str(row), fmt)

    def highlight_row(self, row, row_color="white"):
        r_color = Color(1, 1, 1)  # Background color default is white
        text_color = Color(0, 0, 0)  # Text color default is black

        if "red" in row_color:
            r_color = Color(1, 0, 0)
            text_color = Color(1, 1, 1)
        elif "yellow" in row_color:
            r_color = Color(1, 1, 0)

        fmt = CellFormat(
            backgroundColor=r_color,
            textFormat=TextFormat(bold=True, foregroundColor=text_color)
            # horizontalAlignment='CENTER'
        )

        format_cell_range(self.sheet_instance, str(row), fmt)

    def highlight_cell(self, row, col, color_cell="white"):
        cell_color = None
        text_color = Color(0, 0, 0)

        if "yellow" == color_cell:
            cell_color = Color(1, 1, 0)
        else:
            cell_color = Color(1, 1, 1)

        fmt = CellFormat(
            backgroundColor=cell_color,
            textFormat=TextFormat(bold=False, foregroundColor=text_color),
        )

        cell_str = "{}:{}".format(row, col)
        format_cell_range(self.sheet_instance, cell_str, fmt)
