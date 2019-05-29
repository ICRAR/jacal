from dlg.drop import BarrierAppDROP

from fits_cube import *


class FitsImageReplicator(BarrierAppDROP):

    def initialize(self, **kwargs):
        self.copies = kwargs.get('copies', 1)
        super(FitsImageReplicator, self).initialize(**kwargs)

    def run(self):
        fits_output = self.outputs[0].path
        fits_input = [self.inputs[0].path]*self.copies
        concat_images(fits_output, fits_input)
