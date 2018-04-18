import logging
import time
import unittest

from jacalingest.engine.servicerunnerfactory import ServiceRunnerFactory
from jacalingest.engine.configuration.configurationmessage import ConfigurationMessage
from jacalingest.engine.messaging.messager import Messager
from jacalingest.engine.messaging.queuemessagingsystem import QueueMessagingSystem
from jacalingest.ingest.visibilitydatagramsourceservice import VisibilityDatagramSourceService
from jacalingest.ingest.visibilitydatagram import VisibilityDatagram
from jacalingest.stringdomain.tostringservice import ToStringService
from jacalingest.stringdomain.stringmessage import StringMessage
from jacalingest.stringdomain.stringwriterservice import StringWriterService
from jacalingest.testbed.icerunner import IceRunner
from jacalingest.testbed.playback import Playback

class TestVisibilityDatagramSourceService(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        logging.basicConfig(level=logging.INFO, format='%(threadName)s, %(module)s: %(message)s')



    def test(self):
        messaging_system = QueueMessagingSystem()
        messager = Messager()

        configuration_stream = messager.get_stream(messaging_system, "configuration", ConfigurationMessage)
        control_stream = messager.get_stream(messaging_system, "control", StringMessage)

        service_runner_factory = ServiceRunnerFactory(messager)

        visibility_stream = messager.get_stream(messaging_system, "visibility", VisibilityDatagram)
        visibility_datagram_source_service_runner = service_runner_factory.get_service_runner(VisibilityDatagramSourceService, {"name": "visibility_datagram_source_service", "visibility_datagram_endpoint":visibility_stream.get_endpoint(), "control_endpoint":control_stream.get_endpoint()}, configuration_stream=configuration_stream)

        visibility_string_stream = messager.get_stream(messaging_system, "visibilitystring", StringMessage)
        tostring_service_runner = service_runner_factory.get_service_runner(ToStringService, {"name":"tostring_service", "input_endpoint":visibility_stream.get_endpoint(), "output_endpoint":visibility_string_stream.get_endpoint(), "control_endpoint":control_stream.get_endpoint()}, configuration_stream=configuration_stream)


        string_writer_service_runner = service_runner_factory.get_service_runner(StringWriterService, {"name":"string_writer_service", "string_endpoint":visibility_string_stream.get_endpoint(), "control_endpoint":control_stream.get_endpoint()}, configuration_stream=configuration_stream)


        # start Ice
        logging.info("Starting Ice")
        ice_runner = IceRunner("testbed_data")
        ice_runner.start()

        time.sleep(5)

        logging.info("Starting services")
        string_writer_service_runner.start()
        tostring_service_runner.start()
        visibility_datagram_source_service_runner.start()
    
        time.sleep(5)

        logging.info("Publishing configuration")
        mainline_configuration_endpoint = configuration_stream.get_endpoint()

        configuration_message = ConfigurationMessage({"antennas": {"ant2": {"name": "ak02",
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
                                                   "itrf": (-2555888.891875,5097552.280516,-2848324.679547)}},
                               "metadata_source": {"host": "localhost",
                                                   "port": "4061",
                                                   "topicmanager": "IceStorm/TopicManager@IceStorm.TopicManager",
                                                   "topic": "metadata",
                                                   "adapter": "IngestPipeline"},
                               "datagram_source": {"host": "localhost",
                                                   "port": "3000"},
                               "correlation_modes": {"standard": {"channel_width": "18.518518",
                                                                  "interval": "5000000",
                                                                  "number_of_channels": "216",
                                                                  "stokes": ["XX", "XY", "YX", "YY"]}},
                               "maximum_number_of_beams": "36",
                               "string_writer_service.output_path": "output.txt"})
        messager.publish(mainline_configuration_endpoint, configuration_message)

        logging.info("Starting processing")
        mainline_control_endpoint = control_stream.get_endpoint()

        messager.publish(mainline_control_endpoint, StringMessage("Start"))

        # start playback
        logging.info("Starting playback")
        playback = Playback("testbed_data")
        playback.playback("data/ade1card.ms")
        playback.wait()

        time.sleep(10)
        messager.publish(mainline_control_endpoint, StringMessage("Stop"))

        time.sleep(10)

        visibility_datagram_source_service_runner.terminate()
        tostring_service_runner.terminate()
        string_writer_service_runner.terminate()

        # stop Ice
        logging.info("stopping Ice")
        ice_runner.stop()


if __name__ == '__main__':
    unittest.main()
