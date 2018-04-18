import logging

from jacalingest.engine.configuration.configurableservice import ConfigurableService
from jacalingest.engine.handlerservice import HandlerService

class StringWriterService(HandlerService, ConfigurableService):

    IDLE_STATE = 1
    PROCESSING_STATE = 2

    def __init__(self, **kwargs):
        logging.info("Initializing")

        super(StringWriterService, self).__init__(initial_state=self.IDLE_STATE, **kwargs)

        self.set_handler(self.get_parameter("string_endpoint"), self.handle_string, [self.PROCESSING_STATE])
        self.set_handler(self.get_parameter("control_endpoint"), self.handle_control, [self.IDLE_STATE, self.PROCESSING_STATE])
 
        
        #logging.info("Setting output path to configuration parameter '{}.output_path' or 'output_path'".format(self.get_name()))
        self.output_path = self.get_configuration("{}.output_path".format(self.get_name())) or self.get_configuration("output_path")
        assert self.output_path is not None
        self.output_path = str(self.output_path)
        logging.info("Output will be written to {}".format(self.output_path))

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

    def handle_string(self, message, state):
        payload = message.get_payload()
        logging.debug("Received message '%s'" % payload)
        with open(self.output_path, "a") as f:
            f.write("%s\n" % payload)
        logging.info("Write a message to file.")
        return state
