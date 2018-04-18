import logging
import threading
import time

from jacalingest.engine.servicerunner import ServiceRunner
from jacalingest.engine.configuration.configurationadapter import ConfigurationAdapter
from jacalingest.engine.monitoringandcontrol.monitoradapter import MonitorAdapter

class ServiceRunnerFactory:
    def __init__(self, messager):
        self.messager = messager

    def get_service_runner(self, service_class, service_parameters, configuration_stream=None, metrics_stream=None):
        if configuration_stream is None:
            service = service_class(service_parameters, None)
        else:
            service = ConfigurationAdapter(service_class, service_parameters, configuration_stream.get_read_endpoint())

        if metrics_stream is not None:
            service = MonitorAdapter(service, metrics_stream.get_write_endpoint())

        return ServiceRunner(service, self.messager)

