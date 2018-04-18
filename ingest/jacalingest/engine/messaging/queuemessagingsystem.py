from collections import defaultdict
import logging
from threading import Lock
import Queue

from jacalingest.engine.messaging.messagingsystem import MessagingSystem

class QueueMessagingSystem(MessagingSystem):
    def __init__(self):
        logging.debug("initializing")

        self.message_queues = dict()
        self.locks = defaultdict(Lock)

    """Returns a cursor to be used to poll for messages."""
    def subscribe(self, topic):
        with self.locks[topic]:
            if topic not in self.message_queues:
                self.message_queues[topic] = list()

            self.message_queues[topic].append(Queue.Queue())
            return len(self.message_queues[topic])-1

    """Returns a tuple containing the next message after the cursor for a topic,
       together with an updated cursor."""
    def poll(self, topic, cursor):
        logging.debug("Polling for message on topic %s" % topic)

        try:
            message = self.message_queues[topic][cursor].get(block=False)
            return (message, cursor)
        except Queue.Empty:
            return (None, cursor)
    
    """Publishes a message on a given topic."""
    def publish(self, topic, message):
        logging.debug("Publishing message %s to topic %s" % (message, topic))

        if topic in self.message_queues:
            for queue in self.message_queues[topic]:
                queue.put(message)
