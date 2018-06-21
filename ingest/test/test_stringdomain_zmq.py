import logging
import threading
import time
import unittest

from jacalingest.engine.servicerunner import ServiceRunner
from jacalingest.engine.servicerunnerfactory import ServiceRunnerFactory
from jacalingest.engine.configuration.configurationadapter import ConfigurationAdapter
from jacalingest.engine.configuration.configurationmessage import ConfigurationMessage

from jacalingest.engine.messaging.messager import Messager
from jacalingest.engine.messaging.zmq.zmqmessagingsystem import ZMQMessagingSystem
from jacalingest.engine.messaging.zmq.zmqmessagingsystemregistry import ZMQMessagingSystemRegistry
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

        
    def _run_letter1(self):
        messaging_system = ZMQMessagingSystem("localhost", self.registry_port, 9001)
        messager = Messager()
        letter1_stream = messager.get_stream(messaging_system, "letter1", StringMessage)
        configuration_stream = messager.get_stream(messaging_system, "configuration", ConfigurationMessage)
        letter1_metrics_stream = messager.get_stream(messaging_system, "letter1_metrics", Metrics)
        service_runner_factory = ServiceRunnerFactory(messager)
        letter1_generator_service_runner = service_runner_factory.get_service_runner(LetterGeneratorService, {"name": "letter1_generator_service", "endpoint": letter1_stream.get_write_endpoint()}, configuration_stream=configuration_stream, metrics_stream=letter1_metrics_stream)
        letter1_generator_service_runner.start()

        self.letter1_stopped = False
        while not self.letter1_stopped:
            time.sleep(1)
        letter1_generator_service_runner.terminate()
        logging.debug("THREAD _run_letter1 terminates.")

    def _run_letter2(self):
        messaging_system = ZMQMessagingSystem("localhost", self.registry_port, 9002)
        messager = Messager()
        letter2_stream = messager.get_stream(messaging_system, "letter2", StringMessage)
        configuration_stream = messager.get_stream(messaging_system, "configuration", ConfigurationMessage)
        letter2_metrics_stream = messager.get_stream(messaging_system, "letter2_metrics", Metrics)
        service_runner_factory = ServiceRunnerFactory(messager)
        letter2_generator_service_runner = service_runner_factory.get_service_runner(LetterGeneratorService, {"name": "letter2_generator_service", "endpoint": letter2_stream.get_write_endpoint()}, configuration_stream=configuration_stream, metrics_stream=letter2_metrics_stream)
        letter2_generator_service_runner.start()

        self.letter2_stopped = False
        while not self.letter2_stopped:
            time.sleep(1)
        letter2_generator_service_runner.terminate()
        logging.debug("THREAD _run_letter2 terminates.")

    def _run_concatenator(self):
        messaging_system = ZMQMessagingSystem("localhost", self.registry_port, 9003)
        messager = Messager()
        letter1_stream = messager.get_stream(messaging_system, "letter1", StringMessage)
        letter2_stream = messager.get_stream(messaging_system, "letter2", StringMessage)
        configuration_stream = messager.get_stream(messaging_system, "configuration", ConfigurationMessage)
        control_stream = messager.get_stream(messaging_system, "control", StringMessage)
        concatenation_stream = messager.get_stream(messaging_system, "concatenation", StringMessage)
        concatenator_metrics_stream = messager.get_stream(messaging_system, "concatenator_metrics", Metrics)
        service_runner_factory = ServiceRunnerFactory(messager)
        string_concatenator_service_runner = service_runner_factory.get_service_runner(StringConcatenatorService, {"name": "string_concatenator_service", "first_endpoint": letter1_stream.get_read_endpoint(), "second_endpoint": letter2_stream.get_read_endpoint(), "concatenation_endpoint": concatenation_stream.get_write_endpoint(), "control_endpoint": control_stream.get_read_endpoint()}, configuration_stream=configuration_stream, metrics_stream=concatenator_metrics_stream)
        string_concatenator_service_runner.start()

        self.concatenator_stopped = False
        while not self.concatenator_stopped:
            time.sleep(1)
        string_concatenator_service_runner.terminate()
        logging.debug("THREAD _run_concatenator terminates.")

    def _run_writer(self):
        messaging_system = ZMQMessagingSystem("localhost", self.registry_port, 9004)
        messager = Messager()
        concatenation_stream = messager.get_stream(messaging_system, "concatenation", StringMessage)
        control_stream = messager.get_stream(messaging_system, "control", StringMessage)
        configuration_stream = messager.get_stream(messaging_system, "configuration", ConfigurationMessage)
        writer_metrics_stream = messager.get_stream(messaging_system, "writer_metrics", Metrics)
        service_runner_factory = ServiceRunnerFactory(messager)
        string_writer_service_runner = service_runner_factory.get_service_runner(StringWriterService, {"name": "string_writer_service", "string_endpoint": concatenation_stream.get_read_endpoint(), "control_endpoint": control_stream.get_read_endpoint()}, configuration_stream=configuration_stream, metrics_stream=writer_metrics_stream)
        string_writer_service_runner.start()

        self.writer_stopped = False
        while not self.writer_stopped:
            time.sleep(1)
        string_writer_service_runner.terminate()
        logging.debug("THREAD _run_writer terminates.")

    def _run_monitor(self):
        messaging_system = ZMQMessagingSystem("localhost", self.registry_port, 9005)
        messager = Messager()
        letter1_metrics_stream = messager.get_stream(messaging_system, "letter1_metrics", Metrics)
        letter2_metrics_stream = messager.get_stream(messaging_system, "letter2_metrics", Metrics)
        concatenator_metrics_stream = messager.get_stream(messaging_system, "concatenator_metrics", Metrics)
        writer_metrics_stream = messager.get_stream(messaging_system, "writer_metrics", Metrics)
        monitor_service = GenericMonitorService("generic_monitor_service", [letter1_metrics_stream.get_read_endpoint(), letter2_metrics_stream.get_read_endpoint(), concatenator_metrics_stream.get_read_endpoint(), writer_metrics_stream.get_read_endpoint()])
        monitor_service_runner = ServiceRunner(monitor_service, messager)
        monitor_service_runner.start()

        self.monitor_stopped = False
        while not self.monitor_stopped:
            time.sleep(1)
        monitor_service_runner.terminate()
        logging.debug("THREAD _run_monitor terminates.")

    def test(self):
        self.registry_port = 9000
        registry = ZMQMessagingSystemRegistry(self.registry_port)
        registry.start()

        time.sleep(1)

        logging.info("starting services")

        letter1_thread = threading.Thread(target=self._run_letter1)
        letter1_thread.start()

        letter2_thread = threading.Thread(target=self._run_letter2)
        letter2_thread.start()

        concatenator_thread = threading.Thread(target=self._run_concatenator)
        concatenator_thread.start()

        writer_thread = threading.Thread(target=self._run_writer)
        writer_thread.start()

        monitor_thread = threading.Thread(target=self._run_monitor)
        monitor_thread.start()

        time.sleep(5)

        logging.info("Setting up messaging system")
        messaging_system = ZMQMessagingSystem("localhost", self.registry_port, 9006)
        messager = Messager()
        control_stream = messager.get_stream(messaging_system, "control", StringMessage)
        configuration_stream = messager.get_stream(messaging_system, "configuration", ConfigurationMessage)
        logging.info("Registering to publish on 'configuration' topic.")
        configuration_endpoint = configuration_stream.get_write_endpoint()
        time.sleep(5)
        logging.info("Publishing ConfigurationMessage")
        configuration_message = ConfigurationMessage({"letter1_generator_service.upper": True, "string_writer_service.output_path": "output.txt"})
        messager.publish(configuration_endpoint, configuration_message)

        time.sleep(5)
        logging.info("Registering to publish on 'control' topic")
        control_endpoint = control_stream.get_write_endpoint()
        time.sleep(5)
        logging.info("Publishing 'Start' control message")
        messager.publish(control_endpoint, StringMessage("Start"))

        time.sleep(20)

        logging.info("Publishing 'Stop' control message")
        messager.publish(control_endpoint, StringMessage("Stop"))

        time.sleep(5)

        logging.info("Stopping services")
        self.letter1_stopped = True
        self.letter2_stopped = True
        self.concatenator_stopped = True
        self.writer_stopped = True
        self.monitor_stopped = True

        time.sleep(10)

        registry.stop()

if __name__ == '__main__':
    unittest.main()

