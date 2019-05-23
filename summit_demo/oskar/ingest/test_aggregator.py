import unittest

from dlg import droputils
from dlg.drop import FileDROP

from image_aggregator import FitsImageAggregator


class TestAggregator(unittest.TestCase):

    def test_basic_run(self):
        agg = FitsImageAggregator('0', '0', freq_step=1000.0)
        file1 = FileDROP('1', '1', filepath='image_eor01.restored.fits', dirname='./output/')
        file2 = FileDROP('2', '2', filepath='image_eor02.restored.fits', dirname='./output/')
        file3 = FileDROP('3', '3', filepath='image_eor03.restored.fits', dirname='./output/')
        file4 = FileDROP('4', '4', filepath='image_eor04.restored.fits', dirname='./output/')
        agg.addInput(file1)
        agg.addInput(file2)
        agg.addInput(file3)
        agg.addInput(file4)

        output = FileDROP('10', '10', filepath='summit.fits', dirname='./output/')
        agg.addOutput(output)

        with droputils.DROPWaiterCtx(self, agg, 1000):
            file1.setCompleted()
            file2.setCompleted()
            file3.setCompleted()
            file4.setCompleted()