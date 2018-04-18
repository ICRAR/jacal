import logging
import Queue
import select
import socket
import struct
import threading
import time

from jacalingest.engine.configuration.configurableservice import ConfigurableService
from jacalingest.engine.statefulservice import StatefulService

class SocketReaderService(StatefulService, ConfigurableService):
    IDLE_STATE = 1
    PROCESSING_STATE = 2

    def __init__(self, **kwargs):
        logging.debug("Initializing")

        super(SocketReaderService, self).__init__(initial_state=self.IDLE_STATE, **kwargs)

        self.output_class = self.get_parameter("output_class")
        assert self.output_class is not None

        self.output_endpoint = self.get_parameter("output_endpoint")
        assert self.output_endpoint is not None

        self.control_endpoint = self.get_parameter("control_endpoint")
        assert self.control_endpoint is not None

        configuration = self.get_configuration(self.get_name())
        host = configuration["host"]
        port = int(configuration["port"])
        logging.info("Binding to {}:{}".format(host, port))

        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((host, port))
        self.server_socket.listen(1)
        
        self.buffer = Queue.Queue()

        self.__stopthread__ = False
        self.socketthread = threading.Thread(target=self.readFromSocket, name="%s socket thread" % self.__class__.__name__)

        self.header_format = "!I"
        self.header_size = struct.calcsize(self.header_format)

    def readFromSocket(self):
        read_list = [self.server_socket]

        header_data = None
        data = None
        data_length = None

        while not self.__stopthread__:
            readable, writable, errored = select.select(read_list, [], [], 5)
            for s in readable:
                if s is self.server_socket:
                    client_socket, address = self.server_socket.accept()
                    client_socket.setblocking(0)
                    read_list.append(client_socket)
                else:
                    if header_data is None:
                        header_data = s.recv(self.header_size)
                    elif len(header_data) < self.header_size:
                        header_data = header_data + s.recv(self.header_size-len(header_data))
                    elif data is None:
                        (data_length,) = struct.unpack(self.header_format, header_data)
                        bytes_to_request = data_length if data_length < 4096 else 4096
                        data = s.recv(bytes_to_request)
                    elif len(data) < data_length:
                        remaining = data_length-len(data)
                        bytes_to_request = remaining if remaining < 4096 else 4096
                        data = data + s.recv(remaining)
                    else:
                        message = self.output_class.deserialize(data)
                        self.buffer.put(message)
                        #logging.info("Received some data! Buffer is now approximately %d long" % self.buffer.qsize())
                        s.shutdown(socket.SHUT_RDWR)
                        s.close()
                        read_list.remove(s)
                        header_data = None
                        data = None

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
                message = self.buffer.get(block=False)
            except Queue.Empty:
                logging.debug("Queue is empty")
                return None
            else:
                #logging.info("Pulled a message from the buffer! Buffer is now approximately %d long" % self.buffer.qsize())
    
                self.messager.publish(self.output_endpoint, message)
                logging.debug("Published a data message.")

                return state

