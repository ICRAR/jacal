import logging
import struct

from jacalingest.engine.messaging.message import Message

class VisibilityDatagram(Message):
    def __init__(self, timestamp, block, card, channel, freq, beam_id, baseline1, baseline2, visibilities):
        self.timestamp = timestamp
        self.block = block
        self.card = card
        self.channel = channel
        self.freq = freq
        self.beam_id = beam_id
        self.baseline1 = baseline1
        self.baseline2 = baseline2
        self.visibilities = visibilities

    headerformat = "!QIIIdIII"
    headersize = struct.calcsize(headerformat)
    visibilityformat = "ff"
    visibilitysize = struct.calcsize(visibilityformat)

    def get_visibility(self, i):
        return self.visibilities[i]

    @staticmethod
    def serialize(object):
        return struct.pack(VisibilityDatagram.headerformat + VisibilityDatagram.visibilityformat*len(object.visibilities), object.timestamp, object.block, object.card, object.channel, object.freq, object.beam_id, object.baseline1, object.baseline2, *(e for v in object.visibilities for e in (v.real, v.imag)))

    @staticmethod
    def deserialize(serialized):
        number_of_visibilities = (len(serialized) - VisibilityDatagram.headersize) / VisibilityDatagram.visibilitysize

        (timestamp, block, card, channel, freq, beam_id, baseline1, baseline2) = struct.unpack(VisibilityDatagram.headerformat, serialized[:VisibilityDatagram.headersize])

        vit = iter(struct.unpack(VisibilityDatagram.visibilityformat*number_of_visibilities, serialized[VisibilityDatagram.headersize:]))
        visibilities = [complex(a, b) for (a, b) in zip(vit, vit)]

        return VisibilityDatagram(timestamp, block, card, channel, freq, beam_id, baseline1, baseline2, visibilities)

    def __str__(self):
        return "(%s, %d, %d, %d, %f, %d, %d, %d, (%s))" % (self.timestamp, self.block, self.card, self.channel, self.freq, self.beam_id, self.baseline1, self.baseline2, ",".join(str(v) for v in self.visibilities))

