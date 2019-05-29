import os
import unittest

from contextlib import suppress
from dlg import droputils
from dlg.drop import FileDROP

from image_aggregator import FitsImageAggregator
from image_replicator import FitsImageReplicator


class TestAggregator(unittest.TestCase):

    def setUp(self):
        with suppress(Exception):
            os.remove('/tmp/output/summit.fits')

        with suppress(Exception):
            os.remove('/tmp/output/summit_replication.fits')

    def test_agg_and_rep(self):
        # aggregate
        agg = FitsImageAggregator('0', '0', freq_step=1000.0)
        file1 = FileDROP('1', '1', filepath='image_eor01.restored.fits', dirname='/tmp/output/')
        file2 = FileDROP('2', '2', filepath='image_eor02.restored.fits', dirname='/tmp/output/')
        file3 = FileDROP('3', '3', filepath='image_eor03.restored.fits', dirname='/tmp/output/')
        file4 = FileDROP('4', '4', filepath='image_eor04.restored.fits', dirname='/tmp/output/')
        agg.addInput(file1)
        agg.addInput(file2)
        agg.addInput(file3)
        agg.addInput(file4)

        output = FileDROP('10', '10', filepath='summit.fits', dirname='/tmp/output/')
        agg.addOutput(output)

        # replicate
        rep = FitsImageReplicator('11', '11', copies=4)
        rep_output = FileDROP('12', '12', filepath='summit_replication.fits', dirname='/tmp/output/')
        rep.addInput(output)
        rep.addOutput(rep_output)

        with droputils.DROPWaiterCtx(self, rep, 1000):
            file1.setCompleted()
            file2.setCompleted()
            file3.setCompleted()
            file4.setCompleted()
