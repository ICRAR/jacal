import os
import sys
import time
import logging
import unittest

from dlg import droputils
from dlg.ddap_protocol import AppDROPStates
from dlg.drop import InMemoryDROP, FileDROP
from avg_drop import AveragerSinkDrop, AveragerRelayDrop
from signal_drop import SignalGenerateAndAverageDrop


logging.basicConfig(stream=sys.stdout, level=logging.INFO)

output = os.environ.get('OUTPUT', '/tmp/test.ms')
internal_port = 41000
stream_port = 51000
try:
    from mpi4py import MPI
    rank = MPI.COMM_WORLD.Get_rank()
    output = os.environ.get('OUTPUT', '/tmp/test_%d.ms') % rank
    internal_port += rank * 10
    stream_port += rank * 10
    logging.info('Using internal/stream ports %d/%d', internal_port, stream_port)
except:
    pass

class TestAverager(unittest.TestCase):

    def test_basic_run(self):
        signal = SignalGenerateAndAverageDrop('1', '1',
                                              internal_port=internal_port,
                                              stream_port=stream_port,
                                              start_freq=210200000,
                                              freq_step=4000,
                                              use_gpus=int(os.environ.get('USE_GPUS', 0)),
                                              num_freq_steps=3,
                                              telescope_model_path='./conf/aa2.tm',
                                              sky_model_file_path="./conf/eor_model_list.csv")

        sink = AveragerSinkDrop('2', '2',
                                stream_listen_port_start=stream_port,
                                use_adios2=int(os.environ.get('USE_ADIOS2', 0)),
                                baseline_exclusion_map_path='./conf/aa2_baselines.csv',
                                node='127.0.0.1')
        drop = InMemoryDROP('3', '3')
        drop.addStreamingConsumer(sink)
        signal.addOutput(drop)
        ms = FileDROP('4', '4', filepath=output)
        sink.addOutput(ms)

        with droputils.DROPWaiterCtx(self, ms, 1000):
            signal.async_execute()
