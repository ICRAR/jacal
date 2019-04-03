import os
import sys
import logging
import unittest

from dlg.drop import FileDROP
from cimager_drop import CImagerDrop
from dlg.droputils import DROPWaiterCtx


logging.basicConfig(stream=sys.stdout, level=logging.INFO)


class TestCImager(unittest.TestCase):

    def test_basic_run(self):
        input_ms = os.environ.get('INPUT_MS', '/tmp/output/aa01.ms')
        a = FileDROP('1', '1', filepath=input_ms)
        b = CImagerDrop('2', '2')
        c = FileDROP('3', '3', filepath='image_aa01')

        b.addInput(a)
        b.addOutput(c)

        with DROPWaiterCtx(self, c, 100):
            a.setCompleted()


