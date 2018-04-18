import casacore
import logging
import math
import numpy
import unittest

class TestCasacore(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        logging.basicConfig(level=logging.INFO, format='%(threadName)s, %(module)s: %(message)s')

    def test(self):
        dm = casacore.measures.measures()

        #observatory_position_itrf = dm.position("ITRF", "{}m".format(antenna1[0]), "{}m".format(antenna1[1]), "{}m".format(antenna1[2]))
        observatory_position_itrf = dm.position("ITRF", "-2556109.976515m", "5097388.699862m", "-2848440.120972m")
        dm.do_frame(observatory_position_itrf)
        logging.info("Observatory position is {}".format(observatory_position_itrf))
        observatory_position_long = dm.get_value(observatory_position_itrf)[0].get_value("rad")
        observatory_position_lat = dm.get_value(observatory_position_itrf)[1].get_value("rad")
        logging.info("Observatory_position is ({}, {})".format(observatory_position_long, observatory_position_lat))


        timestamp = 4679920058342343
        tai_time = dm.epoch("TAI", "{}us".format(timestamp))
        utc_time = dm.measure(tai_time, 'UTC')
        logging.info("UTC time is {}".format(utc_time))

        utc_seconds = 4679920262.842344
        utc_time = dm.epoch("UTC", "{}s".format(utc_seconds))
        logging.info("Hardcoded override: UTC time is {}".format(utc_time))

        utc_quantity = dm.get_value(utc_time)[0]
        utc_seconds = utc_quantity.get_value("s")
        logging.info("UTC seconds is {}".format(utc_seconds))

        dm.do_frame(utc_time)

        antenna1 = (-2556028.607336, 5097451.468188, -2848399.831132)
        antenna2 = (-2556496.237175, 5097333.724901, -2848187.338327)


        beam_offset = (0, 0)
        logging.info("Beam offset is {}".format(beam_offset))

        (dish_pointing_ra, dish_pointing_dec) = (-3.01069, -0.785398)
        dish_pointing = (math.cos(dish_pointing_dec)*math.cos(dish_pointing_ra), math.cos(dish_pointing_dec)*math.sin(dish_pointing_ra), math.sin(dish_pointing_dec))
        logging.info("Dish pointing in (ra, dec) is {}".format((dish_pointing_ra, dish_pointing_dec)))
        logging.info("Dish pointing as vector is {}".format(dish_pointing))

        (beam_offset_ra, beam_offset_dec) = beam_offset

        phase_centre_j2000 = dm.direction("J2000", "{}rad".format(dish_pointing_ra-beam_offset_ra), "{}rad".format(dish_pointing_dec+beam_offset_dec))
        phase_centre_hadec = dm.measure(phase_centre_j2000, "HADEC")
        dm.do_frame(phase_centre_hadec)

        phase_centre_long = dm.get_value(phase_centre_hadec)[0].get_value("rad")
        phase_centre_lat = dm.get_value(phase_centre_hadec)[1].get_value("rad")
        logging.info("Phase centre is ({}, {})".format(phase_centre_long, phase_centre_lat))

        #h0 = phase_centre_long - observatory_position_long
        #dec = phase_centre_lat
        #logging.info("(h0, dec) = ({},{})".format(h0, dec))

        #sh0 = math.sin(h0)
        #ch0 = math.cos(h0)
        #sd = math.sin(dec)
        #cd = math.cos(dec)

        #transform_matrix = numpy.array([[-sh0, -ch0, 0],
                                        #[sd*ch0, -sd*sh0, -cd],
                                        #[-cd*ch0, cd*sh0, -sd]])

        #baseline = numpy.array(antenna2) - numpy.array(antenna1)
        baseline = numpy.array(antenna1) - numpy.array(antenna2)
        logging.info("Baseline before rotation is ({}, {}, {})".format(baseline[0], baseline[1], baseline[2]))

        unrotated_baseline_itrf = dm.baseline('itrf', "{}m".format(baseline[0]), "{}m".format(baseline[1]), "{}m".format(baseline[2]))

        uvw = dm.to_uvw(unrotated_baseline_itrf)

        #logging.info("Unrotated UVW is {}".format(uvw))
        #logging.info("Unrotated UVW measure is {}".format(uvw['measure']))

        #rotated_baseline = transform_matrix.dot(baseline)
        #logging.info("Baseline after rotation is ({}, {}, {})".format(rotated_baseline[0], rotated_baseline[1], rotated_baseline[2]))

        #rotated_baseline_itrf = dm.baseline('j2000', "{}m".format(rotated_baseline[0]), "{}m".format(rotated_baseline[1]), "{}m".format(rotated_baseline[2]))

        #uvw = dm.to_uvw(rotated_baseline_itrf)

        logging.info("casacore UVW is {}".format(uvw))
        logging.info("Casacore UVW measure is {}".format(uvw['measure']))

        u = dm.get_value(uvw['measure'])[0].get_value()
        v = dm.get_value(uvw['measure'])[1].get_value()
        w = dm.get_value(uvw['measure'])[2].get_value()
        uvw_vec = (u, v, w)
        logging.info("UVW is {}".format(uvw_vec))


if __name__ == '__main__':
    unittest.main()

