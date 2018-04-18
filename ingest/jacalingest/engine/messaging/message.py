import logging

class Message(object):
    def __init__(self, **kwargs):
        logging.debug("initializing")

    @staticmethod
    def serialize(message):
        raise NotImplementedError

    @staticmethod
    def deserialize(serialized):
        raise NotImplementedError
