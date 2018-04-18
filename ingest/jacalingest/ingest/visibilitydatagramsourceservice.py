import logging
import Queue
import socket
import struct
import threading
import time

from jacalingest.engine.configuration.configurableservice import ConfigurableService
from jacalingest.engine.statefulservice import StatefulService
from jacalingest.ingest.visibilitydatagram import VisibilityDatagram

# ISSUES: Need to support max_beam_id and max_slice

class VisibilityDatagramSourceService(StatefulService, ConfigurableService):
    IDLE_STATE = 1
    PROCESSING_STATE = 2

    def __init__(self, **kwargs):
        logging.debug("Initializing")

        super(VisibilityDatagramSourceService, self).__init__(initial_state=self.IDLE_STATE, **kwargs)

        self.visibility_datagram_endpoint = self.get_parameter("visibility_datagram_endpoint")
        assert self.visibility_datagram_endpoint is not None

        self.control_endpoint = self.get_parameter("control_endpoint")
        assert self.control_endpoint is not None

        buffersize = self.get_parameter("buffersize") or 1024 * 1024 * 16

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, buffersize)
        self.sock.setblocking(0) # non-blocking

        configuration = self.get_configuration("datagram_source")
        host = configuration["host"]
        port = int(configuration["port"])
        
        logging.info("Binding to {}:{}".format(host, port))
        self.sock.bind((host, port))

        self.buffer = Queue.Queue()

        self.udp_datagrams = dict()

        self.socketthread = threading.Thread(target=self.readFromSocket, name="%s socket thread" % self.__class__.__name__)
        self.__stopthread__ = False

    def readFromSocket(self):
        while not self.__stopthread__:
            try:
                data = self.sock.recv(UDPDatagram.DATAGRAM_SIZE)
            except socket.error as e:
                logging.debug("Socket receive failed with error %s." % str(e))
                time.sleep(0.1)
            else:
                self.buffer.put(data)
                logging.debug("Received some data! Buffer is now approximately %d long" % self.buffer.qsize())

    def stateful_tick(self, state):
        logging.debug("in stateful_tick with state {}".format(state))
        always_state = self.always_tick(state)

        if always_state is not None and always_state != state:
            logging.info("New state is {}".format(always_state))
            state = always_state

        if state == self.PROCESSING_STATE:
            processing_state = self.processing_tick(state)
            if processing_state is None:
                return always_state
            if processing_state != state:
                logging.info("New state is {}".format(processing_state))
            return processing_state

    def always_tick(self, state):
        logging.debug("In always tick")
        message = self.messager.poll(self.control_endpoint)
        while message is not None:
            command = message.get_payload()
            if command == "Start":
                logging.info("Received 'Start' control message")
                self.socketthread.start()
                return self.PROCESSING_STATE
            elif command == "Stop":
                logging.info("Received 'Stop' control message")
                self.__stopthread__ = True
                return self.IDLE_STATE
            else:
                logging.info("Received unknown control message: {}".format(command))
                return state
            message = self.messager.poll(self.control_endpoint)
        return None

    def processing_tick(self, state):
        logging.debug("In processing_tick")
        while True:
            try:
                data = self.buffer.get(block=False)
            except Queue.Empty:
                logging.debug("Queue is empty")
                return None
            else:
                logging.debug("Pulled some data from the buffer! Buffer is now approximately %d long" % self.buffer.qsize())
    
                udp_datagram = UDPDatagram(data)
            
                #if (udp_datagram.timestamp, udp_datagram.channel) not in self.udp_datagrams:
                     #self.udp_datagrams[(udp_datagram.timestamp, udp_datagram.channel)] = [None, None, None, None]
                #self.udp_datagrams[(udp_datagram.timestamp, udp_datagram.channel)][udp_datagram.slice] = udp_datagram
#
                #datagrams = self.udp_datagrams[(udp_datagram.timestamp, udp_datagram.channel)]
                #if not datagrams[0]:
                    #continue
                #if not datagrams[1]:
                    #continue
                #if not datagrams[2]:
                    #continue
                #if not datagrams[3]:
                    #continue

                #flatvisibilities = (datagrams[0].visibilities
                                   #+datagrams[1].visibilities
                                   #+datagrams[2].visibilities
                                   #+datagrams[3].visibilities)
                #vit = iter(flatvisibilities)
                #visibilities = [complex(a, b) for (a, b) in zip(vit, vit)]
                #message = VisibilityDatagram(udp_datagram.timestamp, udp_datagram.block, udp_datagram.card, udp_datagram.channel, udp_datagram.freq, udp_datagram.beam_id, self.udp_datagrams[(udp_datagram.timestamp, udp_datagram.channel, datagrams[0].baseline1, datagrams[3].baseline2, visibilities)

                vit = iter(udp_datagram.visibilities)
                visibilities = [complex(a, b) for (a, b) in zip(vit, vit)]
                message = VisibilityDatagram(udp_datagram.timestamp, udp_datagram.block, udp_datagram.card, udp_datagram.channel, udp_datagram.freq, udp_datagram.beam_id, udp_datagram.baseline1, udp_datagram.baseline2, visibilities)
                self.messager.publish(self.visibility_datagram_endpoint, message)
                logging.debug("Published a data message.")

                #del self.udp_datagrams[(udp_datagram.timestamp, udp_datagram.channel)]
                return state


class UDPDatagram(object):
    _MAX_BASELINES_PER_SLICE = 657

    _HEADER_FORMAT = "<IIQIIIdIII"
    _HEADER_SIZE = struct.calcsize(_HEADER_FORMAT)

    _VISIBILITIES_FORMAT = ">"+("ff"*_MAX_BASELINES_PER_SLICE)
    _VISIBILITIES_SIZE = struct.calcsize(_VISIBILITIES_FORMAT)

    DATAGRAM_SIZE = _HEADER_SIZE + _VISIBILITIES_SIZE

    def __init__(self, data):
        self.data = data

        (self.version, self.slice, self.timestamp, self.block, self.card, self.channel, self.freq, self.beam_id, self.baseline1, self.baseline2) = struct.unpack(UDPDatagram._HEADER_FORMAT, data[:UDPDatagram._HEADER_SIZE])
        self.visibilities = list(struct.unpack(UDPDatagram._VISIBILITIES_FORMAT, data[UDPDatagram._HEADER_SIZE:]))

        logging.debug("slice %d, timestamp %s, block %d, card %d, channel %d, freq %f, beam_id %d, baseline1 %d, baseline2 %d, visibility count %d" % (self.slice, self.timestamp, self.block, self.card, self.channel, self.freq, self.beam_id, self.baseline1, self.baseline2, (self.baseline2-self.baseline1+1)))

