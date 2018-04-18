import logging
import threading
import time

from jacalingest.engine.service import Service

class ConfigurableService(Service):
    def __init__(self, parameters, configuration, **kwargs):
        logging.info("Initializing")
        self._parameters = parameters
        self._configuration = configuration
        super(ConfigurableService, self).__init__(name=parameters["name"], **kwargs)

    def get_parameter(self, key):
        if self._parameters is None:
            return None
        return self._parameters.get(key)

    def get_configuration(self, key):
        return self._configuration.get(key)

