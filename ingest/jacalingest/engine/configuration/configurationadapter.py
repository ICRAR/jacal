import logging

from jacalingest.engine.service import Service
from jacalingest.engine.servicecontainer import ServiceContainer

class ConfigurationAdapter(Service, ServiceContainer):
    def __init__(self, service_class, service_parameters, configuration_endpoint):
        super(ConfigurationAdapter, self).__init__(name=service_parameters["name"])
        self.service_class = service_class
        self.service_parameters = service_parameters
        self._service = None

        self.configuration_endpoint = configuration_endpoint

    def start(self):
        if self._service is not None:
            self._service.start()

    def terminate(self):
        if self._service is not None:
            self._service.terminate()

    def tick(self):
        configuration_message = self.poll(self.configuration_endpoint)
        if configuration_message:
            logging.info("Processing configuration message for service with label {}".format(self.service_parameters["name"]))
            configuration = configuration_message.get_configuration()
            self._service = self.service_class(parameters=self.service_parameters, configuration=configuration)
            self._service.set_messager(self)
            self._service.start()
        
        if self._service != None:
            return self._service.tick()
        return None

    def publish(self, endpoint, message):
        self.messager.publish(endpoint, message)

    def poll(self, endpoint):
        return self.messager.poll(endpoint)
