import logging
import threading
import time

from jacalingest.engine.service import Service

class StatefulService(Service):

    OFF_STATE = 0

    def __init__(self, initial_state, **kwargs):
        logging.debug("Initializing")

        super(StatefulService, self).__init__(**kwargs)
        self.state = self.OFF_STATE
        self.initial_state = initial_state

    def start(self):
        logging.debug("Starting")
        self.state = self.initial_state
        super(StatefulService, self).start()

    def tick(self):
        if self.state == self.OFF_STATE:
            return self.OFF_STATE

        state = self.stateful_tick(self.state)
        if state is not None:
            self.state = state

        return self.state

    def stateful_tick(self, state):
        raise NotImplementedError

    # tell the service to terminate and die
    def terminate(self):
        logging.debug("Terminating")
        self.state = self.OFF_STATE
        super(StatefulService, self).terminate()

