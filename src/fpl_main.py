#!/usr/bin/python3

import heapq
import sys

from models.fpl_player import FPLPlayer
from models.fpl_session import FPLSession
from models.google_sheets import GoogleSheets
from models.heapnode import Node


def update_google_gameweek_sheet(gameweek, player_map, gsheets):
    print("Updating gameweek {0} points".format(gameweek))
    for _, player in player_map.items():
        pname = player.get_name()
        ppoints = player.get_points(week=gameweek)
        cell = gsheets.search_player(pname)
        print("{0}:{1}".format(pname, ppoints))
        gsheets.update_player_score(cell.row, cell.col + gameweek, ppoints)


def update_google_rank_sheet(player_map, gsheets):
    heap = []

    for _, player in player_map.items():
        cell = gsheets.search_player(player.get_name())
        gsheets.update_player_score(cell.row, cell.col + 1, player.get_total_win())
        gsheets.update_player_score(cell.row, cell.col + 2, player.get_total_loss())
        gsheets.update_player_score(cell.row, cell.col + 3, player.get_total_draw())
        gsheets.update_player_score(cell.row, cell.col + 4, player.get_total_h2h_points())

        heapq.heappush(heap, Node(player))

    print("Rank:")
    num = 1
    while heap:
        node = heapq.heappop(heap).val
        print("{0}: {1}".format(num, node.get_name()))
        cell = gsheets.search_player(node.get_name())
        gsheets.update_player_score(cell.row, cell.col + 5, num)
        gsheets.reset_row_highlight(cell.row)

        if num < 4:
            # Highlight the top 3
            gsheets.highlight_row(cell.row, "yellow")
        if not heap:
            # Highlight the last one (pays double)
            gsheets.highlight_row(cell.row, "red")

        num += 1

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
    # TODO add command line arguments
    creds_file = '/home/antonio/my-project-33107-c176b4ff01ad.json'
    gsheets_fname = 'Fantasy Premier League - 21/22'

    fpl_session = FPLSession()
    gsheets = GoogleSheets(creds_fname=creds_file, fname=gsheets_fname)

    h2h_league, h2h_league_fixtures = fpl_session.fpl_get_h2h_league_fixtures()
    print("%30s: %s\n" % ('Fantasy Premier League', h2h_league))

    player_map = create_players(h2h_league_fixtures)
    #print("Number of players: ", len(player_map))
    #for id, player in player_map.items():
    #    print(id, ":", player)

    update_google_gameweek_sheet(fpl_session.get_current_gameweek(),
                                 player_map, gsheets)
    # Update Rank Table
    gsheets.update_worksheet_num(num=2)
    update_google_rank_sheet(player_map, gsheets)


if __name__ == "__main__":
    main(sys.argv)
