import logging

"""This abstract class defines the interface for a messaging system"""
class MessagingSystem:
    def __init__(self):
        raise NotImplementedError

    """Returns an initial cursor for a topic, so that a service
       may beging consuming messages on that topic."""
    def subscribe(self, topic):
        raise NotImplementedError

    """Publishes a message for a topic"""
    def publish(self, topic, serialized_message):
        raise NotImplementedError

    """Return a tuple consisting of the next message (or None if none exists) for a topic after the cursor,
       along with a cursor for use next time"""
    def poll(self, topic, cursor):
        raise NotImplementedError

