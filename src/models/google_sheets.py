import gspread
import pandas as pd

from oauth2client.service_account import ServiceAccountCredentials
from gspread_formatting import *

SCOPE = ['https://spreadsheets.google.com/feeds',
         'https://www.googleapis.com/auth/drive']

class GoogleSheets():

    def __init__(self, creds_fname, fname, worksheet_num=0):
        creds = ServiceAccountCredentials.from_json_keyfile_name(creds_fname, SCOPE)
        client = gspread.authorize(creds)
        self.sheet = client.open(fname)
        self.sheet_instance = self.sheet.get_worksheet(worksheet_num)

    def search_player(self, name):
        return self.sheet_instance.find(name)

    def update_player_score(self, row, col, value):
        return self.sheet_instance.update_cell(row, col, value)

    def update_worksheet_num(self, num):
        self.sheet_instance = self.sheet.get_worksheet(num)

    def reset_row_highlight(self, row):
        fmt = cellFormat(
            backgroundColor=color(1, 1, 1),
            textFormat=textFormat(bold=False, foregroundColor=color(0, 0, 0))
        )

        format_cell_range(self.sheet_instance, str(row), fmt)


    def highlight_row(self, row, row_color="white"):
        r_color = color(1, 1, 1) # Background color default is white
        text_color = color(0, 0, 0) # Text color default is black

        if "red" in row_color:
            r_color = color(1, 0, 0)
            text_color = color(1, 1, 1)
        elif "yellow" in row_color:
            r_color = color(1, 1, 0)

        fmt = cellFormat(
            backgroundColor=r_color,
            textFormat=textFormat(bold=True, foregroundColor=text_color)
            #horizontalAlignment='CENTER'
        )

        format_cell_range(self.sheet_instance, str(row), fmt)
