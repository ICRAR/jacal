import logging
import time
import unittest

from jacalingest.engine.servicerunner import ServiceRunner
from jacalingest.engine.configuration.configurationmessage import ConfigurationMessage
from jacalingest.engine.configuration.configurationadapter import ConfigurationAdapter

from jacalingest.engine.messaging.queuemessagingsystem import QueueMessagingSystem
from jacalingest.engine.messaging.messager import Messager

from jacalingest.stringdomain.numbergeneratorservice import NumberGeneratorService
from jacalingest.stringdomain.stringmessage import StringMessage


class TestNumberGeneratorService(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        logging.basicConfig(level=logging.INFO, format='%(threadName)s, %(module)s: %(message)s')

    def test(self):
        messaging_system = QueueMessagingSystem()
        messager = Messager()
        numbers_endpoint = messager.get_endpoint(messaging_system, "numbers", StringMessage)
        parameters = {'name': 'number_service', 'endpoint': numbers_endpoint}

        configuration_endpoint = messager.get_endpoint(messaging_system, "configuration", ConfigurationMessage)
        configuration_adapter = ConfigurationAdapter(NumberGeneratorService, parameters, configuration_endpoint)

        number_generator_service_runner = ServiceRunner(configuration_adapter, messager)
      
        number_generator_service_runner.start()
        time.sleep(10)

        configuration_message = ConfigurationMessage({})
        messager.publish(configuration_endpoint, configuration_message)

        time.sleep(10)

        number_generator_service_runner.terminate()
        number_generator_service_runner.wait()

if __name__ == '__main__':
    unittest.main()
