import logging
import Queue
import socket
import struct

from jacalingest.engine.configuration.configurableservice import ConfigurableService
from jacalingest.engine.handlerservice import HandlerService

class SocketWriterService(HandlerService, ConfigurableService):

    IDLE_STATE = 1
    PROCESSING_STATE = 2

    def __init__(self, **kwargs):
        logging.info("Initializing")

        super(SocketWriterService, self).__init__(initial_state=self.IDLE_STATE, **kwargs)

        self.input_class = self.get_parameter("input_class")
        assert self.input_class is not None

        configuration = self.get_configuration(self.get_name())
        self.host = configuration["host"]
        assert self.host is not None
        self.port = configuration["port"]
        assert self.port is not None
        self.port = int(self.port)

        logging.info("Output will be written to socket at ({}, {})".format(self.host, self.port))

        self.set_handler(self.get_parameter("input_endpoint"), self.handle_input, [self.PROCESSING_STATE])
        self.set_handler(self.get_parameter("control_endpoint"), self.handle_control, [self.IDLE_STATE, self.PROCESSING_STATE])
        
    def handle_control(self, message, state):
        command = message.get_payload()
        if command == "Start":
            logging.info("Received 'Start' control message.")
            return self.PROCESSING_STATE
        elif command == "Stop":
            logging.info("Received 'Stop' control message.")
            return self.IDLE_STATE
        else:
            logging.info("Received unknown control message '{}'".format(command))
            return state

    def handle_input(self, message, state):
        serialized = self.input_class.serialize(message)
        header = struct.pack("!I", len(serialized))

        #logging.info("Pushing message of class {}, serialized to length {}, to socket at ({}, {}).".format(self.input_class, len(serialized), self.host, self.port))
        the_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        the_socket.connect((self.host, self.port))
        the_socket.send(header+serialized)
        the_socket.shutdown(socket.SHUT_RDWR)
        the_socket.close()

