import logging
import socket
import zmq
from jacalingest.engine.messaging.messagingsystem import MessagingSystem

class ZMQMessagingSystem(MessagingSystem):
    def __init__(self, registry_host, registry_port, publish_port):
        logging.debug("initializing")

        self.context = zmq.Context()
        self.registry_socket = self.context.socket(zmq.REQ)
        self.registry_socket.connect("tcp://{}:{}".format(registry_host, registry_port))

        self.host = socket.gethostname()

        if publish_port is not None:
            self.port = publish_port
            self.server_socket = self.context.socket(zmq.PUB)
            self.server_socket.bind("tcp://*:{}".format(self.port))

    def register(self, topic):
        assert self.port is not None

        request=b"{}:{}:{}".format(self.host, self.port, topic)
        self.registry_socket.send(request)
        reply = self.registry_socket.recv()
        logging.debug("Registered {}:{} as publisher of topic{}".format(self.host, self.port, topic))

    def publish(self, topic, serialized_message):
        assert self.port is not None

        escaped_topic = topic.replace(":", "\:") # dodgy
        self.server_socket.send_string("{}:{}".format(escaped_topic, serialized_message))
        logging.debug("Published message %s to topic %s" % (serialized_message, topic))

    def _check_registry(self, topic):
        request = b"{}".format(topic)
        self.registry_socket.send(request)
        reply = self.registry_socket.recv()
        logging.debug("Received reply '{}' from registry".format(reply))
        if reply == "":
            return None
        else:
            subscriber_socket = self.context.socket(zmq.SUB)
            subscriber_socket.connect("tcp://{}".format(reply))

            escaped_topic = topic.replace(":", "\:") # dodgy
            #if isinstance(escaped_topic, bytes):
                #escaped_topic = escaped_topic.decode('ascii')
            subscriber_socket.setsockopt(zmq.SUBSCRIBE, "{}:".format(escaped_topic))
            return subscriber_socket

    """Returns a cursor to be used to poll for messages."""
    def subscribe(self, topic):
        logging.debug("Subscribing to topic '{}'...".format(topic))
        return self._check_registry(topic)

    def poll(self, topic, cursor):
        logging.debug("Polling for message on topic '{}'...".format(topic))
        if cursor==None:
            logging.debug("Cursor is None, checking registry again...")
            cursor=self._check_registry(topic)
        if cursor==None:
            logging.debug("Cursor is still None, therefore no message...")
            return (None, None)

        poller = zmq.Poller()
        poller.register(cursor, zmq.POLLIN)
        if cursor in dict(poller.poll(0)):
            message = cursor.recv()
            prefix = "{}:".format(topic.replace(":", "\:"))
            assert message.startswith(prefix)
            message = message[len(prefix):]
            return (message, cursor)
        else:
            return (None, cursor)

