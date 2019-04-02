import os
import sys
import time
import logging
import unittest

from dlg.ddap_protocol import AppDROPStates
from dlg.drop import InMemoryDROP, FileDROP
from avg_drop import AveragerSinkDrop, AveragerRelayDrop
from signal_drop import SignalGenerateAndAverageDrop


logging.basicConfig(stream=sys.stdout, level=logging.INFO)


class TestAverager(unittest.TestCase):

    def test_basic_run(self):
        signal = SignalGenerateAndAverageDrop('1', '1',
                                              stream_port=51000,
                                              start_freq=210200000,
                                              freq_step=4000,
                                              num_freq_steps=3,
                                              telescope_model_path='./conf/aa2.tm',
                                              sky_model_file_path="./conf/eor_model_list.csv")

        sink = AveragerSinkDrop('2', '2',
                                stream_listen_port_start=51000,
                                use_adios2=int(os.environ.get('USE_ADIOS2', 0)),
                                baseline_exclusion_map_path='./conf/aa2_baselines.csv',
                                node='127.0.0.1')
        drop = InMemoryDROP('3', '3')
        drop.addStreamingConsumer(sink)
        signal.addOutput(drop)
        sink.addOutput(FileDROP('4', '4', filepath='/tmp/test.ms'))

        signal.async_execute()

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
