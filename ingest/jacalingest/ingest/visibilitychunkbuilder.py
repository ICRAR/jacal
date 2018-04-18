import logging
import struct

import casacore

from jacalingest.ingest.tosmetadata import TOSMetadata
from jacalingest.ingest.visibilitychunk import VisibilityChunk

class VisibilityChunkBuilder():

    def __init__(self, number_of_antennas, number_of_channels, stokes, period, maximum_number_of_beams, baseline_antenna_indices=None):
        self.number_of_antennas = number_of_antennas
        self.number_of_channels = number_of_channels
        self.stokes = stokes
        self.period = period
        self.maximum_number_of_beams = maximum_number_of_beams

        self.number_of_baselines = self.number_of_antennas * (1+self.number_of_antennas) / 2
        self.number_of_rows = self.number_of_baselines * self.maximum_number_of_beams
        self.current_chunk = None

        self._init_baseline_map()
        if baseline_antenna_indices is not None:
            self._slice_baseline_map(baseline_antenna_indices)

        self._init_beam_map(self.maximum_number_of_beams)

    def has_chunk(self):
        return (self.current_chunk is not None)

    def clear_chunk(self):
        self.current_chunk = None

    def get_chunk(self):
        return self.current_chunk

    def new_chunk(self, tos_metadata):
        logging.debug("Creating new chunk with timestamp {}".format(tos_metadata.timestamp))
        self.current_chunk = VisibilityChunk(self.number_of_rows, self.number_of_channels, len(self.stokes), self.number_of_antennas, self.period / 1000 / 1000, self.maximum_number_of_beams)

        middle_timestamp = tos_metadata.timestamp + self.period / 2
        dm = casacore.measures.measures()
        tai_time = dm.epoch("TAI", "{}us".format(middle_timestamp))
        utc_time = dm.measure(tai_time, 'UTC')
        utc_quantity = dm.get_value(utc_time)[0]
        utc_seconds = utc_quantity.get_value("s")
        self.current_chunk.set_time(utc_seconds)

        self.current_chunk.set_scan_id(tos_metadata.scanid)
        self.current_chunk.set_flagged(tos_metadata.flagged)
        self.current_chunk.set_sky_frequency(tos_metadata.sky_frequency)
        self.current_chunk.set_target_name(tos_metadata.target_name)
        self.current_chunk.set_target_direction(tos_metadata.target_ra, tos_metadata.target_dec)
        self.current_chunk.set_phase_direction(tos_metadata.phase_ra, tos_metadata.phase_dec)
        self.current_chunk.set_corr_mode(tos_metadata.corrmode)
        self.current_chunk.set_antennas(tos_metadata.antennas)

  
    def add_visibilities(self, visibility_datagram):
        logging.debug("The first three visibilities are {}, {}, {}.".format(visibility_datagram.get_visibility(0), visibility_datagram.get_visibility(1), visibility_datagram.get_visibility(2)))
        channel = self._map_channel(visibility_datagram.channel-1)
        logging.debug("Mapped channel from {} to {}".format(visibility_datagram.channel, channel))

        logging.debug("Adding visibilities for baselines {} through {}".format(visibility_datagram.baseline1, visibility_datagram.baseline2))
        for i in range(visibility_datagram.baseline2-visibility_datagram.baseline1+1):
            product = i + visibility_datagram.baseline1
            logging.debug("Calling map_corr_product with product {}, beam id {}.".format(product, visibility_datagram.beam_id))
            product = self._map_corr_product(product, visibility_datagram.beam_id)
            if product is not None:
                (row, polarisation_index) = product
                logging.debug("Row is {}, polarisation index is {}".format(row, polarisation_index))
                logging.debug("Setting visibility for (row, channel, polarisation_index) ({}, {}, {}) to {}.".format(row, channel, polarisation_index, visibility_datagram.get_visibility(i)))
                self.current_chunk.set_visibility(row, channel, polarisation_index, visibility_datagram.get_visibility(i))


    # hardcoded logic for now, like ASKAPsoft does
    def _map_channel(self, channel_id):
        fine_offset = channel_id % 9
        group = channel_id // 9
        chip = group // 4
        coarse_channel = group % 4

        return fine_offset + chip * 9 + coarse_channel * 54

    def _init_baseline_map(self, number_of_antennas=36):
        logging.debug("In _init_baseline_map with {}".format(number_of_antennas))
        self.baseline_map = dict()
        baseline = 0
        for antenna2 in range(number_of_antennas):
            for antenna1 in range(antenna2):
                baseline += 1
                self.baseline_map[baseline] = (antenna1, antenna2, "XX")
                baseline += 1
                self.baseline_map[baseline] = (antenna1, antenna2, "YX")
            baseline += 1
            self.baseline_map[baseline] = (antenna2, antenna2, "XX")
            for antenna1 in range(antenna2+1):
                baseline += 1
                self.baseline_map[baseline] = (antenna1, antenna2, "XY")
                baseline += 1
                self.baseline_map[baseline] = (antenna1, antenna2, "YY")
        logging.debug("Initialized baseline map to {}".format(self.baseline_map))

    def _slice_baseline_map(self, baseline_antenna_indices):
        logging.debug("In _slice_baseline_map with {}".format(baseline_antenna_indices))
        new_map = dict()

        for (id, (antenna1, antenna2, stokes)) in self.baseline_map.iteritems():
            new_index1 = -1
            new_index2 = -1
            for index, antenna_index in enumerate(baseline_antenna_indices):
                if antenna_index == antenna1:
                    new_index1 = index
                if antenna_index == antenna2:
                    new_index2 = index
            if (new_index1 >= 0) and (new_index2 >= 0):
                new_map[id] = (new_index1, new_index2, stokes)

        self.baseline_map = new_map
        logging.debug("Sliced baseline map to {}".format(self.baseline_map))
    
    #def _init_beam_map(self, number_of_feeds, max_beam_id):
    def _init_beam_map(self, number_of_feeds):
        #beams_to_receive = min(number_of_feeds, max_beam_id)
        beams_to_receive = number_of_feeds

        self._beam_map = dict()
        for beam in range(1, beams_to_receive+1):
            self._beam_map[beam] = beam-1

         
    def _map_corr_product(self, baseline, beam):
        if baseline not in self.baseline_map:
            return None

        (antenna1, antenna2, stokes) = self.baseline_map[baseline]
        beam_id = self._beam_map[beam]
        logging.debug("In map_corr_product, antenna1 is {}, antenna2 is {}, beam_id is {}.".format(antenna1, antenna2, beam_id))
        polarisation_index = self._map_stokes(stokes)
        row = self._calculate_row(antenna1, antenna2, beam_id)
        return (row, polarisation_index)

    def _calculate_row(self, antenna1, antenna2, beam):
        return (beam * self.number_of_antennas * (self.number_of_antennas+1) / 2) + (antenna1 * self.number_of_antennas - (antenna1*(antenna1-1)/2))+antenna2

    def _map_stokes(self, stokes):
        return self.stokes.index(stokes)

