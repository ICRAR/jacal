import logging
import time
import unittest

from jacalingest.engine.servicerunner import ServiceRunner
from jacalingest.engine.configuration.configurationadapter import ConfigurationAdapter
from jacalingest.engine.configuration.configurationmessage import ConfigurationMessage

from jacalingest.engine.messaging.queuemessagingsystem import QueueMessagingSystem
from jacalingest.engine.messaging.messager import Messager
from jacalingest.engine.monitoringandcontrol.metrics import Metrics
from jacalingest.engine.monitoringandcontrol.monitoradapter import MonitorAdapter
from jacalingest.stringdomain.stringconcatenatorservice import StringConcatenatorService
from jacalingest.stringdomain.stringmessage import StringMessage

class TestStringConcatenatorService(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        logging.basicConfig(level=logging.INFO, format='%(threadName)s, %(module)s: %(message)s')

    def test(self):
        messaging_system=QueueMessagingSystem()
        messager = Messager()
        metrics_endpoint = messager.get_endpoint(messaging_system, "metrics", Metrics)
        first_endpoint = messager.get_endpoint(messaging_system, "first", StringMessage)
        second_endpoint = messager.get_endpoint(messaging_system, "second", StringMessage)
        concatenation_endpoint = messager.get_endpoint(messaging_system, "concatenation", StringMessage)
        control_endpoint = messager.get_endpoint(messaging_system, "control", StringMessage)

        parameters={"name":"string_concatenator_service", "first_endpoint":first_endpoint, "second_endpoint":second_endpoint, "concatenation_endpoint":concatenation_endpoint, "control_endpoint":control_endpoint}
        
        configuration_endpoint = messager.get_endpoint(messaging_system, "configuration", ConfigurationMessage)
        configuration_adapter = ConfigurationAdapter(StringConcatenatorService, parameters, configuration_endpoint)
        monitor_adapter = MonitorAdapter(configuration_adapter, metrics_endpoint)
        service_runner = ServiceRunner(monitor_adapter, messager)

        service_runner.start()
        time.sleep(5)

        logging.info("Publishing ConfigurationMessage")
        configuration_message = ConfigurationMessage({})
        messager.publish(configuration_endpoint, configuration_message)

        time.sleep(5)

        logging.info("Publishing 'Start' control message")
        messager.publish(control_endpoint, StringMessage("Start"))

        time.sleep(5)

        logging.info("Publishing 'Stop' control message")
        messager.publish(control_endpoint, StringMessage("Stop"))

        time.sleep(5)

        service_runner.terminate()
        service_runner.wait()

if __name__ == '__main__':
    unittest.main()

