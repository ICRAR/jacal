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
    # 1: ["file_1294.9_1319.0.ms", 7746, 9046],
    # 2: ["file_1319.0_1343.1.ms", 9047, 10347],
    # 3: ["file_1343.1_1367.2.ms", 10348, 11648],
    # 4: ["file_1367.2_1391.3.ms", 11649, 12949],
    # 5: ["file_1391.3_1415.4.ms", 12950, 14250],
    # 6: ["file_1415.4_1439.5.ms", 14251, 15551],
    1: ["file_1294.9_1295.9.ms", 7746, 7799],
    2: ["file_1295.9_1296.9.ms", 7800, 7853],
    3: ["file_1296.9_1297.9.ms", 7854, 7907],
    4: ["file_1297.9_1298.9.ms", 7908, 7961],
    5: ["file_1298.9_1299.9.ms", 7962, 8015],
    6: ["file_1299.9_1300.9.ms", 8016, 8069],
    7: ["file_1300.9_1301.9.ms", 8070, 8123],
    8: ["file_1301.9_1302.9.ms", 8124, 8177],
    9: ["file_1302.9_1303.9.ms", 8178, 8231],
    10: ["file_1303.9_1304.9.ms", 8232, 8285],
    11: ["file_1304.9_1305.9.ms", 8286, 8339],
    12: ["file_1305.9_1306.9.ms", 8340, 8393],
    13: ["file_1306.9_1307.9.ms", 8394, 8447],
    14: ["file_1307.9_1308.9.ms", 8448, 8501],
    15: ["file_1308.9_1309.9.ms", 8502, 8555],
    16: ["file_1309.9_1310.9.ms", 8556, 8609],
    17: ["file_1310.9_1311.9.ms", 8610, 8663],
    18: ["file_1311.9_1312.9.ms", 8664, 8717],
    19: ["file_1312.9_1313.9.ms", 8718, 8771],
    20: ["file_1313.9_1314.9.ms", 8772, 8825],
    21: ["file_1314.9_1315.9.ms", 8826, 8879],
    22: ["file_1315.9_1316.9.ms", 8880, 8933],
    23: ["file_1316.9_1317.9.ms", 8934, 8987],
    24: ["file_1317.9_1318.9.ms", 8988, 9041],
    25: ["file_1318.9_1319.9.ms", 9042, 9095],
    26: ["file_1319.9_1320.9.ms", 9096, 9149],
    27: ["file_1320.9_1321.9.ms", 9150, 9203],
    28: ["file_1321.9_1322.9.ms", 9204, 9257],
    29: ["file_1322.9_1323.9.ms", 9258, 9311],
    30: ["file_1323.9_1324.9.ms", 9312, 9365],
    31: ["file_1324.9_1325.9.ms", 9366, 9419],
    32: ["file_1325.9_1326.9.ms", 9420, 9473],
    33: ["file_1326.9_1327.9.ms", 9474, 9527],
    34: ["file_1327.9_1328.9.ms", 9528, 9581],
    35: ["file_1328.9_1329.9.ms", 9582, 9635],
    36: ["file_1329.9_1330.9.ms", 9636, 9689],
    37: ["file_1330.9_1331.9.ms", 9690, 9743],
    38: ["file_1331.9_1332.9.ms", 9744, 9797],
    39: ["file_1332.9_1333.9.ms", 9798, 9851],
    40: ["file_1333.9_1334.9.ms", 9852, 9905],
    41: ["file_1334.9_1335.9.ms", 9906, 9959],
    42: ["file_1335.9_1336.9.ms", 9960, 10013],
    43: ["file_1336.9_1337.9.ms", 10014, 10067],
    44: ["file_1337.9_1338.9.ms", 10068, 10121],
    45: ["file_1338.9_1339.9.ms", 10122, 10175],
    46: ["file_1339.9_1340.9.ms", 10176, 10229],
    47: ["file_1340.9_1341.9.ms", 10230, 10283],
    48: ["file_1341.9_1342.9.ms", 10284, 10337],
    49: ["file_1342.9_1343.9.ms", 10338, 10391],
    50: ["file_1343.9_1344.9.ms", 10392, 10445],
    51: ["file_1344.9_1345.9.ms", 10446, 10499],
    52: ["file_1345.9_1346.9.ms", 10500, 10553],
    53: ["file_1346.9_1347.9.ms", 10554, 10607],
    54: ["file_1347.9_1348.9.ms", 10608, 10661],
    55: ["file_1348.9_1349.9.ms", 10662, 10715],
    56: ["file_1349.9_1350.9.ms", 10716, 10769],
    57: ["file_1350.9_1351.9.ms", 10770, 10823],
    58: ["file_1351.9_1352.9.ms", 10824, 10877],
    59: ["file_1352.9_1353.9.ms", 10878, 10931],
    60: ["file_1353.9_1354.9.ms", 10932, 10985],
    61: ["file_1354.9_1355.9.ms", 10986, 11039],
    62: ["file_1355.9_1356.9.ms", 11040, 11093],
    63: ["file_1356.9_1357.9.ms", 11094, 11147],
    64: ["file_1357.9_1358.9.ms", 11148, 11201],
    65: ["file_1358.9_1359.9.ms", 11202, 11255],
    66: ["file_1359.9_1360.9.ms", 11256, 11309],
    67: ["file_1360.9_1361.9.ms", 11310, 11363],
    68: ["file_1361.9_1362.9.ms", 11364, 11417],
    69: ["file_1362.9_1363.9.ms", 11418, 11471],
    70: ["file_1363.9_1364.9.ms", 11472, 11525],
    71: ["file_1364.9_1365.9.ms", 11526, 11579],
    72: ["file_1365.9_1366.9.ms", 11580, 11633],
    73: ["file_1366.9_1367.9.ms", 11634, 11687],
    74: ["file_1367.9_1368.9.ms", 11688, 11741],
    75: ["file_1368.9_1369.9.ms", 11742, 11795],
    76: ["file_1369.9_1370.9.ms", 11796, 11849],
    77: ["file_1370.9_1371.9.ms", 11850, 11903],
    78: ["file_1371.9_1372.9.ms", 11904, 11957],
    79: ["file_1372.9_1373.9.ms", 11958, 12011],
    80: ["file_1373.9_1374.9.ms", 12012, 12065],
    81: ["file_1374.9_1375.9.ms", 12066, 12119],
    82: ["file_1375.9_1376.9.ms", 12120, 12173],
    83: ["file_1376.9_1377.9.ms", 12174, 12227],
    84: ["file_1377.9_1378.9.ms", 12228, 12281],
    85: ["file_1378.9_1379.9.ms", 12282, 12335],
    86: ["file_1379.9_1380.9.ms", 12336, 12389],
    87: ["file_1380.9_1381.9.ms", 12390, 12443],
    88: ["file_1381.9_1382.9.ms", 12444, 12497],
    89: ["file_1382.9_1383.9.ms", 12498, 12551],
    90: ["file_1383.9_1384.9.ms", 12552, 12605],
    91: ["file_1384.9_1385.9.ms", 12606, 12659],
    92: ["file_1385.9_1386.9.ms", 12660, 12713],
    93: ["file_1386.9_1387.9.ms", 12714, 12767],
    94: ["file_1387.9_1388.9.ms", 12768, 12821],
    95: ["file_1388.9_1389.9.ms", 12822, 12875],
    96: ["file_1389.9_1390.9.ms", 12876, 12929],
    97: ["file_1390.9_1391.9.ms", 12930, 12983],
    98: ["file_1391.9_1392.9.ms", 12984, 13037],
    99: ["file_1392.9_1393.9.ms", 13038, 13091],
    100: ["file_1393.9_1394.9.ms", 13092, 13145],
    101: ["file_1394.9_1395.9.ms", 13146, 13199],
    102: ["file_1395.9_1396.9.ms", 13200, 13253],
    103: ["file_1396.9_1397.9.ms", 13254, 13307],
    104: ["file_1397.9_1398.9.ms", 13308, 13361],
    105: ["file_1398.9_1399.9.ms", 13362, 13415],
    106: ["file_1399.9_1400.9.ms", 13416, 13469],
    107: ["file_1400.9_1401.9.ms", 13470, 13523],
    108: ["file_1401.9_1402.9.ms", 13524, 13577],
    109: ["file_1402.9_1403.9.ms", 13578, 13631],
    110: ["file_1403.9_1404.9.ms", 13632, 13685],
    111: ["file_1404.9_1405.9.ms", 13686, 13739],
    112: ["file_1405.9_1406.9.ms", 13740, 13793],
    113: ["file_1406.9_1407.9.ms", 13794, 13847],
    114: ["file_1407.9_1408.9.ms", 13848, 13901],
    115: ["file_1408.9_1409.9.ms", 13902, 13955],
    116: ["file_1409.9_1410.9.ms", 13956, 14009],
    117: ["file_1410.9_1411.9.ms", 14010, 14063],
    118: ["file_1411.9_1412.9.ms", 14064, 14117],
    119: ["file_1412.9_1413.9.ms", 14118, 14171],
    120: ["file_1413.9_1414.9.ms", 14172, 14225],
    121: ["file_1414.9_1415.9.ms", 14226, 14279],
    122: ["file_1415.9_1416.9.ms", 14280, 14333],
    123: ["file_1416.9_1417.9.ms", 14334, 14387],
    124: ["file_1417.9_1418.9.ms", 14388, 14441],
    125: ["file_1418.9_1419.9.ms", 14442, 14495],
    126: ["file_1419.9_1420.9.ms", 14496, 14549],
    127: ["file_1420.9_1421.9.ms", 14550, 14603],
    128: ["file_1421.9_1422.9.ms", 14604, 14657],
    129: ["file_1422.9_1423.9.ms", 14658, 14711],
    130: ["file_1423.9_1424.9.ms", 14712, 14765],
    131: ["file_1424.9_1425.9.ms", 14766, 14819],
    132: ["file_1425.9_1426.9.ms", 14820, 14873],
    133: ["file_1426.9_1427.9.ms", 14874, 14927],
    134: ["file_1427.9_1428.9.ms", 14928, 14981],
    135: ["file_1428.9_1429.9.ms", 14982, 15035],
    136: ["file_1429.9_1430.9.ms", 15036, 15089],
    137: ["file_1430.9_1431.9.ms", 15090, 15143],
    138: ["file_1431.9_1432.9.ms", 15144, 15197],
    139: ["file_1432.9_1433.9.ms", 15198, 15251],
    140: ["file_1433.9_1434.9.ms", 15252, 15305],
    141: ["file_1434.9_1435.9.ms", 15306, 15359],
    142: ["file_1435.9_1436.9.ms", 15360, 15413],
    143: ["file_1436.9_1437.9.ms", 15414, 15467],
    144: ["file_1437.9_1438.9.ms", 15468, 15521],
    145: ["file_1438.9_1439.9.ms", 15522, 15575],
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
