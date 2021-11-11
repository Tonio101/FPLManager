import sys
import aiohttp
import asyncio

from fpl import FPL
from models.logger import Logger
from pathlib import Path

log = Logger.getInstance().getLogger()


class FPLSession():
    """
    Wrapper class for an FPL session.
    """

    def __init__(self, h2h_league_id, gameweeks_db='gameweek.db'):
        self.fpl_session = None
        self.user = None
        self.h2h_league = None
        self.h2h_league_fixtures = None
        self.h2h_league_all_fixtures = []
        self.h2h_league_fixture_map = dict()
        self.curr_gameweek = 0
        self.next_gameweek = 0
        self.h2h_league_id = h2h_league_id
        self.gameweeks_db = gameweeks_db
        dbfile = Path(gameweeks_db)
        dbfile.touch(exist_ok=True)
        self.fpl_fixtures_retrieve_method = 1
        asyncio.run(self.fpl_get_session())

    def get_current_gameweek(self):
        return self.curr_gameweek

    def set_current_gameweek(self):
        for gw in self.gameweeks:
            if gw and gw.is_current:
                self.curr_gameweek = gw.id
            if gw and gw.is_next:
                self.next_gameweek = gw.id

    def is_valid_gameweek_fixture(self, fixture):
        if (
            fixture['entry_1_win'] == 0 and
            fixture['entry_1_loss'] == 0 and
            fixture['entry_1_draw'] == 0
           ) or \
           (
            fixture['entry_2_win'] == 0 and
            fixture['entry_2_loss'] == 0 and
            fixture['entry_2_draw'] == 0
           ):
            log.error(("Invalid fixture for gameweek {0}: {1}").format(
                self.get_current_gameweek(), fixture
            ))
            return False
        return True

    def is_valid_fixtures(self, fixtures):
        if fixtures is None or len(fixtures) == 0:
            log.error("Failed to retrieve H2H league fixture")
            sys.exit(2)

        for fixture in fixtures:
            if not self.is_valid_gameweek_fixture(fixture):
                return False

        return True

    async def fpl_get_fixtures(self):
        list_of_fixtures = []
        for i in range(0, self.curr_gameweek):
            gameweek = i + 1
            fixtures = await self.h2h_league.get_fixture(gameweek)
            if not self.is_valid_fixtures(fixtures):
                log.info(("\nFailed to retrieve fixture data "
                          "for gameweek {0}, retry...\n").format(
                              gameweek
                          ))
                # Workaround incase the other API
                # does not have the latest info
                fixtures = \
                    await self.h2h_league.get_fixture(
                        str(gameweek) + "&page=1"
                    )
                if not self.is_valid_fixtures(fixtures):
                    log.error("\nInvalid H2H league fixture\n")
                    # sys.exit(2)
                    raise ValueError("Invalide H2H league fixtures")

            list_of_fixtures.append(fixtures)

        return list_of_fixtures

    async def fpl_get_fixtures_2(self):
        list_of_fixtures = []
        all_fixtures = await self.h2h_league.get_fixtures()
        for fixture in all_fixtures:
            # We don't care about future events yet.
            if fixture['event'] > self.curr_gameweek:
                break

            if not self.is_valid_gameweek_fixture(fixture):
                log.error("Invalid fixture: {0}".format(fixture))
                log.error(("\n*** Failed to retrieve gameweek data ***\n"))
                # sys.exit(2)
                raise ValueError("Invalide H2H league fixtures")

            list_of_fixtures.append(fixture)

        return list_of_fixtures

    async def fpl_get_fixtures_3(self):
        list_of_fixtures = []
        for i in range(0, self.curr_gameweek):
            gameweek = i + 1
            fixtures = await self.h2h_league.get_fixture(gameweek)
            if not self.is_valid_fixtures(fixtures):
                log.info(("\nFailed to retrieve fixture data "
                          "for gameweek {0}, retry...\n").format(
                              gameweek
                          ))
                # Workaround incase the other APIs
                # does not have the latest info
                # Manually populate the win/loss/draw data
                for i, fixture in enumerate(fixtures):
                    player_1_points = fixture['entry_1_points']
                    player_2_points = fixture['entry_2_points']

                    if player_1_points == 0 or player_2_points == 0:
                        log.error("\nInvalid H2H league fixture\n")
                        sys.exit(2)

                    if player_1_points > player_2_points:
                        fixtures[i]['entry_1_win'] = 1
                        fixtures[i]['entry_1_total'] = 3
                        fixtures[i]['entry_2_loss'] = 1
                    elif player_2_points > player_1_points:
                        fixtures[i]['entry_2_win'] = 1
                        fixtures[i]['entry_2_total'] = 3
                        fixtures[i]['entry_1_loss'] = 1
                    elif player_1_points == player_2_points:
                        fixtures[i]['entry_1_draw'] = 1
                        fixtures[i]['entry_2_draw'] = 1
                        fixtures[i]['entry_1_total'] = 1
                        fixtures[i]['entry_2_total'] = 1

            list_of_fixtures.append(fixtures)

        return list_of_fixtures

    async def fpl_get_session(self):
        async with aiohttp.ClientSession() as session:
            self.fpl_session = FPL(session)
            await self.fpl_session.login()
            self.user = await self.fpl_session.get_user()
            self.gameweeks = await self.fpl_session.get_gameweeks()
            self.set_current_gameweek()
            self.h2h_league = \
                await self.fpl_session.get_h2h_league(self.h2h_league_id)
            try:
                self.h2h_league_all_fixtures = await self.fpl_get_fixtures()
            except ValueError:
                log.info(("Failed to retrieve game week data, "
                          "try second method"))
                # TODO - Refactor
                try:
                    self.h2h_league_all_fixtures = \
                        await self.fpl_get_fixtures_2()
                    self.fpl_fixtures_retrieve_method = 2
                except ValueError:
                    log.info(("Failed to retrieve game week data, "
                              "try third method"))

                    # TODO - Check if this is required.
                    if not self.is_gameweek_data_checked():
                        self.current_gameweek_data_valid = False
                        return

                    self.h2h_league_all_fixtures = \
                        await self.fpl_get_fixtures_3()
                    self.fpl_fixtures_retrieve_method = 3

            self.current_gameweek_data_valid = True

    def build_h2h_league_fixture_map(self, h2h_league_fixtures):
        for h2h_league_fixture in h2h_league_fixtures:
            curr_week = h2h_league_fixture['event']
            if curr_week > self.curr_gameweek:
                continue

            if curr_week not in self.h2h_league_fixture_map:
                self.h2h_league_fixture_map[curr_week] = []

            self.h2h_league_fixture_map[curr_week].append(
                h2h_league_fixture)

    def fpl_get_h2h_league_fixtures(self):
        if self.fpl_fixtures_retrieve_method == 1 or\
           self.fpl_fixtures_retrieve_method == 3:
            # List of lists
            for h2h_league_fixtures in self.h2h_league_all_fixtures:
                self.build_h2h_league_fixture_map(h2h_league_fixtures)
        elif self.fpl_fixtures_retrieve_method == 2:
            self.build_h2h_league_fixture_map(self.h2h_league_all_fixtures)

        log.info("Build H2H league info method {0}".format(
            self.fpl_fixtures_retrieve_method
        ))
        return self.h2h_league, self.h2h_league_fixture_map

    def has_gameweek_been_updated(self):
        with open(self.gameweeks_db, 'r') as db:
            lines = db.readlines()
            for line in lines:
                log.debug(line)
                if int(line) == self.curr_gameweek:
                    return True

        return False

    def marked_gameweek_updated(self):
        with open(self.gameweeks_db, 'a') as db:
            db.write(str(self.curr_gameweek) + "\n")

    def is_gameweek_data_checked(self):
        gw_obj = self.gameweeks[self.curr_gameweek - 1]

        if gw_obj.id != self.curr_gameweek:
            log.error("Wrong gameweek!")
            sys.exit(2)

        return (gw_obj.is_current and gw_obj.data_checked)

    def is_current_gameweek_completed(self):
        gw_obj = self.gameweeks[self.curr_gameweek - 1]

        if gw_obj.id != self.curr_gameweek:
            log.error("Wrong gameweek!")
            sys.exit(2)

        return (self.is_gameweek_data_checked() or
                self.current_gameweek_data_valid)
