import logging
import threading
import time

from jacalingest.engine.servicecontainer import ServiceContainer

class ServiceRunner(ServiceContainer):

    def __init__(self, service, messager, naptime=5):
        logging.debug("Initializing")

        self._name = self.__class__.__name__
        self.service = service
        service.set_messager(self)

        self.messager = messager
        self.naptime = naptime

        self.running = False
        self.__thread = threading.Thread(target=self.__run, name="%s main thread" % self._name)

    def start(self):
        logging.info("Starting service...")

        self.service.start()

        if not self.running:
            self.running = True
            self.__thread.start()
        else:
            logging.info("Told to start but was already running.")

    # tell the service to terminate and die
    def terminate(self):
        logging.info("Terminating service...")
        self.service.terminate()

        if self.running:
            self.running = False
        else:
            logging.info("Told to stop but wasn't running.")

    # wait for the service to terminate and die
    def wait(self):
        logging.info("Waiting for thread to die...")
        self.__thread.join()
        logging.info("... wait over")

    def __run(self):
        self.started()

        while self.running:
            returncode = self.service.tick()
            if returncode is None:
                logging.debug("Nothing done; sleeping...")
                time.sleep(self.naptime)
            elif returncode == 0:
                self.running = False

        self.terminated()

    # called when the service has started
    def started(self):
        logging.debug("Started")

    # called when the service has stopped
    def terminated(self):
        logging.debug("Terminated")


    # AbstractContainer contract
    def publish(self, endpoint, message):
        self.messager.publish(endpoint, message)

    def poll(self, endpoint):
        return self.messager.poll(endpoint)

