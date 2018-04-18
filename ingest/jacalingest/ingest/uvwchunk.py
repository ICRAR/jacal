import logging
import numpy
import struct

from jacalingest.engine.messaging.message import Message

class UVWChunk(Message):
    J2000 = 1
    AZEL = 2

    def __init__(self):
        logging.debug("Initializing...")

    @staticmethod
    def create_from_visibility_chunk(visibility_chunk):
        uvw_chunk = UVWChunk()
        uvw_chunk._number_of_rows = visibility_chunk._number_of_rows
        uvw_chunk._number_of_channels = visibility_chunk._number_of_channels
        uvw_chunk._number_of_polarisations = visibility_chunk._number_of_polarisations
        uvw_chunk._number_of_antennas = visibility_chunk._number_of_antennas
        uvw_chunk._interval = visibility_chunk._interval
        uvw_chunk._maximum_number_of_beams = visibility_chunk._maximum_number_of_beams
        uvw_chunk._time = visibility_chunk._time
        uvw_chunk._scan_id = visibility_chunk._scan_id
        uvw_chunk._flagged = visibility_chunk._flagged
        uvw_chunk._sky_frequency = visibility_chunk._sky_frequency
        uvw_chunk._target_name = visibility_chunk._target_name
        uvw_chunk._target_ra = visibility_chunk._target_ra
        uvw_chunk._target_dec = visibility_chunk._target_dec
        uvw_chunk._phase_ra = visibility_chunk._phase_ra
        uvw_chunk._phase_dec = visibility_chunk._phase_dec
        uvw_chunk._corr_mode = visibility_chunk._corr_mode

        uvw_chunk._antennas = visibility_chunk._antennas
        uvw_chunk._beam1 = visibility_chunk._beam1
        uvw_chunk._beam2 = visibility_chunk._beam2
        uvw_chunk._antenna1 = visibility_chunk._antenna1
        uvw_chunk._antenna2 = visibility_chunk._antenna2

        uvw_chunk._visibilities = visibility_chunk._visibilities

        uvw_chunk._uvw = [None] * uvw_chunk._number_of_rows
        return uvw_chunk

    def set_uvw(self, row, u, v, w):
        self._uvw[row] = (u,v,w)

    @staticmethod
    def serialize(chunk):
        serialized = (UVWChunk.TupleSerializer("!IIIIfI").serialize((chunk._number_of_rows, chunk._number_of_channels, chunk._number_of_polarisations, chunk._number_of_antennas, chunk._interval, chunk._maximum_number_of_beams))
                     + UVWChunk.TupleSerializer("!di?d").serialize((chunk._time, chunk._scan_id, chunk._flagged, chunk._sky_frequency))
                     + UVWChunk.StringSerializer().serialize(chunk._target_name)
                     + UVWChunk.TupleSerializer("!dddd").serialize((chunk._target_ra, chunk._target_dec, chunk._phase_ra, chunk._phase_dec))
                     + UVWChunk.StringSerializer().serialize(chunk._corr_mode)
                     + UVWChunk.DictSerializer(UVWChunk.StringSerializer(), UVWChunk.TupleSerializer("!ddddd??")).serialize(chunk._antennas)
                     + UVWChunk.ArraySerializer().serialize(chunk._visibilities)
                     + UVWChunk.ListSerializer(UVWChunk.TupleSerializer("!fff")).serialize(chunk._uvw))
        return serialized

    @staticmethod
    def deserialize(serialized):
        ((number_of_rows, number_of_channels, number_of_polarisations, number_of_antennas, interval, maximum_number_of_beams), tail) = UVWChunk.TupleSerializer("!IIIIfI").deserialize_next(serialized)
        chunk = UVWChunk()
        chunk._number_of_rows = number_of_rows
        chunk._number_of_channels = number_of_channels
        chunk._number_of_polarisations = number_of_polarisations
        chunk._number_of_antennas = number_of_antennas
        chunk._interval = interval
        chunk._maximum_number_of_beams = maximum_number_of_beams

        ((time, scan_id, flagged, sky_frequency), tail) = UVWChunk.TupleSerializer("!di?d").deserialize_next(tail)
        chunk._time = time
        chunk._scan_id = scan_id
        chunk._flagged = flagged
        chunk._sky_frequency = sky_frequency

        (target_name, tail) = UVWChunk.StringSerializer().deserialize_next(tail)
        chunk._target_name = target_name

        ((target_ra, target_dec, phase_ra, phase_dec), tail) = UVWChunk.TupleSerializer("!dddd").deserialize_next(tail)
        chunk._target_ra = target_ra
        chunk._target_dec = target_dec
        chunk._phase_ra = phase_ra
        chunk._phase_dec = phase_dec

        (corr_mode, tail) = UVWChunk.StringSerializer().deserialize_next(tail)
        chunk._corr_mode = corr_mode

        (antennas, tail) = UVWChunk.DictSerializer(UVWChunk.StringSerializer(), UVWChunk.TupleSerializer("!ddddd??")).deserialize_next(tail)
        chunk._antennas = antennas

        (visibilities, tail) = UVWChunk.ArraySerializer().deserialize_next(tail)
        chunk._visibilities = visibilities

        (uvw, tail) = UVWChunk.ListSerializer(UVWChunk.TupleSerializer("!fff")).deserialize_next(tail)
        chunk._uvw = uvw

        return chunk

    def __str__(self):
        return "UVWChunk:\n\tTimestamp: {}\n\tScan ID: {}\n\tFlagged: {}\n\tSky frequency: {}\n\tTarget name: {}\n\tTarget direction: ({}, {})\n\tPhase direction: ({}, {})\n\tCorr mode: {}\n\tAntennas: [{}]\n\tShape of visibilities: {}".format(self._time, self._scan_id, self._flagged, self._sky_frequency, self._target_name, self._target_ra, self._target_dec, self._phase_ra, self._phase_dec, self._corr_mode, str(self._antennas), self._visibilities.shape)


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
            return struct.pack(UVWChunk.StringSerializer._lenformat, len(the_string)) + the_string

        def deserialize_next(self, serialized):
            (string_len,) = struct.unpack(UVWChunk.StringSerializer._lenformat, serialized[:UVWChunk.StringSerializer._lensize])
            head = serialized[UVWChunk.StringSerializer._lensize:(UVWChunk.StringSerializer._lensize+string_len)]
            tail = serialized[(UVWChunk.StringSerializer._lensize+string_len):]
            return (head, tail)

    class ListSerializer(object):
        def __init__(self, contentserializer):
            self._serializer = contentserializer

        _lenformat = "I"
        _lensize = struct.calcsize(_lenformat)


        def serialize(self, the_list):
            serialized = struct.pack(UVWChunk.ListSerializer._lenformat, len(the_list))
            for e in the_list:
                serialized = serialized + self._serializer.serialize(e)

            return serialized

        def deserialize_next(self, serialized):
            the_list = list()

            (list_len,) = struct.unpack(UVWChunk.ListSerializer._lenformat, serialized[:UVWChunk.ListSerializer._lensize])

            tail = serialized[UVWChunk.ListSerializer._lensize:]
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
            serialized = struct.pack(UVWChunk.DictSerializer._lenformat, len(the_dict))
            for (k,v) in the_dict.iteritems():
                serialized = serialized + self._keyserializer.serialize(k) + self._valueserializer.serialize(v)
            return serialized

        def deserialize_next(self, serialized):
            the_dict = dict()

            (dict_len,) = struct.unpack(UVWChunk.DictSerializer._lenformat, serialized[:UVWChunk.DictSerializer._lensize])

            tail = serialized[UVWChunk.DictSerializer._lensize:]
            for s in range(dict_len):
               (key, tail) = self._keyserializer.deserialize_next(tail)
               (value, tail) = self._valueserializer.deserialize_next(tail)
               the_dict[key] = value

            return (the_dict, tail)

    class ArraySerializer(object):
        def __init__(self):
            self.string_serializer = UVWChunk.StringSerializer()

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

