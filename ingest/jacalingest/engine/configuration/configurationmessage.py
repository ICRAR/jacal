import json

from jacalingest.engine.messaging.message import Message

class ConfigurationMessage(Message):
    def __init__(self, configuration):
        self._configuration = configuration
        super(ConfigurationMessage, self).__init__()

    def get_configuration(self):
        return self._configuration

    @staticmethod
    def serialize(configuration_message):
        return json.dumps(configuration_message._configuration)

    @staticmethod
    def deserialize(serialized):
        return ConfigurationMessage(json.loads(serialized))

