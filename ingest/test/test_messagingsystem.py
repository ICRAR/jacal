import logging
import time
import unittest

from jacalingest.engine.messaging.messager import Messager
from jacalingest.engine.messaging.asciifilemessagingsystem import AsciiFileMessagingSystem
from jacalingest.engine.messaging.blockingqueuemessagingsystem import BlockingQueueMessagingSystem
from jacalingest.engine.messaging.queuemessagingsystem import QueueMessagingSystem
from jacalingest.stringdomain.stringmessage import StringMessage


class TestMessagingSystem(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        logging.basicConfig(level=logging.INFO, format='%(threadName)s, %(module)s: %(message)s')

    def test(self):
        messager = Messager()

        for messaging_system in [QueueMessagingSystem(),
                                 AsciiFileMessagingSystem(),
                                 BlockingQueueMessagingSystem(100)]:

            logging.info("Testing class {}...".format(messaging_system.__class__.__name__))

            stream_a = messager.get_stream(messaging_system, "topic a", StringMessage)
            stream_b = messager.get_stream(messaging_system, "topic b", StringMessage)

            out_message_a1 = StringMessage("a1")
            out_message_b1 = StringMessage("b1")
            out_message_a2 = StringMessage("a2")
            out_message_b2 = StringMessage("b2")

            out_endpoint_a = stream_a.get_endpoint()
            out_endpoint_b = stream_b.get_endpoint()

            in_endpoint_a = stream_a.get_endpoint()
            in_endpoint_b = stream_b.get_endpoint()

            messager.publish(out_endpoint_a, out_message_a1)
            messager.publish(out_endpoint_b, out_message_b1)
            messager.publish(out_endpoint_a, out_message_a2)
            messager.publish(out_endpoint_b, out_message_b2)

            in_message_a1 = None
            while in_message_a1 is None:
                time.sleep(1)
                in_message_a1 = messager.poll(in_endpoint_a)
            assert in_message_a1.get_payload() == out_message_a1.get_payload()

            in_message_b1 = None
            while in_message_b1 is None:
                time.sleep(1)
                in_message_b1 = messager.poll(in_endpoint_b)
            assert in_message_b1.get_payload() == out_message_b1.get_payload()

            in_message_a2 = None
            while in_message_a2 is None:
                time.sleep(1)
                in_message_a2 = messager.poll(in_endpoint_a)
            assert in_message_a2.get_payload() == out_message_a2.get_payload()

            in_message_b2 = None
            while in_message_b2 is None:
                time.sleep(1)
                in_message_b2 = messager.poll(in_endpoint_b)
            assert in_message_b2.get_payload() == out_message_b2.get_payload()


if __name__ == '__main__':
    unittest.main()

