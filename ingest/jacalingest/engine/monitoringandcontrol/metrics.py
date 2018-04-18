from collections import defaultdict
import json

from jacalingest.engine.messaging.message import Message

class Metrics(Message):

    def __init__(self, label):
        self.label = label

        self.current_state = None
        self.sent_metrics = defaultdict(int)
        self.polled_metrics = defaultdict(int)
        self.received_metrics = defaultdict(int)

    def state(self, current_state):
        self.current_state = current_state

    def sent(self, topic):
        self.sent_metrics[topic] += 1

    def polled(self, topic):
        self.polled_metrics[topic] += 1

    def received(self, topic):
        self.received_metrics[topic] += 1

    def __str__(self):
        return "Metrics for {} in state {}: ".format(self.label, self.current_state)+"; ".join(["{} unsuccessful polls on {}".format(v, k)for k,v in self.polled_metrics.items()] + ["{} received messages on {}".format(v, k)for k,v in self.received_metrics.items()] + ["{} sent messages on {}".format(v, k)for k,v in self.sent_metrics.items()])


    @staticmethod
    def serialize(metrics):
        return json.dumps((metrics.label, metrics.current_state, metrics.sent_metrics, metrics.polled_metrics, metrics.received_metrics))

    @staticmethod
    def deserialize(serialized):
        (label, current_state, sent_metrics, polled_metrics, received_metrics) = json.loads(serialized)
        metrics = Metrics(label)
        metrics.current_state = current_state
        metrics.sent_metrics = sent_metrics
        metrics.polled_metrics = polled_metrics
        metrics.received_metrics = received_metrics

        return metrics

