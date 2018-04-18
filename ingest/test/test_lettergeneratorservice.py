import logging
import time
import unittest

from jacalingest.engine.servicerunner import ServiceRunner
from jacalingest.engine.configuration.configurationadapter import ConfigurationAdapter
from jacalingest.engine.configuration.configurationmessage import ConfigurationMessage
from jacalingest.engine.messaging.queuemessagingsystem import QueueMessagingSystem
from jacalingest.engine.messaging.messager import Messager
from jacalingest.stringdomain.lettergeneratorservice import LetterGeneratorService
from jacalingest.stringdomain.stringmessage import StringMessage

class TestLetterGeneratorService(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        logging.basicConfig(level=logging.INFO, format='%(threadName)s, %(module)s: %(message)s')

    def test(self):
        messaging_system = QueueMessagingSystem()
        messager = Messager()
        letters_endpoint = messager.get_endpoint(messaging_system, "letters", StringMessage)
        parameters = {'name': 'letter_generator_service', 'endpoint': letters_endpoint}

        configuration_endpoint = messager.get_endpoint(messaging_system, "configuration", ConfigurationMessage)
        configuration_adapter = ConfigurationAdapter(LetterGeneratorService, parameters, configuration_endpoint)

        letter_generator_service_runner = ServiceRunner(configuration_adapter, messager)

        letter_generator_service_runner.start()
        time.sleep(10)

        configuration_message = ConfigurationMessage({"letter_generator_service.upper": True})
        messager.publish(configuration_endpoint, configuration_message)

        time.sleep(10)

        letter_generator_service_runner.terminate()
        letter_generator_service_runner.wait()

if __name__ == '__main__':
    unittest.main()

