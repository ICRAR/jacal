import logging

from jacalingest.engine.configuration.configurationmessage import ConfigurationMessage
from jacalingest.engine.handlerservice import HandlerService

class HardConfigurationService(HandlerService):
    RUNNING_STATE=1

    def __init__(self, name, control_endpoint, configuration_endpoint, **kwargs):
        super(HardConfigurationService, self).__init__(name=name, initial_state=self.RUNNING_STATE, **kwargs)

        self.set_handler(control_endpoint, self.handle_control, [self.RUNNING_STATE])
        self.configuration_endpoint = configuration_endpoint

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

        self.configuration = {"antennas": antennas,
                         "baseline_map": {"name": "standard",
                                          "antennaidx": ["ak02", "ak04", "ak05", "ak12"],
                                          "antennaindices": [1, 3, 4, 11]},
                         "feeds": {"number_of_feeds": "36",
                                   "feed0": (0, 0),
                                   "feed1": (0, 0),
                                   "feed2": (0, 0),
                                   "feed3": (0, 0),
                                   "feed4": (0, 0),
                                   "feed5": (0, 0),
                                   "feed6": (0, 0),
                                   "feed7": (0, 0),
                                   "feed8": (0, 0),
                                   "feed9": (0, 0),
                                   "feed10": (0, 0),
                                   "feed11": (0, 0),
                                   "feed12": (0, 0),
                                   "feed13": (0, 0),
                                   "feed14": (0, 0),
                                   "feed15": (0, 0),
                                   "feed16": (0, 0),
                                   "feed17": (0, 0),
                                   "feed18": (0, 0),
                                   "feed19": (0, 0),
                                   "feed20": (0, 0),
                                   "feed21": (0, 0),
                                   "feed22": (0, 0),
                                   "feed23": (0, 0),
                                   "feed24": (0, 0),
                                   "feed25": (0, 0),
                                   "feed26": (0, 0),
                                   "feed27": (0, 0),
                                   "feed28": (0, 0),
                                   "feed29": (0, 0),
                                   "feed30": (0, 0),
                                   "feed31": (0, 0),
                                   "feed32": (0, 0),
                                   "feed33": (0, 0),
                                   "feed34": (0, 0),
                                   "feed35": (0, 0)},
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
                         "socket_writer_service": {"host": "localhost",
                                                   "port": "10001"},
                         "socket_reader_service": {"host": "localhost",
                                                   "port": "10001"},
                         "string_writer_service.output_path": "output.txt"}
        self.configuration_message = ConfigurationMessage(self.configuration)

    def handle_control(self, message, state):
        command = message.get_payload()
        if command == "Start":
            logging.info("Received 'Start' control message: publishing Configuration")
            self.messager.publish(self.configuration_endpoint, self.configuration_message)
        else:
            logging.info("Received unknown control message: {}".format(command))
        return state

