
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
"""
Mock objects for testing
"""
import logging

from dlg.drop import BarrierAppDROP
from dlg.io import OpenMode

LOGGER = logging.getLogger(__name__)


class DynLibAppMock(BarrierAppDROP):
    def initialize(self, **kwargs):
        super(DynLibAppMock, self).initialize(**kwargs)
        LOGGER.info(f"initialize DynLibAppMock: {kwargs}")
        self._dictionary = {key:value for (key,value) in kwargs.items()}

    def run(self):
        LOGGER.info(f"run DynLibAppMock: {self.__dict__}")
        for input_ in self.inputs:
            LOGGER.info(f"dict: {input_.__dict__}")
            drop_io = input_.getIO()
            drop_io.open(OpenMode.OPEN_READ)
            byte_array = bytearray()
            while True:
                data = drop_io.read(1024)
                if len(data) == 0:
                    break
                LOGGER.info(f"data: {data}")
                byte_array.extend(data)
            LOGGER.info(f"data: {byte_array}")
            drop_io.close()

    def dataURL(self):
        return "DynLibAppMock"
