import logging

class ServiceContainer:
    def __init__(self, **kwargs):
        pass

    def publish(self, endpoint, message):
        raise NotImplementedError

    def poll(self, endpoint):
        raise NotImplementedError

