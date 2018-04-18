import logging
import time
import unittest

from jacalingest.engine.servicerunner import ServiceRunner
from jacalingest.engine.servicerunnerfactory import ServiceRunnerFactory
from jacalingest.engine.configuration.configurationadapter import ConfigurationAdapter
from jacalingest.engine.configuration.configurationmessage import ConfigurationMessage

from jacalingest.engine.messaging.messager import Messager
from jacalingest.engine.messaging.queuemessagingsystem import QueueMessagingSystem

from jacalingest.network.socketreaderservice import SocketReaderService
from jacalingest.network.socketwriterservice import SocketWriterService

from jacalingest.stringdomain.stringmessage import StringMessage


class TestStringDomain(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        logging.basicConfig(level=logging.INFO, format='%(threadName)s, %(module)s: %(message)s')

    def test(self):
        messaging_system = QueueMessagingSystem()
        messager = Messager()

        configuration_stream = messager.get_stream(messaging_system, "configuration", ConfigurationMessage)
        control_stream = messager.get_stream(messaging_system, "control", StringMessage)
        input_stream = messager.get_stream(messaging_system, "input", StringMessage)
        output_stream = messager.get_stream(messaging_system, "output", StringMessage)

        service_runner_factory = ServiceRunnerFactory(messager)

        socket_writer_service_runner = service_runner_factory.get_service_runner(SocketWriterService, {"name": "socket_writer_service", "input_endpoint": input_stream.get_read_endpoint(), "control_endpoint": control_stream.get_read_endpoint(), "input_class": StringMessage}, configuration_stream=configuration_stream)

        socket_reader_service_runner = service_runner_factory.get_service_runner(SocketReaderService, {"name": "socket_reader_service", "output_endpoint": output_stream.get_write_endpoint(), "control_endpoint": control_stream.get_read_endpoint(), "output_class": StringMessage}, configuration_stream=configuration_stream)


       
        # start them, wait ten seconds, stop them
        logging.info("starting services")
        socket_writer_service_runner.start()
        socket_reader_service_runner.start()

        time.sleep(5)

        logging.info("Publishing ConfigurationMessage")
        mainline_configuration_endpoint = configuration_stream.get_write_endpoint()
        configuration_message = ConfigurationMessage({"socket_writer_service": {"host": "localhost", "port": "10001"}, "socket_reader_service": {"host": "localhost", "port": "10001"}})
        messager.publish(mainline_configuration_endpoint, configuration_message)

        time.sleep(5)


        logging.info("Publishing 'Start' control message")
        mainline_control_endpoint = control_stream.get_write_endpoint()
        messager.publish(mainline_control_endpoint, StringMessage("Start"))

        time.sleep(5)


        mainline_input_endpoint = input_stream.get_write_endpoint()
        mainline_output_endpoint = output_stream.get_read_endpoint()

        logging.info("Publishing messagse to socket writer...")
        messager.publish(mainline_input_endpoint, StringMessage("Message 1"))
        messager.publish(mainline_input_endpoint, StringMessage("Message 2"))
        messager.publish(mainline_input_endpoint, StringMessage("Message 3"))
        messager.publish(mainline_input_endpoint, StringMessage("Message 4"))
        messager.publish(mainline_input_endpoint, StringMessage("Message 5"))
        messager.publish(mainline_input_endpoint, StringMessage("Message 6"))
        messager.publish(mainline_input_endpoint, StringMessage("Message 7"))
        messager.publish(mainline_input_endpoint, StringMessage("Message 8"))
        messager.publish(mainline_input_endpoint, StringMessage("Message 9"))
        messager.publish(mainline_input_endpoint, StringMessage("Message 10"))

        time.sleep(5)

        logging.info("Checking for message at socket reader...")

        for i in range(20):
            message = messager.poll(mainline_output_endpoint)
            if message is None:
                logging.info("No message.")
                time.sleep(1)
            else:
                logging.info("Message is '{}'".format(message.get_payload()))


        logging.info("Publishing 'Stop' control message")
        messager.publish(mainline_control_endpoint, StringMessage("Stop"))

        time.sleep(5)

        logging.info("Stopping services")
        socket_writer_service_runner.terminate()
        socket_reader_service_runner.terminate()

if __name__ == '__main__':
    unittest.main()

