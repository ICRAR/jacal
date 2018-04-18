from collections import defaultdict
import itertools
import logging

from jacalingest.engine.statefulservice import StatefulService

class HandlerService(StatefulService):

    def __init__(self, **kwargs):
        logging.debug("Initializing")

        super(HandlerService, self).__init__(**kwargs)

        self.handlers = defaultdict(dict)
        self.cyclers = dict()

    def set_handler(self, endpoint, handler, states):
        assert endpoint is not None

        for state in states:
            self.handlers[state][endpoint] = handler
            self.cyclers[state] = itertools.cycle(self.handlers[state])

    def stateful_tick(self, state):
        for i in range(len(self.handlers[state])):
            endpoint = self.cyclers[state].next()
            message = self.messager.poll(endpoint)
            if message:
                handler = self.handlers[state][endpoint]
                return handler(message, state)
        return None

