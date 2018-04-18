import logging
import threading
import time

class Service(object):

    def __init__(self, name):
        logging.debug("Initializing")

        self.messager = None
        self.service_name = name

    def get_name(self):
        return self.service_name

    def set_messager(self, messager):
        self.messager = messager

    def start(self):
        pass

    def terminate(self):
        pass

    def tick(self):
        raise NotImplementedError

