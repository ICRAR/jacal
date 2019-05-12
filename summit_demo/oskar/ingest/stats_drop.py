import logging
import os
import sys
import time

import dlg
from dlg.drop import AppDROP, BarrierAppDROP, FileDROP

logging.basicConfig(stream=sys.stdout, level=logging.INFO)

class SetTimeDrop(BarrierAppDROP):
    def run(self):
        ct = time.time()
        for oup in self.outputs:
            oup.write(str(ct).encode('ascii'))

class CalcDataRateDrop(BarrierAppDROP):

    def _get_short_values(self, source, bufsize=4096):
        desc = source.open()
        return source.read(desc, bufsize)

    def _check_file_size(self, filename):
        """
        Return the size of a file, reported by os.stat().
        Do NOT support diretory yet
        """
        try:
            return os.stat(filename).st_size
        except:
            logging.warn("fail to file stat for %s" % filename)
            return 0

    def run(self):
        stt = None
        edt = time.time()
        total_vol = 0.0
        for inp in self.inputs:
            if (inp.name == 'start_time'):
                stt = float(self._get_short_values(inp).decode('ascii'))
            elif (isinstance(inp, FileDROP)):
                total_vol += self._check_file_size(inp.path)

        if (stt is None):
            raise Exception('Cannot find start time!')
        data_rate = total_vol / (edt - stt)
        self.outputs[0].write(str(data_rate).encode('ascii'))