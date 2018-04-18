import logging
import Queue

import casacore.measures

from jacalingest.engine.handlerservice import HandlerService
from jacalingest.engine.configuration.configurableservice import ConfigurableService
from jacalingest.ingest.tosmetadata import TOSMetadata
from jacalingest.ingest.visibilitydatagram import VisibilityDatagram
from jacalingest.ingest.visibilitychunk import VisibilityChunk
from jacalingest.ingest.visibilitychunkbuilder import VisibilityChunkBuilder

class AlignService(HandlerService, ConfigurableService):
    IDLE_STATE = 1
    PROCESSING_STATE = 2

    def __init__(self, **kwargs):
        logging.info("Initializing")

        super(AlignService, self).__init__(initial_state=self.IDLE_STATE, **kwargs)

        self.set_handler(self.get_parameter("metadata_endpoint"), self.handle_tos_metadata, [self.PROCESSING_STATE])
        self.set_handler(self.get_parameter("datagram_endpoint"), self.handle_visibility_datagram, [self.PROCESSING_STATE])
        self.set_handler(self.get_parameter("control_endpoint"), self.handle_control, [self.IDLE_STATE, self.PROCESSING_STATE])

        self.chunk_endpoint = self.get_parameter("chunk_endpoint")
        assert self.chunk_endpoint is not None

        self.tos_draining = False
        self.vis_draining = False

        self.metadata_queue = Queue.Queue()
        self.datagram_queue = Queue.Queue()

        self.current_visibility = None

        self.number_of_antennas = len(self.get_configuration("antennas"))
        self.number_of_channels = int(self._configuration["correlation_modes"]["standard"]["number_of_channels"])
        self.stokes = self._configuration["correlation_modes"]["standard"]["stokes"]
        self.period = int(self._configuration["correlation_modes"]["standard"]["interval"])
        self.maximum_number_of_beams = int(self.get_configuration("maximum_number_of_beams"))
        if self._configuration["baseline_map"]["antennaindices"] is None:
            baseline_antenna_indices = None
            logging.info("baseline_antenna_indices is None")
        else:
            baseline_antenna_indices = [int(s) for s in self._configuration["baseline_map"]["antennaindices"]]
            logging.info("baseline_antenna_indices is {}".format(baseline_antenna_indices))

        number_of_baselines = self.number_of_antennas * (1+self.number_of_antennas) / 2
        self.number_of_rows = number_of_baselines * self.maximum_number_of_beams

        self.visibility_chunk_builder = VisibilityChunkBuilder(self.number_of_antennas, self.number_of_channels, self.stokes, self.period, self.maximum_number_of_beams, baseline_antenna_indices=baseline_antenna_indices)


    def handle_control(self, message, state):
        command = message.get_payload()
        if command == "Start":
            logging.info("Received 'Start' control message")
            return self.PROCESSING_STATE
        elif command == "Stop":
            logging.info("Received 'Stop' control message")
            return self.IDLE_STATE
        else:
            logging.info("Received unknown command: {}".format(command))
            return state

    def handle_tos_metadata(self, message, state):
        logging.debug("Queueing TOS metadata")
        self.metadata_queue.put(message)
        self.do_align()
        return state

    def handle_visibility_datagram(self, message, state):
        logging.debug("Queueing visibility datagram")
        self.datagram_queue.put(message)
        self.do_align()
        return state

    def do_align(self):
        logging.debug("Commencing do_align")

        logging.debug("Checking for a current chunk....")
        if not self.visibility_chunk_builder.has_chunk():
            logging.debug("No current chunk; checking metadata queue...")
            if not self.metadata_queue.empty():
               tos_metadata = self.metadata_queue.get_nowait()
               logging.info("Received TOS metadata with timestamp {}".format(tos_metadata.timestamp))

               self.current_timestamp = tos_metadata.timestamp
               self.visibility_chunk_builder.new_chunk(tos_metadata)

        logging.debug("Checking for a current visibility....")
        if self.current_visibility is None:
            logging.debug("No current visibility; checking visibilty queue...")
            if not self.datagram_queue.empty():
                self.current_visibility = self.datagram_queue.get_nowait()
                logging.debug("Received visibility with timestamp {}".format(self.current_visibility.timestamp))

        #if not self.visibility_chunk_builder.has_chunk() and self.current_visibility is not None:
            #logging.debug("No message on either stream.")

        if self.visibility_chunk_builder.has_chunk() and self.current_visibility is not None:
            if self.current_timestamp < self.current_visibility.timestamp:
                logging.info("Newer visibility triggers sending of chunk ({} < {})".format(self.current_timestamp, self.current_visibility.timestamp))
                self.messager.publish(self.chunk_endpoint, self.visibility_chunk_builder.get_chunk())
                self.visibility_chunk_builder.clear_chunk()
                self.current_timestamp = None # don't really need to do this
            else:
                if self.current_timestamp == self.current_visibility.timestamp:
                    logging.debug("Adding a visibility to the current chunk ({} = {})".format(self.current_timestamp, self.current_visibility.timestamp))
                    self.visibility_chunk_builder.add_visibilities(self.current_visibility)
                else:
                    logging.info("Discarding an old visibility ({} > {})".format(self.current_timestamp, self.current_visibility.timestamp))
                self.current_visibility = None


