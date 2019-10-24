import os
import sys
import logging
import unittest

from dlg import droputils
from dlg.drop import FileDROP
import signal_drop


level = logging.INFO
if int(os.environ.get('VERBOSE', '0')):
    level = logging.DEBUG
logging.basicConfig(stream=sys.stdout, level=level, datefmt='%H:%M:%S',
                    format="%(asctime)s %(module)s:%(lineno)d %(message)s")

output = os.environ.get('OUTPUT', os.path.join(os.getcwd(), 'test.ms'))
tm = os.environ.get('TM', 'aa4').lower()
internal_port = 12345
try:
    from mpi4py import MPI
    rank = MPI.COMM_WORLD.Get_rank()
    internal_port += rank * 10
    logging.info('Using internal/stream ports %d', internal_port)
except:
    pass

class TestAdios2Pipeline(unittest.TestCase):

    def test_basic_run(self):
        signal = signal_drop.SignalGenerateAndAverageDrop(
            '1', '1',
            mode=signal_drop.MODE_ADIOS_PIPELINE,
            internal_port=internal_port,
            start_freq=int(os.environ.get('START_FREQ', 45991200)),
            freq_step=int(os.environ.get('FREQ_STEP', 6400)),
            use_gpus=int(os.environ.get('USE_GPUS', 0)),
            num_freq_steps=int(os.environ.get('NUM_CHANNELS', 1)),
            telescope_model_path='./conf/%s.tm' % tm,
            sky_model_file_path="./conf/eor_model_list.csv",
            num_time_steps=int(os.environ.get('NUM_TIME_STEPS', 1)),
            num_repetitions=int(os.environ.get('NUM_REPETITIONS', 100))
        )
        ms = FileDROP('2', '2', filepath=output)
        signal.addOutput(ms)
        with droputils.DROPWaiterCtx(self, ms, 1000):
            signal.async_execute()

if __name__ == '__main__':
    unittest.main()