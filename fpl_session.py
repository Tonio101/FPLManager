import asyncio
import os
import sys
from pathlib import Path

from fpl import FPL
from logger import Logger

log = Logger.getInstance().getLogger()


class FPLSession:
    """
    Wrapper class for an FPL session.
    """

    def __init__(self, h2h_league_id, gameweeks_db="gameweek.db"):
        self.fpl_session = None
        self.user = None
        self.h2h_league = None
        self.h2h_league_fixtures = None
        self.h2h_league_all_fixtures = []
        self.h2h_league_fixture_map = {}
        self.curr_gameweek = 0
        self.next_gameweek = 0
        self.h2h_league_id = h2h_league_id
        self.gameweeks_db = gameweeks_db
        self.fpl_fixtures_retrieve_method = 1
        self.current_gameweek_data_valid = False

        Path(gameweeks_db).touch(exist_ok=True)
        asyncio.run(self.fpl_get_session())

    # ------------------ Gameweek Methods ------------------

    def get_current_gameweek(self):
        return self.curr_gameweek

    def set_current_gameweek(self):
        for gw in self.gameweeks:
            if gw:
                if gw.is_current:
                    log.info(f"Current gameweek: {gw.id}")
                    self.curr_gameweek = gw.id
                if gw.is_next:
                    log.info(f"Next gameweek: {gw.id}")
                    self.next_gameweek = gw.id

    def is_gameweek_data_checked(self):
        gw_obj = self.gameweeks[self.curr_gameweek - 1]
        if gw_obj.id != self.curr_gameweek:
            log.error(f"Wrong gameweek! {gw_obj.id} != {self.curr_gameweek}")
            sys.exit(2)
        return gw_obj.is_current and gw_obj.data_checked

    def is_current_gameweek_completed(self):
        return self.is_gameweek_data_checked() or self.current_gameweek_data_valid

    def has_gameweek_been_updated(self):
        with open(self.gameweeks_db, "r") as db:
            return str(self.curr_gameweek) + "\n" in db.readlines()

    def marked_gameweek_updated(self):
        with open(self.gameweeks_db, "a") as db:
            db.write(f"{self.curr_gameweek}\n")

    # ------------------ Fixture Validation ------------------

    def is_valid_gameweek_fixture(self, fixture):
        entry_1_empty = (
            fixture["entry_1_win"] == 0
            and fixture["entry_1_loss"] == 0
            and fixture["entry_1_draw"] == 0
        )
        entry_2_empty = (
            fixture["entry_2_win"] == 0
            and fixture["entry_2_loss"] == 0
            and fixture["entry_2_draw"] == 0
        )
        if entry_1_empty or entry_2_empty:
            log.info(
                f"Match week {self.curr_gameweek} still in progress. "
                f"{fixture['entry_1_name']} vs {fixture['entry_2_name']}"
            )
            return False
        return True

    def is_valid_fixtures(self, fixtures):
        if not fixtures:
            log.error("Failed to retrieve H2H league fixture")
            sys.exit(2)
        return all(self.is_valid_gameweek_fixture(fixture) for fixture in fixtures)

    # ------------------ Fixtures Retrieval Methods ------------------

    async def fpl_fixtures_info(self):
        local_gameweek = self.curr_gameweek + 1
        fixtures = await self.h2h_league.get_fixture(local_gameweek)
        for fixture in fixtures:
            log.info(fixture)

    async def fpl_get_fixtures(self):
        all_fixtures = []
        for gameweek in range(1, self.curr_gameweek + 1):
            fixtures = await self.h2h_league.get_fixture(gameweek)
            if not self.is_valid_fixtures(fixtures):
                log.info(
                    f"\nFailed to retrieve fixture data for gameweek {gameweek}, retry...\n"
                )
                fixtures = await self.h2h_league.get_fixture(f"{gameweek}&page=1")
                if not self.is_valid_fixtures(fixtures):
                    log.error("Invalid H2H league fixture")
                    raise ValueError("Invalid H2H league fixtures")
            all_fixtures.append(fixtures)
        return all_fixtures

    async def fpl_get_fixtures_2(self):
        valid_fixtures = []
        all_fixtures = await self.h2h_league.get_fixtures()
        for fixture in all_fixtures:
            if fixture["event"] > self.curr_gameweek:
                break
            if not self.is_valid_gameweek_fixture(fixture):
                log.error(f"Invalid fixture: {fixture}")
                raise ValueError("Invalid H2H league fixtures")
            valid_fixtures.append(fixture)
        return valid_fixtures

    async def fpl_get_fixtures_3(self):
        all_fixtures = []
        for gameweek in range(1, self.curr_gameweek + 1):
            fixtures = await self.h2h_league.get_fixture(gameweek)
            if not self.is_valid_fixtures(fixtures):
                log.info(
                    f"\nFailed to retrieve fixture data for gameweek {gameweek}, retry...\n"
                )
                for i, fixture in enumerate(fixtures):
                    p1, p2 = fixture["entry_1_points"], fixture["entry_2_points"]
                    if p1 == 0 or p2 == 0:
                        log.error("Invalid H2H league fixture")
                        sys.exit(2)
                    if p1 > p2:
                        (
                            fixtures[i]["entry_1_win"],
                            fixtures[i]["entry_1_total"],
                            fixtures[i]["entry_2_loss"],
                        ) = (1, 3, 1)
                    elif p2 > p1:
                        (
                            fixtures[i]["entry_2_win"],
                            fixtures[i]["entry_2_total"],
                            fixtures[i]["entry_1_loss"],
                        ) = (1, 3, 1)
                    else:
                        (
                            fixtures[i]["entry_1_draw"],
                            fixtures[i]["entry_2_draw"],
                            fixtures[i]["entry_1_total"],
                            fixtures[i]["entry_2_total"],
                        ) = (1, 1, 1, 1)
            all_fixtures.append(fixtures)
        return all_fixtures

    # ------------------ H2H League Fixture Mapping ------------------

    def build_h2h_league_fixture_map(self, fixtures):
        for fixture in fixtures:
            week = fixture["event"]
            if week > self.curr_gameweek:
                continue
            self.h2h_league_fixture_map.setdefault(week, []).append(fixture)

    def fpl_get_h2h_league_fixtures(self):
        if self.fpl_fixtures_retrieve_method in (1, 3):
            for fixtures in self.h2h_league_all_fixtures:
                self.build_h2h_league_fixture_map(fixtures)
        else:
            self.build_h2h_league_fixture_map(self.h2h_league_all_fixtures)

        log.info(f"Build H2H league info method {self.fpl_fixtures_retrieve_method}")
        return self.h2h_league, self.h2h_league_fixture_map

    # ------------------ FPL Session Setup ------------------

    async def fpl_get_session(self):
        self.fpl_session = FPL()
        await self.fpl_session.login_v2(
            email=os.environ["FPL_EMAIL"], password=os.environ["FPL_PASSWORD"]
        )
        self.user = await self.fpl_session.get_user()
        self.gameweeks = await self.fpl_session.get_gameweeks()
        self.set_current_gameweek()
        self.h2h_league = await self.fpl_session.get_h2h_league(self.h2h_league_id)
        await self.fpl_fixtures_info()

        try:
            self.h2h_league_all_fixtures = await self.fpl_get_fixtures()
        except ValueError:
            log.info("Failed to retrieve game week data, trying second method")
            try:
                self.h2h_league_all_fixtures = await self.fpl_get_fixtures_2()
                self.fpl_fixtures_retrieve_method = 2
            except ValueError:
                log.info("Failed to retrieve game week data, trying third method")
                if not self.is_gameweek_data_checked():
                    self.current_gameweek_data_valid = False
                    return
                self.h2h_league_all_fixtures = await self.fpl_get_fixtures_3()
                self.fpl_fixtures_retrieve_method = 3

        self.current_gameweek_data_valid = True
