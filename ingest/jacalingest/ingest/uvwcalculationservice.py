import logging
import math
import numpy

import casacore.measures

from jacalingest.engine.handlerservice import HandlerService
from jacalingest.engine.configuration.configurableservice import ConfigurableService
from jacalingest.ingest.uvwchunk import UVWChunk
from jacalingest.ingest.visibilitychunk import VisibilityChunk

class UVWCalculationService(HandlerService, ConfigurableService):
    IDLE_STATE = 1
    PROCESSING_STATE = 2

    def __init__(self, **kwargs):
        logging.info("Initializing")

        super(UVWCalculationService, self).__init__(initial_state=self.IDLE_STATE, **kwargs)

        visibility_chunk_endpoint = self.get_parameter("visibility_chunk_endpoint")
        assert visibility_chunk_endpoint is not None
        self.set_handler(visibility_chunk_endpoint, self.handle_visibility_chunk, [self.PROCESSING_STATE])

        control_endpoint = self.get_parameter("control_endpoint")
        assert control_endpoint is not None
        self.set_handler(control_endpoint, self.handle_control, [self.IDLE_STATE, self.PROCESSING_STATE])

        self.uvw_chunk_endpoint = self.get_parameter("uvw_chunk_endpoint")
        assert self.uvw_chunk_endpoint is not None

        self.dm = casacore.measures.measures()
        self.observatory_name = self.get_parameter("observatory_name")
        observatory_position = self.dm.observatory(self.observatory_name)
        self.observatory_position_itrf = self.dm.measure(observatory_position, "ITRF")
        self.dm.do_frame(self.observatory_position_itrf)

        self.observatory_position_long = self.dm.get_value(self.observatory_position_itrf)[0].get_value("rad")
        self.observatory_position_lat = self.dm.get_value(self.observatory_position_itrf)[1].get_value("rad")

        logging.info("{} ITRF position measure: {}".format(self.observatory_name, self.observatory_position_itrf))

        self.antenna_xyz = list()
        antennas = self.get_configuration("antennas")
        antenna_numbers = sorted(int(a[3:]) for a in antennas)
        for antenna_number in antenna_numbers:
            self.antenna_xyz.append(antennas["ant{}".format(antenna_number)]["itrf"])

        self.beam_offsets = list()
        feeds = self.get_configuration("feeds")
        self.number_of_feeds = int(feeds["number_of_feeds"])
        for f in range(self.number_of_feeds):
            self.beam_offsets.append(feeds["feed{}".format(f)])



    def handle_control(self, message, state):
        command = message.get_payload()
        if command == "Start":
            logging.info("Received 'Start' control message")
            return self.PROCESSING_STATE
        elif command == "Stop":
            logging.info("Received 'Stop' control message")
            return self.IDLE_STATE
        else:
            logging.info("Received unknown control message: {}".format(command))
            return state


    def handle_visibility_chunk(self, visibility_chunk, state):
        epoch = self.dm.epoch("UTC", "{}s".format(visibility_chunk.get_time()))
        self.dm.do_frame(epoch)
        
        (dish_ra, dish_dec) = visibility_chunk.get_phase_direction()
        #logging.info("Dish pointing J2000 (ra, dec) is ({}, {})".format(dish_ra, dish_dec))
        dish_pointing = self.dm.direction("J2000", "{}deg".format(dish_ra), "{}deg".format(dish_dec))
        ##logging.info("Dish pointing J2000 is {})".format(dish_pointing))

        uvw_chunk = UVWChunk.create_from_visibility_chunk(visibility_chunk)

        for row in range(visibility_chunk.get_number_of_rows()):
            beam1 = visibility_chunk.get_beam1(row)
            (beam_offset_ra, beam_offset_dec) = self.beam_offsets[beam1]

            phase_centre_j2000 = self.dm.direction("J2000", "{}rad".format(dish_ra-beam_offset_ra), "{}rad".format(dish_dec+beam_offset_dec))
            phase_centre_hadec = self.dm.measure(phase_centre_j2000, "HADEC")
            self.dm.do_frame(phase_centre_hadec)

            phase_centre_long = self.dm.get_value(phase_centre_hadec)[0].get_value("rad")
            phase_centre_lat = self.dm.get_value(phase_centre_hadec)[1].get_value("rad")
            #logging.info("Phase centre is ({}, {})".format(phase_centre_long, phase_centre_lat))

            #h0 = phase_centre_long - self.observatory_position_long
            #dec = phase_centre_lat
            ##logging.info("(h0, dec) = ({},{})".format(h0, dec))

            #sh0 = math.sin(h0)
            #ch0 = math.cos(h0)
            #sd = math.sin(dec)
            #cd = math.cos(dec)

            #transform_matrix = numpy.array([[-sh0, -ch0, 0],
                                            #[sd*ch0, -sd*sh0, -cd],
                                            #[-cd*ch0, cd*sh0, -sd]])
            ##logging.info("transform_matrix is {}".format(transform_matrix))

            antenna1 = visibility_chunk.get_antenna1(row)
            antenna1_xyz = numpy.array(self.antenna_xyz[antenna1])
            #logging.info("antenna1 is {}".format(antenna1_xyz))

            antenna2 = visibility_chunk.get_antenna2(row)
            antenna2_xyz = numpy.array(self.antenna_xyz[antenna2])
            #logging.info("antenna2 is {}".format(antenna2_xyz))

            baseline = antenna2_xyz-antenna1_xyz
            #logging.info("baseline is {}".format(baseline))
            baseline_itrf = self.dm.baseline('j2000', "{}m".format(baseline[0]), "{}m".format(baseline[1]), "{}m".format(baseline[2]))

            uvw = self.dm.to_uvw(baseline_itrf)
            #logging.info("uvw is {}".format(uvw['measure']))

            #rotated_baseline = transform_matrix.dot(baseline)
            ##logging.info("rotated_baseline is {}".format(rotated_baseline))

            #rotated_baseline_itrf = self.dm.baseline('j2000', "{}m".format(rotated_baseline[0]), "{}m".format(rotated_baseline[1]), "{}m".format(rotated_baseline[2]))
            #uvw = self.dm.to_uvw(rotated_baseline_itrf)
            ##logging.info("uvw is {}".format(uvw))

            u = self.dm.get_value(uvw['measure'])[0].get_value()
            v = self.dm.get_value(uvw['measure'])[1].get_value()
            w = self.dm.get_value(uvw['measure'])[2].get_value()
            #logging.info("UVW is ({}, {}, {})".format(u, v, w))
            uvw_chunk.set_uvw(row, u, v, w)


        self.messager.publish(self.uvw_chunk_endpoint, uvw_chunk)
        logging.info("Published a UVW Chunk.")
        return state
