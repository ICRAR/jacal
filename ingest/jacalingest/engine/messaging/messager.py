import logging

from jacalingest.engine.servicecontainer import ServiceContainer

class Messager(ServiceContainer):
    def __init__(self):
        pass

    def get_stream(self, messaging_system, topic, message_class):
        return Messager.Stream(messaging_system, topic, message_class)

    def get_read_endpoint(self, messaging_system, topic, message_class):
        return Messager.ReadEndpoint(messaging_system, topic, message_class)

    def get_write_endpoint(self, messaging_system, topic, message_class):
        return Messager.WriteEndpoint(messaging_system, topic, message_class)

    def publish(self, endpoint, message):
        endpoint._publish(message)

    def poll(self, endpoint):
        return endpoint._poll()

    class Stream(object):
        def __init__(self, messaging_system, topic, messageclass):
            logging.debug("Initializing stream")
    
            self.messaging_system = messaging_system
            self.topic = topic
            self.messageclass = messageclass

        def get_read_endpoint(self):
            return Messager.ReadEndpoint(self.messaging_system, self.topic, self.messageclass)

        def get_write_endpoint(self):
            return Messager.WriteEndpoint(self.messaging_system, self.topic, self.messageclass)

    class ReadEndpoint(object):
        def __init__(self, messaging_system, topic, messageclass):
            logging.debug("Initializing read endpoint")
    
            self.messaging_system = messaging_system
            self.topic = topic
            self.messageclass = messageclass

            self.cursor = self.messaging_system.subscribe(topic)

        def _poll(self):
            (serialized_message, cursor) = self.messaging_system.poll(self.topic, self.cursor)
            self.cursor = cursor

            if serialized_message is None:
                return None
            else:
                return self.messageclass.deserialize(serialized_message)

    class WriteEndpoint(object):
        def __init__(self, messaging_system, topic, messageclass):
            logging.debug("Initializing write endpoint")
    
            self.messaging_system = messaging_system
            self.topic = topic
            self.messageclass = messageclass

        def _publish(self, message_object):
            serialized_message = self.messageclass.serialize(message_object)
            self.messaging_system.publish(self.topic, serialized_message)

