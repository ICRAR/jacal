import binascii
import logging
import os
from jacalingest.engine.messaging.messagingsystem import MessagingSystem

class AsciiFileMessagingSystem(MessagingSystem):
    def __init__(self):
        logging.debug("initializing")

        self.message_providers = dict()

    """Returns a cursor to be used to poll for messages."""
    def subscribe(self, topic):
        if topic not in self.message_providers:
            logging.debug("Spinning up message generator for topic %s" % topic)
            self.message_providers[topic] = AsciiFileMessagingSystem.MessageProvider(topic)
        return 0

    def register(self, topic):
        pass

    def publish(self, topic, serialized_message):
        logging.debug("Publishing message %s to topic %s" % (serialized_message, topic))

        #logging.info("Start of unencoded: %s" % serialized_message[:20])
        encoded_message = binascii.b2a_base64(serialized_message)
        #logging.info("Start of encoded: %s" % encoded_message[:20])
        topicpath = "messagelog_%s.txt" % topic
        with open(topicpath, "a") as f:
            f.write(encoded_message)

    def poll(self, topic, cursor):
        logging.debug("Polling for message on topic %s" % topic)

        encoded_message = self.message_providers[topic].get(cursor)
        if encoded_message is None:
            return (None, cursor)

        #logging.info("Start of encoded: %s" % encoded_message[:20])
        serialized_message = binascii.a2b_base64(encoded_message)
        #logging.info("Start of unencoded: %s" % serialized_message[:20])
        logging.debug("Message is %s" % serialized_message)

        return (serialized_message, cursor+1)
    

    class MessageProvider(object):
        def __init__(self, topic):
            self.topic = topic
            self.topicpath = "messagelog_%s.txt" % topic

            self.timestamp = 0
            self.messages = None

        def _check(self):
            if not os.path.exists(self.topicpath):
                logging.debug("No message has yet been written for topic %s" % self.topic)
                return False
            return self._update()

        def _update(self):
            if os.stat(self.topicpath).st_mtime == self.timestamp:
                logging.debug("No new messages have been written since last update for topic %s." % self.topic)
                return False
            logging.debug("A message has been written since last read of topic %s." % self.topic)
            self.timestamp = os.stat(self.topicpath).st_mtime
            with open(self.topicpath, "r") as f:
                lines = f.readlines()
                if not lines[-1].endswith("\n"): # read of partially written file due to race condition
                    lines.pop() # let's throw away that partial line
                    self.timestamp = 0 # and force a re-read next time we run out of lines to read
                self.messages = [l.strip() for l in lines]
            return True

        def get(self, cursor):
            if self.messages is None and not self._check():
                return None

            try:
                return self.messages[cursor]
            except IndexError:
                if self._update() and len(self.messages) > cursor:
                    return self.messages[cursor]
            return None

