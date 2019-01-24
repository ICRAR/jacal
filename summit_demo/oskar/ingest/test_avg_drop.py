import sys
import time
import logging
import unittest

from dlg.ddap_protocol import AppDROPStates
from dlg.drop import InMemoryDROP
from avg_drop import AveragerSinkDrop, AveragerRelayDrop


logging.basicConfig(stream=sys.stdout, level=logging.INFO)


class TestAverager(unittest.TestCase):

    def test_basic_run(self):
        relay = AveragerRelayDrop('1', '1', config='conf/recv_relay.json')
        sink = AveragerSinkDrop('2', '2', config='conf/recv.json')
        drop = InMemoryDROP('3', '3')
        drop.addStreamingConsumer(sink)
        relay.addOutput(drop)

        relay.async_execute()

        try:
            tries = 10
            for i in range(1, tries):
                if sink.execStatus == AppDROPStates.ERROR:
                    self.fail("AveragerSinkDrop in Error")
                elif sink.execStatus == AppDROPStates.RUNNING:
                    break

                if i == tries-1:
                    self.fail("Timeout")

                time.sleep(1)
        finally:
            sink.close_sink()
