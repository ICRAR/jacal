import logging

from jacalingest.engine.service import Service
from jacalingest.engine.servicecontainer import ServiceContainer
from jacalingest.engine.monitoringandcontrol.metrics import Metrics

class MonitorAdapter(Service, ServiceContainer):
    def __init__(self, service, metrics_endpoint):
        self._service = service
        self._service.set_messager(self)

        super(MonitorAdapter, self).__init__(name=self._service.get_name())

        self.metrics_endpoint = metrics_endpoint
        self.metrics = Metrics(self.get_name())

    def start(self):
        self._service.start()

    def terminate(self):
        self._service.terminate()
        logging.info("Publishing metrics on termination")
        self.messager.publish(self.metrics_endpoint, self.metrics)

    def tick(self):
        state = self._service.tick()
        if state is not None:
            if state != self.metrics.current_state:
                self.metrics.state(state)
                logging.info("Publishing metrics on change of state.")
                self.messager.publish(self.metrics_endpoint, self.metrics)
        return state

    def publish(self, endpoint, message):
        self.messager.publish(endpoint, message)
        self.metrics.sent(endpoint.topic)

    def poll(self, endpoint):
        message = self.messager.poll(endpoint)

        if message is None:
            self.metrics.polled(endpoint.topic)
        else:
            self.metrics.received(endpoint.topic)

        return message
