from enum import Enum


class PlayerOutcome(Enum):
    WIN = 0
    LOSS = 1
    DRAW = 2
    INVALID = 3


class FPLPlayer():
    """
    Object representation for an FPL Player
    """

    def __init__(self, id, name, team_name):
        self.id = id
        self.name = name
        self.team_name = team_name
        self.win = dict()
        self.draw = dict()
        self.loss = dict()
        self.points = dict()
        self.total_points = 0  # Head-to-Head total points
        self.is_knockout = False
        self.winner = None

    def populate_player_stats(self, week, h2h_fixture, entry):
        if week not in self.win:
            self.win[week] = 0
        if week not in self.draw:
            self.draw[week] = 0
        if week not in self.loss:
            self.loss[week] = 0
        if week not in self.points:
            self.points[week] = 0

        self.win[week] = (h2h_fixture[entry + '_win'])
        self.draw[week] = (h2h_fixture[entry + '_draw'])
        self.loss[week] = (h2h_fixture[entry + '_loss'])
        self.points[week] = (h2h_fixture[entry + '_points'])
        self.total_points += self.points[week]

    def get_id(self):
        return self.id

    def get_name(self):
        return self.name

    def get_team_name(self):
        return self.team_name

    def get_points(self, week):
        return self.points[week]

    def get_win(self, week):
        return self.win[week]

    def get_loss(self, week):
        return self.loss[week]

    def get_draw(self, week):
        return self.draw[week]

    def get_total_win(self):
        return sum(v for v in self.win.values())

    def get_total_loss(self):
        return sum(v for v in self.loss.values())

    def get_total_draw(self):
        return sum(v for v in self.draw.values())

    def get_total_h2h_points(self):
        return ((self.get_total_win() * 3) + self.get_total_draw())

    def get_total_points(self):
        return self.total_points

    def is_winner(self, current_week):
        return (self.get_current_week_outcome(current_week) ==
                PlayerOutcome.WIN)

    def is_loser(self, current_week):
        return (self.get_current_week_outcome(current_week) ==
                PlayerOutcome.LOSS)

    def is_draw(self, current_week):
        return (self.get_current_week_outcome(current_week) ==
                PlayerOutcome.DRAW)

    def get_current_week_outcome(self, current_week):
        # Current week.
        if self.get_win(week=current_week):
            return PlayerOutcome.WIN
        elif self.get_loss(week=current_week):
            return PlayerOutcome.LOSS
        elif self.get_draw(week=current_week):
            return PlayerOutcome.DRAW
        return PlayerOutcome.INVALID

    def __str__(self):
        to_str = ("{name} "
                  "[{team_name}]\n"
                  "Win: {w} "
                  "Loss: {l} "
                  "Draw: {d} "
                  "H2H_Points:{h2h_p}\n"
                  "Points: {p} "
                  "Total Points: {t}").format(
                      name=self.name,
                      team_name=self.team_name,
                      w=self.get_total_win(),
                      l=self.get_total_loss(),
                      d=self.get_total_draw(),
                      h2h_p=self.get_total_h2h_points(),
                      p=self.points,
                      t=self.total_points)
        return to_str
