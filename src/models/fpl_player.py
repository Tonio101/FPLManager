"""

"""
class FPLPlayer():

    def __init__(self):
        self.id = 0
        self.name = ''
        self.team_name = ''
        self.win = 0
        self.draw = 0
        self.loss = 0
        self.points = 0 # Current week points
        self.total_points = 0 # Head-to-Head total points
        self.is_knockout = False
        self.winner = None
        self.curr_gameweek = 0

    def populate_player_info(self, h2h_fixture, entry):
        self.id = h2h_fixture[entry + '_entry']
        self.name = h2h_fixture[entry + '_player_name']
        self.team_name = h2h_fixture[entry + '_name']
        self.win = h2h_fixture[entry + '_win']
        self.draw = h2h_fixture[entry + '_draw']
        self.loss = h2h_fixture[entry + '_loss']
        self.points = h2h_fixture[entry + '_points']
        self.total_points = h2h_fixture[entry + '_total']

    def set_gameweek(self, gameweek):
        self.curr_gameweek = gameweek

    def get_gameweek(self):
        return self.curr_gameweek

    def get_name(self):
        return self.name

    def get_team_name(self):
        return self.team_name

    def get_points(self):
        return self.points

    def get_win(self):
        return self.win

    def get_loss(self):
        return self.loss

    def get_draw(self):
        return self.draw

    def get_total_points(self):
        return self.total_points

    def __str__(self):
        to_str = "{name} [{team_name}]".format(name=self.name, team_name=self.team_name)
        return to_str

