import logging
import numpy
import struct

from jacalingest.engine.messaging.message import Message
from jacalingest.ingest.tosmetadata import TOSMetadata

class VisibilityChunk(Message):
    J2000 = 1
    AZEL = 2

    def __init__(self, number_of_rows, number_of_channels, number_of_polarisations, number_of_antennas, interval, maximum_number_of_beams):
        logging.debug("Initializing...")

        self._number_of_rows = int(number_of_rows)
        self._number_of_channels = int(number_of_channels)
        self._number_of_polarisations = int(number_of_polarisations)
        self._number_of_antennas = int(number_of_antennas)
        self._interval = interval
        self._maximum_number_of_beams = int(maximum_number_of_beams)

        self._time = None
        self._scan_id = None
        self._flagged = None
        self._sky_frequency = None
        self._target_name = None
        self._target_ra = None
        self._target_dec = None
        self._phase_ra = None
        self._phase_dec = None
        self._corr_mode = None

        self._antennas = None

        self._beam1 = list()
        self._beam2 = list()
        self._antenna1 = list()
        self._antenna2 = list()
        for beam in range(maximum_number_of_beams):
            for antenna1 in range(number_of_antennas):
                for antenna2 in range(antenna1, number_of_antennas):
                    self._antenna1.append(antenna1)
                    self._antenna2.append(antenna2)
                    self._beam1.append(beam)
                    self._beam2.append(beam)

        self._visibilities = numpy.zeros(shape=(self._number_of_rows, self._number_of_channels, self._number_of_polarisations), dtype=numpy.complex128)

    def set_visibility(self, row, channel, polarisation_index, value):
        self._visibilities[row][channel][polarisation_index] = value

    def get_number_of_rows(self):
        return self._number_of_rows

    def get_number_of_channels(self):
        return self._number_of_channels

    def get_number_of_polarisations(self):
        return self._number_of_polarisations

    def get_beam1(self, row):
        #logging.info("Requesting beam 1 for row {} from list of length {}, with number of rows being {}.".format(row, len(self._beam1), self._number_of_rows))
        return self._beam1[row]

    def get_beam2(self, row):
        #logging.info("Requesting beam 2 for row {} from list of length {}.".format(row, len(self._beam2)))
        return self._beam2[row]

    def get_antenna1(self, row):
        return self._antenna1[row]

    def get_antenna2(self, row):
        return self._antenna2[row]

    def set_time(self, time):
        self._time = time
    
    def get_time(self):
        return self._time

    def set_scan_id(self, scan_id):
        self._scan_id = scan_id

    def set_flagged(self, flagged):
        self._flagged = flagged

    def set_sky_frequency(self, sky_frequency):
        self._sky_frequency = sky_frequency
        
    def set_target_name(self, target_name):
        self._target_name = target_name

    def set_target_direction(self, ra, dec):
        self._target_ra = ra
        self._target_dec = dec

    def set_phase_direction(self, ra, dec):
        self._phase_ra = ra
        self._phase_dec = dec

    def get_phase_direction(self):
        return (self._phase_ra, self._phase_dec)

    def set_corr_mode(self, corr_mode):
        self._corr_mode = corr_mode

    def set_antennas(self, antennas):
        self._antennas = antennas.copy()

    @staticmethod
    def serialize(chunk):
        serialized = (VisibilityChunk.TupleSerializer("!IIIIfI").serialize((chunk._number_of_rows, chunk._number_of_channels, chunk._number_of_polarisations, chunk._number_of_antennas, chunk._interval, chunk._maximum_number_of_beams))
                     + VisibilityChunk.TupleSerializer("!di?d").serialize((chunk._time, chunk._scan_id, chunk._flagged, chunk._sky_frequency))
                     + VisibilityChunk.StringSerializer().serialize(chunk._target_name)
                     + VisibilityChunk.TupleSerializer("!dddd").serialize((chunk._target_ra, chunk._target_dec, chunk._phase_ra, chunk._phase_dec))
                     + VisibilityChunk.StringSerializer().serialize(chunk._corr_mode)
                     + VisibilityChunk.DictSerializer(VisibilityChunk.StringSerializer(), VisibilityChunk.TupleSerializer("!ddddd??")).serialize(chunk._antennas)
                     + VisibilityChunk.ArraySerializer().serialize(chunk._visibilities))
        return serialized

    @staticmethod
    def deserialize(serialized):
        ((number_of_rows, number_of_channels, number_of_polarisations, number_of_antennas, interval, maximum_number_of_beams), tail) = VisibilityChunk.TupleSerializer("!IIIIfI").deserialize_next(serialized)
        chunk = VisibilityChunk(number_of_rows, number_of_channels, number_of_polarisations, number_of_antennas, interval, maximum_number_of_beams)

        ((time, scan_id, flagged, sky_frequency), tail) = VisibilityChunk.TupleSerializer("!di?d").deserialize_next(tail)
        chunk.set_time(time)
        chunk.set_scan_id(scan_id)
        chunk.set_flagged(flagged)
        chunk.set_sky_frequency(sky_frequency)

        (target_name, tail) = VisibilityChunk.StringSerializer().deserialize_next(tail)
        chunk.set_target_name(target_name)

        ((target_ra, target_dec, phase_ra, phase_dec), tail) = VisibilityChunk.TupleSerializer("!dddd").deserialize_next(tail)
        chunk.set_target_direction(target_ra, target_dec)
        chunk.set_phase_direction(phase_ra, phase_dec)

        (corr_mode, tail) = VisibilityChunk.StringSerializer().deserialize_next(tail)
        chunk.set_corr_mode(corr_mode)

        (antennas, tail) = VisibilityChunk.DictSerializer(VisibilityChunk.StringSerializer(), VisibilityChunk.TupleSerializer("!ddddd??")).deserialize_next(tail)
        chunk.set_antennas(antennas)

        (visibilities, tail) = VisibilityChunk.ArraySerializer().deserialize_next(tail)
        chunk._visibilities = visibilities

        return chunk

    def __str__(self):

        return "VisibilityChunk:\n\tTimestamp: {}\n\tScan ID: {}\n\tFlagged: {}\n\tSky frequency: {}\n\tTarget name: {}\n\tTarget direction: ({}, {})\n\tPhase direction: ({}, {})\n\tCorr mode: {}\n\tAntennas: [{}]\n\tShape of visibilities: {}".format(self._time, self._scan_id, self._flagged, self._sky_frequency, self._target_name, self._target_ra, self._target_dec, self._phase_ra, self._phase_dec, self._corr_mode, str(self._antennas), self._visibilities.shape)


    class TupleSerializer(object):
        def __init__(self, format):
            self._format = format
            self._size = struct.calcsize(self._format)

        def serialize(self, args):
            #logging.info("Format is {}, args are {}".format(self._format, args))
            return struct.pack(self._format, *args)

        def deserialize_next(self, serialized):
            head = struct.unpack(self._format, serialized[:self._size])
            tail = serialized[self._size:]
            return (head, tail)

    class StringSerializer(object):
        def __init__(self):
            pass

        _lenformat = "I"
        _lensize = struct.calcsize(_lenformat)

        def serialize(self, the_string):
            return struct.pack(VisibilityChunk.StringSerializer._lenformat, len(the_string)) + the_string

        def deserialize_next(self, serialized):
            (string_len,) = struct.unpack(VisibilityChunk.StringSerializer._lenformat, serialized[:VisibilityChunk.StringSerializer._lensize])
            head = serialized[VisibilityChunk.StringSerializer._lensize:(VisibilityChunk.StringSerializer._lensize+string_len)]
            tail = serialized[(VisibilityChunk.StringSerializer._lensize+string_len):]
            return (head, tail)

    class ListSerializer(object):
        def __init__(self, contentserializer):
            self._serializer = contentserializer

        _lenformat = "I"
        _lensize = struct.calcsize(_lenformat)


        def serialize(self, the_list):
            serialized = struct.pack(VisibilityChunk.ListSerializer._lenformat, len(the_list))
            for e in the_list:
                serialized = serialized + self._serializer.serialize(e)

            return serialized

        def deserialize_next(self, serialized):
            the_list = list()

            (list_len,) = struct.unpack(VisibilityChunk.ListSerializer._lenformat, serialized[:VisibilityChunk.ListSerializer._lensize])

            tail = serialized[VisibilityChunk.ListSerializer._lensize:]
            for s in range(list_len):
               (head, tail) = self._serializer.deserialize_next(tail)
               the_list.append(head)

            return (the_list, tail)

    class DictSerializer(object):
        def __init__(self, keyserializer, valueserializer):
             self._keyserializer = keyserializer
             self._valueserializer = valueserializer
 
        _lenformat = "I"
        _lensize = struct.calcsize(_lenformat)
 
        def serialize(self, the_dict):
            serialized = struct.pack(VisibilityChunk.DictSerializer._lenformat, len(the_dict))
            for (k,v) in the_dict.iteritems():
                serialized = serialized + self._keyserializer.serialize(k) + self._valueserializer.serialize(v)
            return serialized

        def deserialize_next(self, serialized):
            the_dict = dict()

            (dict_len,) = struct.unpack(VisibilityChunk.DictSerializer._lenformat, serialized[:VisibilityChunk.DictSerializer._lensize])

            tail = serialized[VisibilityChunk.DictSerializer._lensize:]
            for s in range(dict_len):
               (key, tail) = self._keyserializer.deserialize_next(tail)
               (value, tail) = self._valueserializer.deserialize_next(tail)
               the_dict[key] = value

            return (the_dict, tail)

    class ArraySerializer(object):
        def __init__(self):
            self.string_serializer = VisibilityChunk.StringSerializer()

        def serialize(self, the_array):
            dimension = len(the_array.shape)

            serialized_dimension = struct.pack("!I", dimension)
            serialized_shape = struct.pack("!{}I".format(len(the_array.shape)), *the_array.shape)
            serialized_array = self.string_serializer.serialize(the_array.tostring())

            return serialized_dimension + serialized_shape + serialized_array

        def deserialize_next(self, serialized):
            format = "!I"
            size = struct.calcsize(format)
            (dimension,) = struct.unpack(format, serialized[:size])
            serialized = serialized[size:]

            format = "!{}I".format(dimension)
            size = struct.calcsize(format)
            shape = struct.unpack(format, serialized[:size])
            serialized = serialized[size:]

            (the_string, tail) = self.string_serializer.deserialize_next(serialized)
            the_array = numpy.fromstring(the_string)
            the_array.dtype = numpy.complex
            the_array = the_array.reshape(shape)
            return (the_array, tail)

