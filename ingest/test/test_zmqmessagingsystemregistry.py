import logging
import unittest
import socket
import threading
import time
import zmq

from jacalingest.engine.messaging.zmq.zmqmessagingsystemregistry import ZMQMessagingSystemRegistry

class TestZMQMessagingSystemRegistry(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        logging.basicConfig(level=logging.INFO, format='%(threadName)s, %(module)s: %(message)s')

    def test(self):
        hostname = socket.gethostname()
        address = socket.gethostbyname(hostname)
        port = 5555

        registry = ZMQMessagingSystemRegistry(port)
        registry.start()

        context = zmq.Context()
        self.zmq_socket = context.socket(zmq.REQ)
        self.zmq_socket.connect("tcp://{}:{}".format(hostname, port))

        reply = self.subscribe("topic1")
        reply = self.publish("host1", 5555, "topic1")
        reply = self.subscribe("topic1")

        registry.stop()

    def subscribe(self, topic):
        request = b"{}".format(topic)
        self.zmq_socket.send(request)
        reply = self.zmq_socket.recv()
        logging.info("Subscribed to topic {}, received reply '{}'".format(topic, reply))

    def publish(self, host, port, topic):
        request = b"{}:{}:{}".format(host, port, topic)
        self.zmq_socket.send(request)
        reply = self.zmq_socket.recv()
        logging.info("{}:{} has registered as publisher of topic {}, receiving reply '{}'".format(host, port, topic, reply))


if __name__ == '__main__':
    unittest.main()

