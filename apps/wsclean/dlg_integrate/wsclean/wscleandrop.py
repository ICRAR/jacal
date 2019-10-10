#
#    ICRAR - International Centre for Radio Astronomy Research
#    (c) UWA - The University of Western Australia, 2015
#    Copyright by UWA (in the framework of the ICRAR)
#    All rights reserved
#
#    This library is free software; you can redistribute it and/or
#    modify it under the terms of the GNU Lesser General Public
#    License as published by the Free Software Foundation; either
#    version 2.1 of the License, or (at your option) any later version.
#
#    This library is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
#    Lesser General Public License for more details.
#
#    You should have received a copy of the GNU Lesser General Public
#    License along with this library; if not, write to the Free Software
#    Foundation, Inc., 59 Temple Place, Suite 330, Boston,
#    MA 02111-1307  USA
#
import logging
import six
import subprocess
import os
import time

from dlg.drop import BarrierAppDROP
from dlg import utils,droputils
logger = logging.getLogger(__name__)

WSCLEAN_PATH = "${WSCLEAN_BUILD_PATH}/wsclean"

def mesage_stdouts(prefix, stdout, stderr, enc='utf8'):
    msg = prefix
    if not stdout and not stderr:
        return msg
    msg += ", output follows:"
    if stdout:
        msg += "\n==STDOUT==\n" + utils.b2s(stdout, enc)
    if stderr:
        msg += "\n==STDERR==\n" + utils.b2s(stderr, enc)
    return msg

class WSClean(BarrierAppDROP):

    def initialize(self, **kwargs):
        super(WSClean, self).initialize(**kwargs)

    def invoke_clean(self, q, vis, outcube):
        pass

    def run(self):
        inp = self.inputs[0]
        out = self.outputs[0]
        
        cmd = droputils.allDropContents(inp)
        # for filedrop
        # lines = []
        # with open(inp.path, 'r') as f :
        #     lines = f.readlines()
        # cmd = "%s %s"%(WSCLEAN_PATH, lines[0])

        cmd = ('/bin/bash', '-c', "%s %s"%(WSCLEAN_PATH, bytes.decode(cmd,encoding='utf-8')))
        logger.info("Command after user creation and wrapping is: %s", cmd)

        start = time.time()

        # Run and wait until it finishes
        process = subprocess.Popen(cmd,
                                   close_fds=True,
                                   stdin=None,
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE,
                                   preexec_fn=os.setsid)

        logger.debug("Process launched, waiting now...")

        pstdout, pstderr = process.communicate()
        pcode = process.returncode

        end = time.time()
        logger.info("Finished in %.3f [s] with exit code %d", (end-start), pcode)

        if pcode == 0 and logger.isEnabledFor(logging.DEBUG):
            logger.debug(mesage_stdouts("Command finished successfully", pstdout, pstderr))
        elif pcode != 0:
            message = "Command didn't finish successfully (exit code %d)" % (pcode,)
            logger.error(mesage_stdouts(message, pstdout, pstderr))
            raise Exception(message)

class Split(BarrierAppDROP):
    def initialize(self, **kwargs):
        super(Split, self).initialize(**kwargs)
        self.wsclean_args = {
                        'niter':  str(self._getArg(kwargs, 'niter', None)),
                        'pol': str(self._getArg(kwargs, 'pol', None)),
                        'data-column': str(self._getArg(kwargs, 'data_column', None)),
                        'weight': str(self._getArg(kwargs, 'weight', None)),
                        'gain': self._getArg(kwargs, 'gain', None),
                        'scale': str(self._getArg(kwargs, 'scale', None)),
                        'size': str(self._getArg(kwargs, 'size', None)),
                        'name': str(self._getArg(kwargs, 'name', None)),
                        'ms': str(self._getArg(kwargs, 'ms', None)),
                        'num_channel': self._getArg(kwargs, 'num_channel', None)}
    def invoke_split(self, q, infile, outdir):
        pass

    def run(self):
        for i in range(len(self.outputs)):
            param_str = ""
            for param in ('niter','pol','data-column','weight','gain','scale','size','name'):
                arg_val = " ".join(self.wsclean_args[param].split("_")) if param in ('weight','size') else self.wsclean_args[param]
                param_str = param_str + "-" + param + " " + arg_val + " "

            if self.wsclean_args['num_channel'] is not None:
                span_chan = int(self.wsclean_args['num_channel']) // len(self.outputs)
                start_chan = str(i*span_chan)
                end_chan = str((i+1)*span_chan)
                param_str = param_str + "-name %s-%s_%s -channel-range %s %s " %(self.wsclean_args['name'],start_chan,end_chan,start_chan,end_chan)

            param_str = param_str + self.wsclean_args['ms']
            self.outputs[i].write(six.b(param_str))
