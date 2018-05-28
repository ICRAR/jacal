import logging
import socket
import re
import threading
import time
import zmq
from collections import defaultdict

class ZMQMessagingSystemRegistry:

    def __init__(self, port):
        hostname = socket.gethostname()
        address = socket.gethostbyname(hostname)

        logging.info("Initialising registry on {}:{} ({}:{})...".format(hostname, port, address, port))

        context = zmq.Context()
        self.socket = context.socket(zmq.REP)
        self.port = port

        self.publishers = dict() # only one producer per topic, sorry

        self._thread = threading.Thread(target=self.run)

    def start(self):
        logging.info("Starting registry...")
        self._thread.start()

    def stop(self):
        logging.info("Stopping registry...")
        self._stop_thread = True

    def run(self):
        logging.info("Registry is running.")
        self._stop_thread = False
        self.socket.bind("tcp://*:{}".format(self.port))
        poller = zmq.Poller()
        poller.register(self.socket, zmq.POLLIN)

        while not self._stop_thread:
	    if self.socket in dict(poller.poll(1000)):
                message = self.socket.recv()
                parts = re.split(r'(?<!\\):', message) # split on :, with escaping support
                if len(parts) == 3: # This is a publisher
                    self.publishers[parts[2]] = "{}:{}".format(parts[0], parts[1])
                    reply = ""
                elif len(parts) == 1: # This is a subscriber
                    if message in self.publishers:
                        reply = self.publishers[message]
                    else:
                        reply = ""
                self.socket.send(reply)
        logging.info("Registry is stopped.")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(module)s: %(message)s")

    registry = ZMQMessagingSystemRegistry(5555)
    registry.start()
    time.sleep(20)
    registry.stop()


