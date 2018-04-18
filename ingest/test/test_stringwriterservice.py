import logging
import time
import unittest

from jacalingest.engine.servicerunner import ServiceRunner
from jacalingest.engine.configuration.configurationadapter import ConfigurationAdapter
from jacalingest.engine.configuration.configurationmessage import ConfigurationMessage

from jacalingest.engine.messaging.messager import Messager
from jacalingest.engine.messaging.queuemessagingsystem import QueueMessagingSystem
from jacalingest.stringdomain.stringmessage import StringMessage
from jacalingest.stringdomain.stringwriterservice import StringWriterService

class TestStringWriterService(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        logging.basicConfig(level=logging.INFO, format='%(threadName)s, %(module)s: %(message)s')

    def test(self):
   
        messaging_system = QueueMessagingSystem()
        messager = Messager()
        string_endpoint = messager.get_endpoint(messaging_system, "string", StringMessage)
        control_endpoint = messager.get_endpoint(messaging_system, "control", StringMessage)

        parameters={"name": "string_writer_service",
                    "string_endpoint": string_endpoint,
                    "control_endpoint": control_endpoint}
        configuration_endpoint = messager.get_endpoint(messaging_system, "configuration", ConfigurationMessage)
        configuration_adapter = ConfigurationAdapter(StringWriterService, parameters, configuration_endpoint)
        service_runner = ServiceRunner(configuration_adapter, messager)

        service_runner.start()

        time.sleep(5)

        logging.info("Publishing ConfigurationMessage")
        configuration_message = ConfigurationMessage({"string_writer_service.output_path": "output.txt"})
        messager.publish(configuration_endpoint, configuration_message)

        time.sleep(5)

        logging.info("Publishing 'Start' control message")
        messager.publish(control_endpoint, StringMessage("Start"))

        time.sleep(10)

        logging.info("Publishing 'Stop' control message")
        messager.publish(control_endpoint, StringMessage("Stop"))

        time.sleep(5)

        service_runner.terminate()
        service_runner.wait()

if __name__ == '__main__':
    unittest.main()

