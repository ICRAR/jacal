import logging
import Queue

from jacalingest.engine.configuration.configurableservice import ConfigurableService

from jacalingest.engine.handlerservice import HandlerService
from jacalingest.stringdomain.stringmessage import StringMessage

class StringConcatenatorService(HandlerService, ConfigurableService):
    IDLE_STATE = 1
    PROCESSING_STATE = 2

    def __init__(self, **kwargs):
        logging.info("Initializing")

        super(StringConcatenatorService, self).__init__(initial_state=self.IDLE_STATE, **kwargs)

        self.set_handler(self.get_parameter("first_endpoint"), self.handle_first, [self.PROCESSING_STATE])
        self.set_handler(self.get_parameter("second_endpoint"), self.handle_second, [self.PROCESSING_STATE])
        self.set_handler(self.get_parameter("control_endpoint"), self.handle_control, [self.IDLE_STATE, self.PROCESSING_STATE])

        self.concatenation_endpoint = self.get_parameter("concatenation_endpoint")

        self.first_queue = Queue.Queue()
        self.second_queue = Queue.Queue()

    def handle_first(self, message, state):
        logging.debug("Received first {}".format(message))
        self.first_queue.put(message)
        if not self.second_queue.empty():
            first_string = self.first_queue.get_nowait().get_payload()
            second_string = self.second_queue.get_nowait().get_payload()
            concatenation = "{}{}".format(first_string, second_string)
            self.send_concatenation(concatenation)
        return state

    def handle_second(self, message, state):
        logging.debug("Received second {}".format(message))
        self.second_queue.put(message)
        if not self.first_queue.empty():
            first_string = self.first_queue.get_nowait().get_payload()
            second_string = self.second_queue.get_nowait().get_payload()
            concatenation = "{}{}".format(first_string, second_string)
            self.send_concatenation(concatenation)
        return state

    def send_concatenation(self, concatenation):
        logging.debug("Publishing concatenation {}".format(concatenation))
        self.messager.publish(self.concatenation_endpoint, StringMessage(concatenation))

    def handle_control(self, message, state):
        command = message.get_payload()
        if command == "Start":
            logging.info("Received 'Start' control message")
            return self.PROCESSING_STATE
        elif command == "Stop":
            logging.info("Received 'Stop' control message")
            return self.IDLE_STATE
        else:
            logging.info("Received unknown control command: {}".format(command)) 
            return state

