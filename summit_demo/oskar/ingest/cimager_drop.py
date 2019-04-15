import os
import tempfile

import six
from dlg.apps.bash_shell_app import BashShellApp


class CImagerDrop(BashShellApp):

    IMAGER_CMD = 'cimager'

    def initialize(self, **kwargs):
        self.config_file = ''
        self.conf = {}

        self.conf['Cimager.dataset'] = ''
        self.conf['Cimager.imagetype'] = 'fits'
        self.conf['Cimager.Images.Names'] = []
        self.conf['Cimager.Images.shape'] = [512, 512]
        self.conf['Cimager.Images.cellsize'] = ['20arcsec', '20arcsec']
        self.conf['Cimager.Images.direction'] = ['13h24m00.00', '-44.00.00.0', 'J2000']
        self.conf['Cimager.Images.restFrequency'] = 'HI'
        # Options for the alternate imager
        self.conf['Cimager.nchanpercore'] = 1
        self.conf['Cimager.usetmpfs'] = 'false'
        self.conf['Cimager.tmpfs'] = '/dev/shm'
        # barycentre and multiple solver mode not supported in continuum imaging (yet)
        self.conf['Cimager.barycentre'] = 'true'
        self.conf['Cimager.solverpercore'] = 'true'
        self.conf['Cimager.nwriters'] = 1
        self.conf['Cimager.singleoutputfile'] = 'false'
        # This defines the parameters for the gridding.
        self.conf['Cimager.gridder.snapshotimaging'] = 'true'
        self.conf['Cimager.gridder.snapshotimaging.wtolerance'] = 2600
        self.conf['Cimager.gridder.snapshotimaging.longtrack'] = 'true'
        self.conf['Cimager.gridder.snapshotimaging.clipping'] = 0.01
        self.conf['Cimager.gridder'] = 'WProject'
        self.conf['Cimager.gridder.WProject.wmax'] = 2600
        self.conf['Cimager.gridder.WProject.nwplanes'] = 99
        self.conf['Cimager.gridder.WProject.oversample'] = 4
        self.conf['Cimager.gridder.WProject.maxsupport'] = 512
        self.conf['Cimager.gridder.WProject.variablesupport'] = 'true'
        self.conf['Cimager.gridder.WProject.offsetsupport'] = 'true'
        # These parameters define the clean algorithm
        self.conf['Cimager.solver'] = 'Clean'
        self.conf['Cimager.solver.Clean.algorithm'] = 'Basisfunction'
        self.conf['Cimager.solver.Clean.niter'] = 5000
        self.conf['Cimager.solver.Clean.gain'] = 0.1
        self.conf['Cimager.solver.Clean.scales'] = [0, 10, 30]
        self.conf['Cimager.solver.Clean.verbose'] = 'false'
        self.conf['Cimager.solver.Clean.tolerance'] = 0.01
        self.conf['Cimager.solver.Clean.weightcutoff'] = 'zero'
        self.conf['Cimager.solver.Clean.weightcutoff.clean'] = 'false'
        self.conf['Cimager.solver.Clean.psfwidth'] = 512
        self.conf['Cimager.solver.Clean.logevery'] = 50
        self.conf['Cimager.threshold.minorcycle'] = ['50%', '30mJy']
        self.conf['Cimager.threshold.majorcycle'] = '18mJy'
        self.conf['Cimager.ncycles'] = 5
        self.conf['Cimager.Images.writeAtMajorCycle'] = 'false'
        self.conf['Cimager.preconditioner.Names'] = ['Wiener', 'GaussianTaper']
        self.conf['Cimager.preconditioner.GaussianTaper'] = ['60arcsec', '60arcsec', '0deg']
        self.conf['Cimager.preconditioner.preservecf'] = 'true'
        self.conf['Cimager.preconditioner.Wiener.robustness'] = 0.5
        # These parameter govern the restoring of the image and the recording of the beam
        self.conf['Cimager.restore'] = 'true'
        self.conf['Cimager.restore.beam'] = 'fit'
        self.conf['Cimager.restore.beam.cutoff'] = 0.5
        self.conf['Cimager.restore.beamReference'] = 'mid'

        kwargs['command'] = 'dummy'

        super(BashShellApp, self).initialize(**kwargs)

    def run(self):
        output = os.path.basename(self.outputs[0].path)
        basedir = os.path.dirname(self.outputs[0].path)
        if six.PY2 and isinstance(output, unicode):
            output = output.encode()
        self.conf['Cimager.dataset'] = self.inputs[0].path
        self.conf['Cimager.Images.Names'].append(output)

        self.conf_file = tempfile.mktemp(dir=basedir, prefix=output, suffix='.ini')
        self._write_conf(self.conf_file)

        self._command = '{0} -c {1}'.format(self.IMAGER_CMD, self.conf_file)

        self._run_bash(self._inputs, self._outputs)

    def _write_conf(self, filename):
        with open(filename, 'w') as the_file:
            for i, j in self.conf.items():
                val = str(j).replace("'", "")
                the_file.write('%s=%s\n' % (i, val))