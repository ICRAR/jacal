import logging
import time
import unittest

from jacalingest.engine.servicerunner import ServiceRunner
from jacalingest.engine.servicerunnerfactory import ServiceRunnerFactory
from jacalingest.engine.configuration.configurationadapter import ConfigurationAdapter
from jacalingest.engine.configuration.configurationmessage import ConfigurationMessage

from jacalingest.engine.messaging.messager import Messager
from jacalingest.engine.messaging.queuemessagingsystem import QueueMessagingSystem
from jacalingest.engine.monitoringandcontrol.genericmonitorservice import GenericMonitorService
from jacalingest.engine.monitoringandcontrol.metrics import Metrics
from jacalingest.engine.monitoringandcontrol.monitoradapter import MonitorAdapter

from jacalingest.stringdomain.lettergeneratorservice import LetterGeneratorService
from jacalingest.stringdomain.stringconcatenatorservice import StringConcatenatorService
from jacalingest.stringdomain.stringmessage import StringMessage
from jacalingest.stringdomain.stringwriterservice import StringWriterService


class TestStringDomain(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        logging.basicConfig(level=logging.INFO, format='%(threadName)s, %(module)s: %(message)s')

    def test(self):
        messaging_system = QueueMessagingSystem()
        messager = Messager()

        configuration_stream = messager.get_stream(messaging_system, "configuration", ConfigurationMessage)
        control_stream = messager.get_stream(messaging_system, "control", StringMessage)

        service_runner_factory = ServiceRunnerFactory(messager)

        letter1_stream = messager.get_stream(messaging_system, "letter1", StringMessage)
        letter1_metrics_stream = messager.get_stream(messaging_system, "letter1_metrics", Metrics)
        letter1_generator_service_runner = service_runner_factory.get_service_runner(LetterGeneratorService, {"name": "letter1_generator_service", "endpoint": letter1_stream.get_endpoint()}, configuration_stream=configuration_stream, metrics_stream=letter1_metrics_stream)

        letter2_stream = messager.get_stream(messaging_system, "letter2", StringMessage)
        letter2_metrics_stream = messager.get_stream(messaging_system, "letter2_metrics", Metrics)
        letter2_generator_service_runner = service_runner_factory.get_service_runner(LetterGeneratorService, {"name": "letter2_generator_service", "endpoint": letter2_stream.get_endpoint()}, configuration_stream=configuration_stream, metrics_stream=letter2_metrics_stream)

        concatenation_stream = messager.get_stream(messaging_system, "concatenation", StringMessage)
        concatenator_metrics_stream = messager.get_stream(messaging_system, "concatenator_metrics", Metrics)
        string_concatenator_service_runner = service_runner_factory.get_service_runner(StringConcatenatorService, {"name": "string_concatenator_service", "first_endpoint": letter1_stream.get_endpoint(), "second_endpoint": letter2_stream.get_endpoint(), "concatenation_endpoint": concatenation_stream.get_endpoint(), "control_endpoint": control_stream.get_endpoint()}, configuration_stream=configuration_stream, metrics_stream=concatenator_metrics_stream)

        writer_metrics_stream = messager.get_stream(messaging_system, "writer_metrics", Metrics)
        string_writer_service_runner = service_runner_factory.get_service_runner(StringWriterService, {"name": "string_writer_service", "string_endpoint": concatenation_stream.get_endpoint(), "control_endpoint": control_stream.get_endpoint()}, configuration_stream=configuration_stream, metrics_stream=writer_metrics_stream)

        monitor_service = GenericMonitorService("generic_monitor_service", [letter1_metrics_stream.get_endpoint(), letter2_metrics_stream.get_endpoint(), concatenator_metrics_stream.get_endpoint(), writer_metrics_stream.get_endpoint()])
        monitor_service_runner = ServiceRunner(monitor_service, messager)

        # start them, wait ten seconds, stop them
        logging.info("starting services")
        monitor_service_runner.start()
        string_writer_service_runner.start()
        string_concatenator_service_runner.start()
        letter1_generator_service_runner.start()
        letter2_generator_service_runner.start()

        time.sleep(5)

        logging.info("Publishing ConfigurationMessage")
        mainline_configuration_endpoint = configuration_stream.get_endpoint()
        configuration_message = ConfigurationMessage({"letter1_generator_service.upper": True, "string_writer_service.output_path": "output.txt"})
        messager.publish(mainline_configuration_endpoint, configuration_message)

        time.sleep(5)

        mainline_control_endpoint = control_stream.get_endpoint()

        logging.info("Publishing 'Start' control message")
        messager.publish(mainline_control_endpoint, StringMessage("Start"))

        time.sleep(5)

        logging.info("Publishing 'Stop' control message")
        messager.publish(mainline_control_endpoint, StringMessage("Stop"))

        time.sleep(5)

        logging.info("Stopping services")
        letter1_generator_service_runner.terminate()
        letter2_generator_service_runner.terminate()
        string_concatenator_service_runner.terminate()
        string_writer_service_runner.terminate()
        monitor_service_runner.terminate()

if __name__ == '__main__':
    unittest.main()

