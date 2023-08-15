import heapq

from copy import deepcopy
from google.cloud import pubsub_v1
from models.logger import Logger

log = Logger.getInstance().getLogger()


class GcpPubSubClient(object):
    """[summary]

    Args:
        object ([type]): [description]
    """
    def __init__(self, project_id, topic_id):
        self.project_id = project_id
        self.topic_id = topic_id
        self.publisher = \
            pubsub_v1.PublisherClient()

        # The `topic_path` method creates a fully qualified
        # identifier in the form
        # `projects/{project_id}/topics/{topic_id}`
        self.topic_path = self.publisher.topic_path(project_id, topic_id)

    def publish(self, fpl_session, heap):
        message = self.build_pubsub_message(fpl_session, heap)
        log.info(message)
        self.publish_message(data=message)

    def publish_message(self, data):
        future = self.publisher.publish(self.topic_path, data)
        # TODO - Handle return code.
        log.debug(future.result())
        log.debug("Published message to {0}".format(self.topic_path))

    def build_pubsub_message(self, fpl_session, heap):
        """[summary]

        Args:
            fpl_session ([type]): [description]
            heap ([type]): [description]

        Returns:
            [type]: [description]
        """
        winners = []
        losers = []
        draws = []
        rank = 1
        heap_copy = deepcopy(heap)
        curr_gw = fpl_session.get_current_gameweek()
        rank_str = ""
        outcome_str = ""

        while heap_copy:
            player = heapq.heappop(heap_copy).val

            name = player.get_name()
            if player.is_winner(curr_gw):
                winners.append(name)
            elif player.is_loser(curr_gw):
                losers.append(name)
            elif player.is_draw(curr_gw):
                draws.append(name)
            else:
                log.error("Invalid outcome")
                exit(2)

            rank_str += ("{0} place {1}.").format(
                self.get_rank_str(rank),
                name
            )
            rank += 1

        if len(winners) > 0:
            outcome_str += "Winners:"
            for winner in winners:
                outcome_str += ("{0}.").format(winner)
        if len(draws) > 0:
            outcome_str += "Draw:"
            for draw in draws:
                outcome_str += ("{0}.").format(draw)

        return ("{winners}:{rank}.").format(
            winners=outcome_str,
            rank=rank_str
        ).encode('utf-8')

    def get_rank_str(self, rank):
        if rank == 1:
            return "First"
        elif rank == 2:
            return "Second"
        elif rank == 3:
            return "Third"
        elif rank == 4:
            return "Fourth"
        elif rank == 5:
            return "Fifth"
        elif rank == 6:
            return "Sixth"
        elif rank == 7:
            return "Seventh"
        elif rank == 8:
            return "Eighth"
        elif rank == 9:
            return "Ninth"
        elif rank == 10:
            return "Tenth"
        elif rank == 11:
            return "Eleventh"
        elif rank == 12:
            return "Twelveth"
        elif rank == 13:
            return "Thirteenth"
        elif rank == 14:
            return "Fourteenth"
        elif rank == 15:
            return "Fifteenth"
        elif rank == 16:
            return "Sixteenth"
