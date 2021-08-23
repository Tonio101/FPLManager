import heapq

class Node(object):
    def __init__(self, val):
        self.val = val

    def __repr__(self):
        return f'Node value: {self.val}'

    def __lt__(self, other):
        if self.val.get_total_points() == other.val.get_total_points():
            return other.val.get_points() < self.val.get_points()

        return other.val.get_total_points() < self.val.get_total_points()
