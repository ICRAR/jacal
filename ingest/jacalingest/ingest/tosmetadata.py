import logging
import struct

from jacalingest.engine.messaging.message import Message

class TOSMetadata(Message):
    J2000 = 1
    AZEL = 2

    def __init__(self, timestamp, scanid, flagged, sky_frequency, target_name, target_ra, target_dec, phase_ra, phase_dec, corrmode, antennas):
        self.timestamp = timestamp
        self.scanid = scanid
        self.flagged = flagged
        self.sky_frequency = sky_frequency
        self.target_name = target_name
        self.target_ra = target_ra
        self.target_dec = target_dec
        self.phase_ra = phase_ra
        self.phase_dec = phase_dec
        self.corrmode = corrmode
        self.antennas = antennas

    @staticmethod
    def serialize(deserialized):
        #logging.info("Need to serialize this:")
        #logging.info(deserialized)
        serialized = (TOSMetadata.TupleSerializer("!Qi?d").serialize((deserialized.timestamp, deserialized.scanid, deserialized.flagged, deserialized.sky_frequency))
                     + TOSMetadata.StringSerializer().serialize(deserialized.target_name)
                     + TOSMetadata.TupleSerializer("!dddd").serialize((deserialized.target_ra, deserialized.target_dec, deserialized.phase_ra, deserialized.phase_dec))
                     + TOSMetadata.StringSerializer().serialize(deserialized.corrmode)
                     + TOSMetadata.DictSerializer(TOSMetadata.StringSerializer(), TOSMetadata.TupleSerializer("!ddddd??")).serialize(deserialized.antennas))
        #logging.info("Serializing into this TOSMetadata:")
        #logging.info(serialized)
        return serialized

    @staticmethod
    def deserialize(serialized):
        #logging.info("Deserializing this:")
        #logging.info(serialized)
        ((timestamp, scanid, flagged, sky_frequency), tail) = TOSMetadata.TupleSerializer("!Qi?d").deserialize_next(serialized)
        (target_name, tail) = TOSMetadata.StringSerializer().deserialize_next(tail)
        ((target_ra, target_dec, phase_ra, phase_dec), tail) = TOSMetadata.TupleSerializer("!dddd").deserialize_next(tail)
        (corrmode, tail) = TOSMetadata.StringSerializer().deserialize_next(tail)
        (antennas, tail) = TOSMetadata.DictSerializer(TOSMetadata.StringSerializer(), TOSMetadata.TupleSerializer("!ddddd??")).deserialize_next(tail)

        return TOSMetadata(timestamp, scanid, flagged, sky_frequency, target_name, target_ra, target_dec, phase_ra, phase_dec, corrmode, antennas)

    def __str__(self):
        return "{}, {}, {}, {}, {}, ({},{}), ({},{}), {}, [{}])".format(self.timestamp, self.scanid, self.flagged, self.sky_frequency, self.target_name, self.target_ra, self.target_dec, self.phase_ra, self.phase_dec, self.corrmode, str(self.antennas))


    class TupleSerializer(object):
        def __init__(self, format):
            self._format = format
            self._size = struct.calcsize(self._format)

        def serialize(self, args):
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
            return struct.pack(TOSMetadata.StringSerializer._lenformat, len(the_string)) + the_string

        def deserialize_next(self, serialized):
            (string_len,) = struct.unpack(TOSMetadata.StringSerializer._lenformat, serialized[:TOSMetadata.StringSerializer._lensize])
            head = serialized[TOSMetadata.StringSerializer._lensize:(TOSMetadata.StringSerializer._lensize+string_len)]
            tail = serialized[(TOSMetadata.StringSerializer._lensize+string_len):]
            return (head, tail)

    class ListSerializer(object):
        def __init__(self, contentserializer):
            self._serializer = contentserializer

        _lenformat = "I"
        _lensize = struct.calcsize(_lenformat)


        def serialize(self, the_list):
            serialized = struct.pack(TOSMetadata.ListSerializer._lenformat, len(the_list))
            for e in the_list:
                serialized = serialized + self._serializer.serialize(e)

            return serialized

        def deserialize_next(self, serialized):
            the_list = list()

            (list_len,) = struct.unpack(TOSMetadata.ListSerializer._lenformat, serialized[:TOSMetadata.ListSerializer._lensize])

            tail = serialized[TOSMetadata.ListSerializer._lensize:]
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
            serialized = struct.pack(TOSMetadata.DictSerializer._lenformat, len(the_dict))
            for (k,v) in the_dict.iteritems():
                serialized = serialized + self._keyserializer.serialize(k) + self._valueserializer.serialize(v)
            return serialized

        def deserialize_next(self, serialized):
            the_dict = dict()

            (dict_len,) = struct.unpack(TOSMetadata.DictSerializer._lenformat, serialized[:TOSMetadata.DictSerializer._lensize])

            tail = serialized[TOSMetadata.DictSerializer._lensize:]
            for s in range(dict_len):
               (key, tail) = self._keyserializer.deserialize_next(tail)
               (value, tail) = self._valueserializer.deserialize_next(tail)
               the_dict[key] = value

            return (the_dict, tail)

