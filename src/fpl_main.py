#!/usr/bin/env python3

import argparse
import heapq
import json
import sys

from copy import deepcopy
from gspread.models import Cell
from models.logger import Logger
from models.fpl_player import FPLPlayer
from models.fpl_session import FPLSession
from models.google_sheets import GoogleSheets
from models.heapnode import Node
from models.sms_message import SmsNotifier
from models.gcp_pubsub import GcpPubSubClient

log = Logger.getInstance().getLogger()

# Debug flag to avoid writing to Googlse sheets for dev.
UPDATE_GOOGLE_SHEETS = True


def update_google_gameweek_sheet(gameweek, player_map, gsheets):
    """
    Update Head-to-Head player points on Google sheets.

    params:
        - gameweek - Current gameweek.
        - player_map - Head-to-Head player map.
        - gsheets - Google sheets instance.
    """
    log.info("Updating gameweek {0} points".format(gameweek))

    player_cells = []
    for _, player in player_map.items():
        pname = player.get_name()
        gw_points = player.get_points(week=gameweek)
        cell = gsheets.search_player(pname)
        log.info("{0}:{1}".format(pname, gw_points))
        player_cells.append(Cell(row=cell.row, col=cell.col + gameweek,
                            value=gw_points))

    if UPDATE_GOOGLE_SHEETS:
        gsheets.update_players_score(player_cells)

    return True


def get_player_rank_heap(player_map):
    heap = []
    for _, player in player_map.items():
        heapq.heappush(heap, Node(player))
    return heap

# def update_google_rank_sheet(player_map, gsheets):
#    """
#    Update Head-to-Head player rank on Google sheets.
#
#    params:
#        - player_map - Head-to-Head player map.
#        - gsheets - Google sheets instance.
#    """
#    heap = []
#    player_cell_map = dict()
#
#    player_cells = []
#    for _, player in player_map.items():
#        cell = gsheets.search_player(player.get_name())
#        player_cell_map[player.get_id()] = cell
#
#        player_cells.append(Cell(row=cell.row, col=cell.col + 1,
#                            value=player.get_total_win()))
#        player_cells.append(Cell(row=cell.row, col=cell.col + 2,
#                            value=player.get_total_loss()))
#        player_cells.append(Cell(row=cell.row, col=cell.col + 3,
#                            value=player.get_total_draw()))
#        player_cells.append(Cell(row=cell.row, col=cell.col + 4,
#                            value=player.get_total_h2h_points()))
#        heapq.heappush(heap, Node(player))
#
#    gsheets.update_players_score(player_cells)
#
#    player_cells = []
#    log.info("Rank:")
#    num = 1
#    while heap:
#        node = heapq.heappop(heap).val
#        log.info("{0}: {1}".format(num, node.get_name()))
#        cell = player_cell_map[node.get_id()]
#        player_cells.append(Cell(row=cell.row, col=cell.col + 5, value=num))
#        gsheets.reset_row_highlight(cell.row)
#
#        if num < 4:
#            # Highlight the top 3
#            gsheets.highlight_row(cell.row, "yellow")
#        if not heap:
#            # Highlight the last one (pays double)
#            gsheets.highlight_row(cell.row, "red")
#
#        num += 1
#
#    gsheets.update_players_score(player_cells)
#    return True


def create_players(h2h_league_fixtures):
    """
    Create Head-to-Head league players.

    params:
        - h2h_league_fixtures - Head-to-Head league fixture map.

    output:
        - player_map - Map containing the participating players.
    """
    player_map = dict()

    for week, fixtures in h2h_league_fixtures.items():
        for h2h_league_fixture in fixtures:
            e_1 = 'entry_1'
            e_2 = 'entry_2'
            entry_1_id = h2h_league_fixture[e_1 + '_entry']
            entry_2_id = h2h_league_fixture[e_2 + '_entry']

            # AVERAGE player is set to None
            if entry_1_id is None:
                entry_1_id = 'AVERAGE'
            elif entry_2_id is None:
                entry_2_id = 'AVERAGE'

            if entry_1_id not in player_map:
                player = \
                    FPLPlayer(id=entry_1_id,
                              name=h2h_league_fixture[e_1 + '_player_name'],
                              team_name=h2h_league_fixture[e_1 + '_name'])
                player_map[entry_1_id] = player
            if entry_2_id not in player_map:
                player = \
                    FPLPlayer(id=entry_2_id,
                              name=h2h_league_fixture[e_2 + '_player_name'],
                              team_name=h2h_league_fixture[e_2 + '_name'])
                player_map[entry_2_id] = player

            player_map[entry_1_id].populate_player_stats(
                week, h2h_league_fixture, e_1)
            player_map[entry_2_id].populate_player_stats(
                week, h2h_league_fixture, e_2)

    return player_map


def should_update(fpl_session):
    if fpl_session.has_gameweek_been_updated():
        log.info(
            ("Gameweek points and rank have alreaady been "
             "updated for gameweek: {0}").format(
                 fpl_session.get_current_gameweek()
             )
        )
        return False

    if not fpl_session.is_current_gameweek_completed():
        log.info(
            ("Gameweek {0} data is not checked yet.").format(
                fpl_session.get_current_gameweek())
        )
        return False

    return True


def main(argv):

    usage = ("{0} --config <file> ").format(__file__)
    description = 'Fantasy Premier League Manager'
    parser = argparse.ArgumentParser(usage=usage, description=description)
    parser.add_argument("-c", "--config", help="Config file",
                        required=True)
    parser.add_argument("-g", "--gameweek", help="Update gameweek points",
                        action='store_true', required=False)
    parser.add_argument("-r", "--rank", help="Update rank standings",
                        action='store_true', required=False)
    parser.add_argument("-p", "--playerconfig", help="Player configuration",
                        action='store_true', required=False)
    parser.add_argument("-d", "--debug", help="Debug", action='store_true',
                        required=False)
    parser.set_defaults(gameweek=False, rank=False, playerconfig=False,
                        debug=False)

    args = parser.parse_args()

    if args.debug:
        Logger.getInstance().enableDebug()

    with open(args.config, encoding='UTF-8') as file:
        data = json.load(file)

    creds_file = data['creds_file']
    gsheets_fname = data['google_sheets_file_name']

    fpl_session = FPLSession(h2h_league_id=data['h2h_league_id'],
                             gameweeks_db=data['gameweekdb_path'])

    if not should_update(fpl_session):
        sys.exit(0)

    log.info("Current gameweek data is checked, update Google sheets")

    gsheets = GoogleSheets(creds_fname=creds_file, fname=gsheets_fname)
    sms_notifier = SmsNotifier(data)
    pubsub_client = GcpPubSubClient(
        project_id=data['gcp']['pubsub']['project_id'],
        topic_id=data['gcp']['pubsub']['topic_id']
    )

    h2h_league, h2h_league_fixtures = fpl_session.fpl_get_h2h_league_fixtures()
    log.info("%30s: %s\n" % ('Fantasy Premier League', h2h_league))

    player_map = create_players(h2h_league_fixtures)

    log.debug("Number of players: {0}".format(len(player_map)))
    for player_id, player in player_map.items():
        log.debug("{0} : {1}".format(player_id, player))

    gameweek_updated = False
    gameweek_rank_updated = False

    if args.gameweek:
        gameweek_updated = update_google_gameweek_sheet(
            fpl_session.get_current_gameweek(), player_map, gsheets)
    # Update Rank Table
    if args.rank:
        gsheets.update_worksheet_num(num=2)

        log.info("Updating player rank {0}".format(
            fpl_session.get_current_gameweek()
        ))

        heap = get_player_rank_heap(player_map)

        gsheets.update_rank_table(heap=heap)
        sms_notifier.send(fpl_session, heap)
        #pubsub_client.publish(fpl_session, heap)

        # TODO - Handle error code
        gameweek_rank_updated = True

    if gameweek_updated and gameweek_rank_updated:
        log.info(
            ("Gameweek {0} points and "
             "rank successfully updated.").format(
                 fpl_session.get_current_gameweek()
            )
        )

        if UPDATE_GOOGLE_SHEETS:
            fpl_session.marked_gameweek_updated()


if __name__ == "__main__":
    main(sys.argv)
