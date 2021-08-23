import heapq
# import json
import sys

from models.fpl_player import FPLPlayer
from models.fpl_session import FPLSession
from models.google_sheets import GoogleSheets
from models.heapnode import Node


def get_list_of_players(fpl_session, h2h_league_fixtures, list_of_players):
    for h2h_fixture in h2h_league_fixtures:
        player_1 = FPLPlayer()
        player_1.populate_player_info(h2h_fixture, "entry_1")
        player_1.set_gameweek(gameweek=fpl_session.get_current_gameweek())

        player_2 = FPLPlayer()
        player_2.populate_player_info(h2h_fixture, "entry_2")
        player_2.set_gameweek(gameweek=fpl_session.get_current_gameweek())

        print('%32s VS %s' % (player_1, player_2))

        # print("{0}".format(json.dumps(h2h_fixture, indent=4)))
        list_of_players.append(player_1)
        list_of_players.append(player_2)


def update_google_gameweek_sheet(list_of_players, gsheets):
    for player in list_of_players:
        pname = player.get_name()
        cell = gsheets.search_player(pname)
        # print("Found {0} in [{1},{2}]".format(pname, cell.row, cell.col))
        gameweek = player.get_gameweek()
        print("Updating gameweek points for {0}".format(player.get_name()))
        gsheets.update_player_score(cell.row, cell.col + gameweek,
                                    player.get_points())


def update_google_rank_sheet(list_of_players, gsheets):
    heap = []

    for player in list_of_players:
        pname = player.get_name()
        cell = gsheets.search_player(pname)
        print("Found {0} in [{1},{2}]".format(pname, cell.row, cell.col))

        if player.get_win():
            gsheets.update_player_score(cell.row, cell.col + 1, player.get_win())
        elif player.get_loss():
            gsheets.update_player_score(cell.row, cell.col + 2, player.get_loss())
        elif player.get_draw():
            gsheets.update_player_score(cell.row, cell.col + 3, player.get_draw())

        gsheets.update_player_score(cell.row, cell.col + 4, player.get_total_points())
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
            # Highlight the last one (they pay double)
            gsheets.highlight_row(cell.row, "red")

        num += 1


def main(argv):
    # TODO add command line arguments
    creds_file = '/home/antonio/my-project-33107-c176b4ff01ad.json'
    gsheets_fname = 'Fantasy Premier League - 21/22'

    fpl_session = FPLSession()
    gsheets = GoogleSheets(creds_fname=creds_file, fname=gsheets_fname)

    h2h_league, h2h_league_fixtures = fpl_session.fpl_get_h2h_league_fixtures()
    print("%30s: %s\n" % ('Fantasy Premier League', h2h_league))

    list_of_players = []
    get_list_of_players(fpl_session, h2h_league_fixtures, list_of_players)
    update_google_gameweek_sheet(list_of_players, gsheets)
    # Update Win/Loss/Draw Table
    gsheets.update_worksheet_num(num=2)
    update_google_rank_sheet(list_of_players, gsheets)


if __name__ == "__main__":
    main(sys.argv)
