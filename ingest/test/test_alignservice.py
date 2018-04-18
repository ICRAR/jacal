import logging
import os
import time
import unittest

from jacalingest.engine.configuration.configurationmessage import ConfigurationMessage
from jacalingest.engine.servicerunner import ServiceRunner
from jacalingest.engine.servicerunnerfactory import ServiceRunnerFactory
from jacalingest.engine.messaging.messager import Messager
from jacalingest.engine.messaging.queuemessagingsystem import QueueMessagingSystem
from jacalingest.engine.monitoringandcontrol.genericmonitorservice import GenericMonitorService
from jacalingest.engine.monitoringandcontrol.metrics import Metrics
from jacalingest.engine.monitoringandcontrol.monitoradapter import MonitorAdapter
from jacalingest.ingest.alignservice import AlignService
from jacalingest.ingest.icemetadatasourceservice import IceMetadataSourceService
from jacalingest.ingest.tosmetadata import TOSMetadata
from jacalingest.ingest.visibilitychunk import VisibilityChunk
from jacalingest.ingest.visibilitydatagram import VisibilityDatagram
from jacalingest.ingest.visibilitydatagramsourceservice import VisibilityDatagramSourceService
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

        chunk_string_stream = messager.get_stream(messaging_system, "chunkstring", StringMessage)
        to_string_metrics_stream = messager.get_stream(messaging_system, "to_stringmetrics", Metrics)
        to_string_service_runner = service_runner_factory.get_service_runner(ToStringService, {"name": "to_string_service", "input_endpoint":chunk_stream.get_read_endpoint(), "output_endpoint": chunk_string_stream.get_write_endpoint(), "control_endpoint":control_stream.get_read_endpoint()}, metrics_stream=to_string_metrics_stream, configuration_stream=configuration_stream)

        string_writer_metrics_stream = messager.get_stream(messaging_system, "stringwritermetrics", Metrics)
        string_writer_service_runner = service_runner_factory.get_service_runner(StringWriterService, {"name": "string_writer_service", "string_endpoint": chunk_string_stream.get_read_endpoint(), "control_endpoint":control_stream.get_read_endpoint()}, metrics_stream=string_writer_metrics_stream, configuration_stream=configuration_stream)

        monitor_service = GenericMonitorService("generic_monitor_service", [datagram_metrics_stream.get_read_endpoint(), metadata_metrics_stream.get_read_endpoint(), align_metrics_stream.get_read_endpoint(), to_string_metrics_stream.get_read_endpoint(), string_writer_metrics_stream.get_read_endpoint()])
        monitor_service_runner = ServiceRunner(monitor_service, messager)

        # start Ice
        logging.info("Starting Ice")
        ice_runner = IceRunner("testbed_data")
        ice_runner.start()
    
    
        logging.info("Starting services")
        monitor_service_runner.start()
        visibility_datagram_source_service_runner.start()
        ice_metadata_source_service_runner.start()
        align_service_runner.start()
        to_string_service_runner.start()
        string_writer_service_runner.start()
    
        logging.info("Publishing configuration")
        mainline_configuration_endpoint = configuration_stream.get_write_endpoint()

        antennas = {"ant2": {"name": "ak02",
                             "itrf": (-2556109.976515, 5097388.699862, -2848440.12097248)},
                    "ant4": {"name": "ak04",
                             "itrf": (-2556087.396082, 5097423.589662, -2848396.867933)},
                    "ant5": {"name": "ak05",
                             "itrf": (-2556028.607336, 5097451.468188, -2848399.83113161)},
                    "ant10": {"name": "ak10",
                              "itrf": (-2556059.228687, 5097560.766055, -2848178.119367)},
                    "ant12": {"name": "ak12",
                              "itrf": (-2556496.237175, 5097333.724901, -2848187.33832738)},
                    # other to get 12-antennas
                    "ant7": {"name": "ak07",
                             "itrf": (-2556282.880670, 5097252.290820, -2848527.104272)},
                    "ant11": {"name": "ak11",
                              "itrf": (-2556397.233607, 5097421.429903, -2848124.497319)},
                    # old BETA antennas
                    "ant1": {"name": "ak01",
                             "itrf": (-2556084.669, 5097398.337, -2848424.133)},
                    "ant15": {"name": "ak15",
                              "itrf": (-2555389.850372, 5097664.627578, -2848561.95991566)},
                    "ant3": {"name": "ak03",
                             "itrf": (-2556118.109261, 5097384.719695, -2848417.19642608)},
                    "ant6": {"name": "ak06",
                             "itrf": (-2556227.878593, 5097380.442223, -2848323.44598377)},
                    "ant8": {"name": "ak08",
                             "itrf": (-2556002.509816,5097320.293832,-2848637.482106)},
                    "ant9": {"name": "ak09",
                             "itrf": (-2555888.891875,5097552.280516,-2848324.679547)}}

        configuration= {"antennas": antennas,
                        "baseline_map": {"name": "standard",
                                        "antennaidx": ["ak02", "ak04", "ak05", "ak12"],
                                        "antennaindices": [1, 3, 4, 11]},
                        "metadata_source": {"host": "localhost",
                                            "port": "4061",
                                            "topic_manager": "IceStorm/TopicManager@IceStorm.TopicManager",
                                            "topic": "metadata",
                                            "adapter": "IngestPipeline"},
                        "datagram_source": {"host": "localhost",
                                            "port": "3000"},
                        "correlation_modes": {"standard": {"channel_width": "18.518518",
                                                           "interval": "5000000",
                                                           "number_of_channels": "216",
                                                           "stokes": ["XX", "XY", "YX", "YY"]}},
                        "maximum_number_of_beams": "36",
                        "string_writer_service.output_path": "output.txt"}

        configuration_message = ConfigurationMessage(configuration)
        messager.publish(mainline_configuration_endpoint, configuration_message)

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
        to_string_service_runner.terminate()
        string_writer_service_runner.terminate()
        monitor_service_runner.terminate()
    
        # trying to force garbage collection
        ice_metadata_source_service_runner = None
        visibility_datagram_source_service_runner = None
        align_service_runner = None
        to_string_service_runner = None
        string_writer_service_runner = None
        monitor_service_runner = None
        playback = None
        messaging_system = None
        messager = None

        # stop Ice
        logging.info("stopping Ice")
        ice_runner.stop()
    
    
    
if __name__ == '__main__':
    unittest.main()
    
