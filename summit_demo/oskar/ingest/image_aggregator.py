from dlg.drop import BarrierAppDROP
from dlg.ddap_protocol import DROPStates

from fits_cube import *


class FitsImageAggregator(BarrierAppDROP):

    def initialize(self, **kwargs):
        self.freq_step = kwargs.get('freq_step', None)

        super(FitsImageAggregator, self).initialize(**kwargs)

    def run(self):
        fits_output = self.outputs[0].path

        channel_order = {}
        for i in self.inputs:
            if i.status != DROPStates.COMPLETED:
                continue
            header = get_header(i.path)
            channel_order[header['CRVAL3']] = i.path

        fits_input = [channel_order[key] for key in sorted(channel_order)]
        concat_images(fits_output, fits_input, self.freq_step)
