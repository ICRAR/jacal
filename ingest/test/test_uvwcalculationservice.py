import logging
import os
import time
import unittest

from jacalingest.engine.servicerunner import ServiceRunner
from jacalingest.engine.servicerunnerfactory import ServiceRunnerFactory
from jacalingest.engine.configuration.configurationmessage import ConfigurationMessage
from jacalingest.ingest.hardconfigurationservice import HardConfigurationService
from jacalingest.engine.messaging.messager import Messager
from jacalingest.engine.messaging.queuemessagingsystem import QueueMessagingSystem
from jacalingest.engine.monitoringandcontrol.genericmonitorservice import GenericMonitorService
from jacalingest.engine.monitoringandcontrol.metrics import Metrics
from jacalingest.engine.monitoringandcontrol.monitoradapter import MonitorAdapter
from jacalingest.ingest.visibilitydatagram import VisibilityDatagram
from jacalingest.ingest.visibilitydatagramsourceservice import VisibilityDatagramSourceService
from jacalingest.ingest.icemetadatasourceservice import IceMetadataSourceService
from jacalingest.ingest.tosmetadata import TOSMetadata
from jacalingest.ingest.visibilitychunk import VisibilityChunk
from jacalingest.ingest.alignservice import AlignService
from jacalingest.ingest.uvwchunk import UVWChunk
from jacalingest.ingest.uvwcalculationservice import UVWCalculationService

from jacalingest.stringdomain.stringmessage import StringMessage
from jacalingest.stringdomain.stringwriterservice import StringWriterService
from jacalingest.stringdomain.tostringservice import ToStringService
from jacalingest.testbed.icerunner import IceRunner
from jacalingest.testbed.playback import Playback

class TestAlignService(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        logging.basicConfig(level=logging.INFO, format='%(threadName)s, %(module)s: %(message)s')


    def test(self):
        messaging_system = QueueMessagingSystem()
        messager = Messager()

        service_runner_factory = ServiceRunnerFactory(messager)

        configuration_stream = messager.get_stream(messaging_system, "configuration", ConfigurationMessage)
        control_stream = messager.get_stream(messaging_system, "control", StringMessage)

        metadata_stream = messager.get_stream(messaging_system, "metadata", TOSMetadata)
        metadata_metrics_stream = messager.get_stream(messaging_system, "metadatametrics", Metrics)

        ice_metadata_source_service_runner = service_runner_factory.get_service_runner(IceMetadataSourceService, {"name":"ice_metadata_source_service", "metadata_endpoint": metadata_stream.get_write_endpoint(), "control_endpoint": control_stream.get_read_endpoint()}, metrics_stream = metadata_metrics_stream, configuration_stream=configuration_stream)

        datagram_stream = messager.get_stream(messaging_system, "datagram", VisibilityDatagram)
        datagram_metrics_stream = messager.get_stream(messaging_system, "datagrammetrics", Metrics)
        visibility_datagram_source_service_runner = service_runner_factory.get_service_runner(VisibilityDatagramSourceService, {"name": "visibility_datagram_source_service", "visibility_datagram_endpoint":datagram_stream.get_write_endpoint(), "control_endpoint":control_stream.get_read_endpoint()}, metrics_stream=datagram_metrics_stream, configuration_stream=configuration_stream)

        # set up the align service
        chunk_stream = messager.get_stream(messaging_system, "chunk", VisibilityChunk)
        align_metrics_stream = messager.get_stream(messaging_system, "alignmetrics", Metrics)
        align_service_runner = service_runner_factory.get_service_runner(AlignService, {"name": "align_service", "datagram_endpoint": datagram_stream.get_read_endpoint(), "metadata_endpoint": metadata_stream.get_read_endpoint(), "chunk_endpoint":chunk_stream.get_write_endpoint(), "control_endpoint":control_stream.get_read_endpoint()}, metrics_stream=align_metrics_stream, configuration_stream=configuration_stream)

        # set up the uvwcalculation service
        uvw_chunk_stream = messager.get_stream(messaging_system, "uvwchunk", UVWChunk)
        uvw_calculation_metrics_stream = messager.get_stream(messaging_system, "uvwcalcmetrics", Metrics)
        uvw_calculation_service_runner = service_runner_factory.get_service_runner(UVWCalculationService, {"name": "uvw_calculation_service", "observatory_name": "ASKAP", "visibility_chunk_endpoint": chunk_stream.get_read_endpoint(), "metadata_endpoint": metadata_stream.get_read_endpoint(), "uvw_chunk_endpoint":uvw_chunk_stream.get_write_endpoint(), "control_endpoint":control_stream.get_read_endpoint()}, metrics_stream=uvw_calculation_metrics_stream, configuration_stream=configuration_stream)

        uvw_chunk_string_stream = messager.get_stream(messaging_system, "chunkstring", StringMessage)
        to_string_metrics_stream = messager.get_stream(messaging_system, "to_stringmetrics", Metrics)
        to_string_service_runner = service_runner_factory.get_service_runner(ToStringService, {"name": "to_string_service", "input_endpoint":uvw_chunk_stream.get_read_endpoint(), "output_endpoint": uvw_chunk_string_stream.get_write_endpoint(), "control_endpoint":control_stream.get_read_endpoint()}, metrics_stream=to_string_metrics_stream, configuration_stream=configuration_stream)

        string_writer_metrics_stream = messager.get_stream(messaging_system, "stringwritermetrics", Metrics)
        string_writer_service_runner = service_runner_factory.get_service_runner(StringWriterService, {"name": "string_writer_service", "string_endpoint": uvw_chunk_string_stream.get_read_endpoint(), "control_endpoint":control_stream.get_read_endpoint()}, metrics_stream=string_writer_metrics_stream, configuration_stream=configuration_stream)

        monitor_service = GenericMonitorService("generic_monitor_service", [datagram_metrics_stream.get_read_endpoint(), metadata_metrics_stream.get_read_endpoint(), align_metrics_stream.get_read_endpoint(), uvw_calculation_metrics_stream.get_read_endpoint(), to_string_metrics_stream.get_read_endpoint(), string_writer_metrics_stream.get_read_endpoint()])
        monitor_service_runner = ServiceRunner(monitor_service, messager)

        configuration_control_stream = messager.get_stream(messaging_system, "configurationcontrol", StringMessage)
        configuration_service = HardConfigurationService("configuration_service", configuration_control_stream.get_read_endpoint(), configuration_stream.get_write_endpoint())
        configuration_service_runner = ServiceRunner(configuration_service, messager)


        # start Ice
        logging.info("Starting Ice")
        ice_runner = IceRunner("testbed_data")
        ice_runner.start()
    
        logging.info("Starting services")
        configuration_service_runner.start()
        monitor_service_runner.start()
        visibility_datagram_source_service_runner.start()
        ice_metadata_source_service_runner.start()
        align_service_runner.start()
        uvw_calculation_service_runner.start()
        to_string_service_runner.start()
        string_writer_service_runner.start()

        logging.info("Publishing configuration")
        mainline_configuration_control_endpoint = configuration_control_stream.get_write_endpoint()

        logging.info("Issuing configuration")
        messager.publish(mainline_configuration_control_endpoint, StringMessage("Start"))

        time.sleep(10)

        logging.info("Starting processing")
        mainline_control_endpoint = control_stream.get_write_endpoint()
        messager.publish(mainline_control_endpoint, StringMessage("Start"))

        # start playback
        logging.info("Starting playback")
        playback = Playback("testbed_data")
        playback.playback("data/ade1card.ms")
        playback.wait()
    
        time.sleep(10)

        messager.publish(mainline_control_endpoint, StringMessage("Stop"))

        time.sleep(10)
    
        ice_metadata_source_service_runner.terminate()
        visibility_datagram_source_service_runner.terminate()
        align_service_runner.terminate()
        uvw_calculation_service_runner.terminate()
        to_string_service_runner.terminate()
        string_writer_service_runner.terminate()
        monitor_service_runner.terminate()
        configuration_service_runner.terminate()
    
        # stop Ice
        logging.info("stopping Ice")
        ice_runner.stop()
    
    
    
if __name__ == '__main__':
    unittest.main()
    
