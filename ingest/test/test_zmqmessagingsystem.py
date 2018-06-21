import logging
import unittest
import socket
import threading
import time

from jacalingest.engine.messaging.zmq.zmqmessagingsystem import ZMQMessagingSystem
from jacalingest.engine.messaging.zmq.zmqmessagingsystemregistry import ZMQMessagingSystemRegistry

class TestZMQMessagingSystemRegistry(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        logging.basicConfig(level=logging.INFO, format='%(threadName)s, %(module)s: %(message)s')


    def _run_subscriber(self):
        self._stop_subscriber = False
        messaging_system = ZMQMessagingSystem("localhost", self.registry_port, None)
        cursor = messaging_system.subscribe(self.topic)
        while not self._stop_subscriber:
            (message, cursor) = messaging_system.poll(self.topic, cursor)
            if message is not None:
                logging.info("Received message '{}'".format(message))
            else:
                time.sleep(1)

    def _run_publisher(self):
        messaging_system = ZMQMessagingSystem("localhost", self.registry_port, 5556)
        messaging_system.register(self.topic)

        time.sleep(1)

        logging.info("Publishing message: 'This is test message 1.'")
        messaging_system.publish(self.topic, "This is test message 1.")

        time.sleep(1)

        logging.info("Publishing message: 'This is test message 2.'")
        messaging_system.publish(self.topic, "This is test message 2.")
        logging.info("Publishing message: 'This is test message 3.'")
        messaging_system.publish(self.topic, "This is test message 3.")
        logging.info("Publishing message: 'This is test message 4.'")
        messaging_system.publish(self.topic, "This is test message 4.")
        logging.info("Publishing message: 'This is test message 5.'")
        messaging_system.publish(self.topic, "This is test message 5.")


    def test(self):
        self.registry_port = 5555
        registry = ZMQMessagingSystemRegistry(self.registry_port)
        registry.start()


        time.sleep(1)

        self.topic = "Test"

        self._subscriber_thread_1 = threading.Thread(target=self._run_subscriber)
        self._subscriber_thread_1.start()

        self._subscriber_thread_2 = threading.Thread(target=self._run_subscriber)
        self._subscriber_thread_2.start()

        time.sleep(1)

        self._publisher_publish_port = 5557
        self._publisher_thread = threading.Thread(target=self._run_publisher)
        self._publisher_thread.start()

        time.sleep(4)

        self._stop_subscriber = True

        time.sleep(4)

        registry.stop()


if __name__ == '__main__':
    unittest.main()

