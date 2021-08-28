#!/usr/bin/python3

import argparse
import heapq
import json
import sys

from gspread.models import Cell
from models.fpl_player import FPLPlayer
from models.fpl_session import FPLSession
from models.google_sheets import GoogleSheets
from models.heapnode import Node
from time import sleep


def update_google_gameweek_sheet(gameweek, player_map, gsheets):
    print("Updating gameweek {0} points".format(gameweek))

    player_cells = []
    for _, player in player_map.items():
        pname = player.get_name()
        gw_points = player.get_points(week=gameweek)
        cell = gsheets.search_player(pname)
        print("{0}:{1}".format(pname, gw_points))
        player_cells.append(Cell(row=cell.row, col=cell.col + gameweek, value=gw_points))
    
    gsheets.update_players_score(player_cells)


def update_google_rank_sheet(player_map, gsheets):
    heap = []
    player_cell_map = dict()

    player_cells = []
    for _, player in player_map.items():
        cell = gsheets.search_player(player.get_name())
        player_cell_map[player.get_id()] = cell

        player_cells.append(Cell(row=cell.row, col=cell.col + 1, value=player.get_total_win()))
        player_cells.append(Cell(row=cell.row, col=cell.col + 2, value=player.get_total_loss()))
        player_cells.append(Cell(row=cell.row, col=cell.col + 3, value=player.get_total_draw()))
        player_cells.append(Cell(row=cell.row, col=cell.col + 4, value=player.get_total_h2h_points()))
        heapq.heappush(heap, Node(player))

    gsheets.update_players_score(player_cells)
    # Google sheets API rate limit
    #sleep(60)

    player_cells = []
    print("Rank:")
    num = 1
    while heap:
        node = heapq.heappop(heap).val
        print("{0}: {1}".format(num, node.get_name()))
        cell = player_cell_map[node.get_id()]
        player_cells.append(Cell(row=cell.row, col=cell.col + 5, value=num))
        gsheets.reset_row_highlight(cell.row)

        if num < 4:
            # Highlight the top 3
            gsheets.highlight_row(cell.row, "yellow")
        if not heap:
            # Highlight the last one (pays double)
            gsheets.highlight_row(cell.row, "red")

        num += 1
    
    gsheets.update_players_score(player_cells)


def create_players(h2h_league_fixtures):
    player_map = dict()

    for week, fixtures in h2h_league_fixtures.items():
        for h2h_league_fixture in fixtures:
            e1 = 'entry_1'
            e2 = 'entry_2'
            entry_1_id = h2h_league_fixture[e1 + '_entry']
            entry_2_id = h2h_league_fixture[e2 + '_entry']

            # AVERAGE player is set to None
            if entry_1_id is None:
                entry_1_id = 'AVERAGE'
            elif entry_2_id is None:
                entry_2_id = 'AVERAGE'

            if entry_1_id not in player_map:
                player = FPLPlayer(id=entry_1_id,
                    name=h2h_league_fixture[e1 + '_player_name'],
                    team_name=h2h_league_fixture[e1 + '_name'])
                player_map[entry_1_id] = player
            if entry_2_id not in player_map:
                player = FPLPlayer(id=entry_2_id,
                    name=h2h_league_fixture[e2 + '_player_name'],
                    team_name=h2h_league_fixture[e2 + '_name'])
                player_map[entry_2_id] = player

            player_map[entry_1_id].populate_player_stats(week, h2h_league_fixture, e1)
            player_map[entry_2_id].populate_player_stats(week, h2h_league_fixture, e2)

    return player_map


def main(argv):

    usage = ("{0} --config <file> ").format(__file__)
    description = 'Fantasy Premier League Manager'
    parser = argparse.ArgumentParser(usage=usage, description=description)
    parser.add_argument("-c", "--config", help="Config file", required=True)
    parser.add_argument("-g", "--gameweek", help="Gameweek", action='store_true', required=False)
    parser.add_argument("-r", "--rank", help="Rank", action='store_true', required=False)
    parser.set_defaults(gameweek=False, rank=False)

    args = parser.parse_args()

    with open(args.config, encoding='UTF-8') as file:
        data = json.load(file)

    creds_file = data['creds_file']
    gsheets_fname = data['google_sheets_file_name']

    fpl_session = FPLSession()
    gsheets = GoogleSheets(creds_fname=creds_file, fname=gsheets_fname)

    h2h_league, h2h_league_fixtures = fpl_session.fpl_get_h2h_league_fixtures()
    print("%30s: %s\n" % ('Fantasy Premier League', h2h_league))

    player_map = create_players(h2h_league_fixtures)
    #print("Number of players: ", len(player_map))
    #for id, player in player_map.items():
    #    print(id, ":", player)

    if args.gameweek:
        update_google_gameweek_sheet(fpl_session.get_current_gameweek(),
                                     player_map, gsheets)
    # Update Rank Table
    if args.rank:
        gsheets.update_worksheet_num(num=2)
        update_google_rank_sheet(player_map, gsheets)


if __name__ == "__main__":
    main(sys.argv)
