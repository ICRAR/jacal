import logging

from jacalingest.engine.configuration.configurableservice import ConfigurableService
from jacalingest.stringdomain.stringmessage import StringMessage

class NumberGeneratorService(ConfigurableService):

    def __init__(self, **kwargs):
        logging.info("initializing")

        super(NumberGeneratorService, self).__init__(**kwargs)

        self.endpoint = self.get_parameter('endpoint')
        self.numbers = self.generate_numbers()

    def generate_numbers(self):
        i=0
        while True:
            i+=1
            yield i

    def start(self):
        logging.info("Starting")

    def tick(self):
        number = self.numbers.next()

        logging.debug("Publishing message %s" % str(number))
        self.messager.publish(self.endpoint, StringMessage(str(number)))
        return 1

    def terminate(self):
        logging.info("Terminating")

