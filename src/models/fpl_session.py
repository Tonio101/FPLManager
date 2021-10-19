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
        self.curr_gameweek = 0
        self.next_gameweek = 0
        self.h2h_league_id = h2h_league_id
        self.gameweeks_db = gameweeks_db
        dbfile = Path(gameweeks_db)
        dbfile.touch(exist_ok=True)
        asyncio.run(self.fpl_get_session())

    def get_current_gameweek(self):
        return self.curr_gameweek

    def set_current_gameweek(self):
        for gw in self.gameweeks:
            if gw and gw.is_current:
                self.curr_gameweek = gw.id
            if gw and gw.is_next:
                self.next_gameweek = gw.id

    async def fpl_get_session(self):
        async with aiohttp.ClientSession() as session:
            self.fpl_session = FPL(session)
            await self.fpl_session.login()
            self.user = await self.fpl_session.get_user()
            self.gameweeks = await self.fpl_session.get_gameweeks()
            self.set_current_gameweek()
            self.h2h_league = \
                await self.fpl_session.get_h2h_league(self.h2h_league_id)
            # self.h2h_league_all_fixtures = \
            #    await self.h2h_league.get_fixtures()
            for i in range(0, self.curr_gameweek):
                self.h2h_league_all_fixtures.append(
                    await self.h2h_league.get_fixture(gameweek=i + 1))

    def fpl_get_h2h_league_fixtures(self):
        self.h2h_league_fixture_map = dict()
        for h2h_league_fixtures in self.h2h_league_all_fixtures:
            for h2h_league_fixture in h2h_league_fixtures:
                curr_week = h2h_league_fixture['event']
                if curr_week > self.curr_gameweek:
                    continue

                if curr_week not in self.h2h_league_fixture_map:
                    self.h2h_league_fixture_map[curr_week] = []
                self.h2h_league_fixture_map[curr_week].append(
                    h2h_league_fixture)

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
            db.write(str(self.curr_gameweek))

    def is_current_gameweek_completed(self):
        gw_obj = self.gameweeks[self.curr_gameweek - 1]

        if gw_obj.id != self.curr_gameweek:
            log.error("Wrong gameweek!")
            sys.exit(2)

        return (gw_obj.is_current and gw_obj.data_checked)
