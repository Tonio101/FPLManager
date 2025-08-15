#!/usr/bin/env python3

import argparse
import heapq
import json
import os
import sys

from gspread.cell import Cell

from fpl_player import FPLPlayer
from fpl_session import FPLSession
from gcp_pubsub import GcpPubSubClient
from google_sheets import GoogleSheets
from heapnode import Node
from logger import Logger

log = Logger.getInstance().getLogger()

# Debug flag to avoid writing to Google sheets for dev.
UPDATE_GOOGLE_SHEETS = True


def update_google_gameweek_sheet(gameweek, player_map, gsheets):
    """
    Update Head-to-Head player points on Google Sheets.
    """
    log.info(f"Updating gameweek {gameweek} points")

    player_cells = []
    for player in player_map.values():
        pname = player.get_name()
        gw_points = player.get_points(week=gameweek)
        cell = gsheets.search_player(pname)
        log.info(f"{pname}: {gw_points}")

        player_cells.append(
            Cell(row=cell.row, col=cell.col + gameweek, value=gw_points)
        )

    if UPDATE_GOOGLE_SHEETS:
        gsheets.update_players_score(player_cells)
    else:
        for cell in player_cells:
            log.info(cell)

    return True


def get_player_rank_heap(player_map):
    """
    Create a min-heap of players for ranking.
    """
    heap = []
    for player in player_map.values():
        heapq.heappush(heap, Node(player))
    return heap


def create_players(h2h_league_fixtures):
    """
    Create Head-to-Head league players from fixtures.
    """
    player_map = {}

    for week, fixtures in h2h_league_fixtures.items():
        for fixture in fixtures:
            e1_id = fixture.get("entry_1_entry") or "AVERAGE"
            e2_id = fixture.get("entry_2_entry") or "AVERAGE"

            if e1_id not in player_map:
                player_map[e1_id] = FPLPlayer(
                    id=e1_id,
                    name=fixture["entry_1_player_name"],
                    team_name=fixture["entry_1_name"],
                )

            if e2_id not in player_map:
                player_map[e2_id] = FPLPlayer(
                    id=e2_id,
                    name=fixture["entry_2_player_name"],
                    team_name=fixture["entry_2_name"],
                )

            player_map[e1_id].populate_player_stats(week, fixture, "entry_1")
            player_map[e2_id].populate_player_stats(week, fixture, "entry_2")

    return player_map


def should_update(fpl_session):
    """
    Determine whether Google Sheets should be updated for this gameweek.
    """
    if fpl_session.has_gameweek_been_updated():
        log.info(
            f"Gameweek points and rank already updated for gameweek: {fpl_session.get_current_gameweek()}"
        )
        return False

    if not fpl_session.is_current_gameweek_completed():
        log.info(
            f"Gameweek {fpl_session.get_current_gameweek()} data is not checked yet."
        )
        return False

    return True


def main(argv):
    parser = argparse.ArgumentParser(
        usage=f"{__file__} --config <file>",
        description="Fantasy Premier League Manager",
    )
    parser.add_argument("-c", "--config", help="Config file", required=True)
    parser.add_argument(
        "-g", "--gameweek", help="Update gameweek points", action="store_true"
    )
    parser.add_argument(
        "-r", "--rank", help="Update rank standings", action="store_true"
    )
    parser.add_argument(
        "-p", "--playerconfig", help="Player configuration", action="store_true"
    )
    parser.add_argument("-d", "--debug", help="Debug", action="store_true")
    parser.set_defaults(gameweek=False, rank=False, playerconfig=False, debug=False)

    args = parser.parse_args(argv[1:])

    if args.debug:
        Logger.getInstance().enableDebug()

    with open(args.config, encoding="UTF-8") as file:
        data = json.load(file)

    creds_file = data["creds_file"]
    gsheets_fname = data["google_sheets_file_name"]

    fpl_session = FPLSession(
        h2h_league_id=data["h2h_league_id"], gameweeks_db=data["gameweekdb_path"]
    )

    if not should_update(fpl_session):
        log.info("No update needed. Exiting...")
        sys.exit(0)

    log.info("Current gameweek data is checked, updating Google Sheets")
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = creds_file

    gsheets = GoogleSheets(creds_fname=creds_file, fname=gsheets_fname)
    pubsub_client = GcpPubSubClient(
        project_id=data["gcp"]["pubsub"]["project_id"],
        topic_id=data["gcp"]["pubsub"]["topic_id"],
    )

    h2h_league, h2h_league_fixtures = fpl_session.fpl_get_h2h_league_fixtures()
    log.info(f"{'Fantasy Premier League':30}: {h2h_league}")

    player_map = create_players(h2h_league_fixtures)

    log.info(f"Number of players: {len(player_map)}")
    for player in player_map.values():
        log.info(f"{player.get_team_name()},{player.get_name()}")

    gameweek_updated = False
    gameweek_rank_updated = False

    if args.gameweek:
        gameweek_updated = update_google_gameweek_sheet(
            fpl_session.get_current_gameweek(), player_map, gsheets
        )

    if args.rank:
        gsheets.update_worksheet_num(num=1)
        log.info(f"\n\nUpdating player rank {fpl_session.get_current_gameweek()}")
        heap = get_player_rank_heap(player_map)
        gsheets.update_rank_table(heap=heap)
        pubsub_client.publish(fpl_session, heap)
        gameweek_rank_updated = True

    if gameweek_updated and gameweek_rank_updated:
        log.info(
            f"Gameweek {fpl_session.get_current_gameweek()} points and rank successfully updated."
        )
        if UPDATE_GOOGLE_SHEETS:
            fpl_session.marked_gameweek_updated()


if __name__ == "__main__":
    main(sys.argv)
