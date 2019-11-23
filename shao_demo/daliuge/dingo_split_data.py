#
#    ICRAR - International Centre for Radio Astronomy Research
#    (c) UWA - The University of Western Australia, 2019
#    Copyright by UWA (in the framework of the ICRAR)
#
#    (c) Copyright 2018 CSIRO
#    Australia Telescope National Facility (ATNF)
#    Commonwealth Scientific and Industrial Research Organisation (CSIRO)
#    PO Box 76, Epping NSW 1710, Australia
#    atnf-enquiries@csiro.au
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
from os.path import join
from time import sleep

from dlg.drop import BarrierAppDROP
from dlg.io import ErrorIO, OpenMode

LOGGER = logging.getLogger(__name__)

# The split files
FILES = {
    1: ["file_1294.9_1319.0.ms", 7746, 9046],
    2: ["file_1319.0_1343.1.ms", 9047, 10347],
    3: ["file_1343.1_1367.2.ms", 10348, 11648],
    4: ["file_1367.2_1391.3.ms", 11649, 12949],
    5: ["file_1391.3_1415.4.ms", 12950, 14250],
    6: ["file_1415.4_1439.5.ms", 14251, 15551],
}


class DingoFrequencySplit(BarrierAppDROP):
    def initialize(self, **kwargs):
        super(DingoFrequencySplit, self).initialize(**kwargs)
        LOGGER.info(f"initialize DingoFrequencySplit: {kwargs}")
        self._mkn = self._getArg(kwargs, "mkn", None)
        self._file_path = self._getArg(kwargs, "file_path", "/tmp/123456")

    def getIO(self):
        """
        This type of DROP cannot be accessed directly
        :return:
        """
        return ErrorIO()

    def dataURL(self):
        return "DingoFrequencySplit"

    def run(self):
        LOGGER.info(f"running DingoFrequencySplit: {self.__dict__}")
        outputs = self.outputs
        for index, (key, value) in enumerate(FILES.items()):
            if self._mkn is not None and index >= self._mkn[1]:
                break

            output_drop = outputs[index]
            drop_io = output_drop.getIO()
            drop_io.open(OpenMode.OPEN_WRITE)
            drop_io.write(
                bytes(
                    f"""
Cimager.dataset                                 = {join(self._file_path, value[0])}
Cimager.imagetype                               = fits
# Apply a maximum UV cutoff
Cimager.MaxUV                                   = 6000
#
Cimager.Images.Names                            = [image.{value[0]}.beam00]
Cimager.Images.shape                            = [1024, 1024]
Cimager.Images.cellsize                         = [2arcsec, 2arcsec]
Cimager.Images.direction                        = [11h50m60.000, -00.26.59.96, J2000]
Cimager.Images.restFrequency                    = HI
# Options for the alternate imager
Cimager.nchanpercore                            = 20
Cimager.usetmpfs                                = false
Cimager.tmpfs                                   = /tmp
# barycentre and multiple solver mode not supported in continuum imaging (yet)
Cimager.barycentre                              = true
Cimager.solverpercore                           = true
Cimager.nwriters                                = 12
Cimager.singleoutputfile                        = true
#
# This defines the parameters for the gridding.
Cimager.gridder.snapshotimaging                 = false
Cimager.gridder.snapshotimaging.wtolerance      = 2600
Cimager.gridder.snapshotimaging.longtrack       = true
Cimager.gridder.snapshotimaging.clipping        = 0.01
Cimager.gridder                                 = WProject
Cimager.gridder.WProject.wmax                   = 30000
Cimager.gridder.WProject.nwplanes               = 257
Cimager.gridder.WProject.oversample             = 4
Cimager.gridder.WProject.maxsupport             = 1024
Cimager.gridder.WProject.variablesupport        = true
Cimager.gridder.WProject.offsetsupport          = true
#
# These parameters define the clean algorithm
Cimager.solver                                  = Clean
Cimager.solver.Clean.algorithm                  = BasisfunctionMFS
Cimager.solver.Clean.niter                      = 1000
Cimager.solver.Clean.gain                       = 0.2
Cimager.solver.Clean.scales                     = [0]
Cimager.solver.Clean.solutiontype               = MAXBASE
Cimager.solver.Clean.verbose                    = False
Cimager.solver.Clean.tolerance                  = 0.01
Cimager.solver.Clean.weightcutoff               = zero
Cimager.solver.Clean.weightcutoff.clean         = false
Cimager.solver.Clean.psfwidth                   = 768
Cimager.solver.Clean.logevery                   = 50
Cimager.threshold.minorcycle                    = [45%,1.0mJy,0.5mJy]
Cimager.threshold.majorcycle                    = [0.5mJy]
Cimager.ncycles                                 = 3
Cimager.Images.writeAtMajorCycle                = false

#
Cimager.preconditioner.Names                    = [Wiener,GaussianTaper]
Cimager.preconditioner.GaussianTaper            = [30arcsec, 30arcsec, 0deg]
Cimager.preconditioner.preservecf               = true
Cimager.preconditioner.Wiener.robustness        = 0.5
#
# These parameter govern the restoring of the image and the recording of the beam
Cimager.restore                                 = true
Cimager.restore.beam                            = fit
Cimager.restore.beam.cutoff                     = 0.5
Cimager.restore.beamReference                   = mid
""",
                    encoding="utf-8",
                )
            )
            drop_io.close()


class DoNothing(BarrierAppDROP):
    def initialize(self, **kwargs):
        super(DoNothing, self).initialize(**kwargs)
        LOGGER.info(f"initialize DoNothing: {kwargs}")

    def getIO(self):
        return ErrorIO()

    def dataURL(self):
        return "DoNothing"

    def run(self):
        LOGGER.info(f"Do nothing: {self.__dict__}")
        sleep(1)
