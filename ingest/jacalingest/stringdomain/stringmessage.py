import logging

from jacalingest.engine.messaging.message import Message

class StringMessage(Message):
    def __init__(self, payload):
        super(StringMessage, self).__init__()
        self._payload = payload

    def get_payload(self):
        return self._payload

    def __str__(self):
        return self._payload

    @staticmethod
    def serialize(string_message):
        return string_message._payload

    @staticmethod
    def deserialize(serialized):
        return StringMessage(serialized)

