import logging

from jacalingest.engine.configuration.configurableservice import ConfigurableService
from jacalingest.engine.handlerservice import HandlerService
from jacalingest.stringdomain.stringmessage import StringMessage

class ToStringService(HandlerService, ConfigurableService):
    IDLE_STATE = 1
    PROCESSING_STATE = 2

    def __init__(self, **kwargs):
        logging.debug("Initializing")

        super(ToStringService, self).__init__(initial_state=self.IDLE_STATE, **kwargs)

        self.set_handler(self.get_parameter("input_endpoint"), self.handle_message, [self.PROCESSING_STATE])
        self.set_handler(self.get_parameter("control_endpoint"), self.handle_control, [self.IDLE_STATE, self.PROCESSING_STATE])

        self.out_endpoint = self.get_parameter("output_endpoint")

    def handle_control(self, message, state):
        command = message.get_payload()
        if command == "Start":
            logging.info("Received 'Start' control message")
            return self.PROCESSING_STATE
        elif command == "Stop":
            logging.info("Received 'Stop' control message")
            return self.IDLE_STATE
        else:
            logging.info("Received unknown control message '{}'".format(command))
            return state

    def handle_message(self, message, state):
        self.messager.publish(self.out_endpoint, StringMessage(str(message)))
        logging.info("Published a string message.")
        return state

