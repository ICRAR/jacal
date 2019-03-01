import sys
import logging
import unittest
import os

from dlg import droputils
from dlg.drop import FileDROP
from cimager_drop import CImagerDrop
from dlg.droputils import DROPWaiterCtx


logging.basicConfig(stream=sys.stdout, level=logging.INFO)


class TestCImager(unittest.TestCase):

    def test_basic_run(self):
        a = FileDROP('a', 'a')
        b = CImagerDrop('1', '1', config='conf/cimage01.ini')
        c = FileDROP('b', 'b')

        b.addInput(a)
        b.addOutput(c)

        # Random data so we always check different contents
        data = os.urandom(10)
        with DROPWaiterCtx(self, c, 100):
            a.write(data)
            a.setCompleted()

