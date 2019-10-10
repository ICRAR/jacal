#
#    ICRAR - International Centre for Radio Astronomy Research
#    (c) UWA - The University of Western Australia, 2016
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

import os
import subprocess
import sys
import sysconfig

from setuptools import find_packages
from setuptools import setup
from setuptools.command.install import install
install_requires = [
    'daliuge >= 0.6.2',
]
setup(
      name='dlg-integrate',
      version="0.1.0",
      description=u'integrate 3rd with DALiuGE',
      long_description="",
      author='weishoulin',
      author_email='weishoulin@astrolab.cn',
      license="LGPLv2+",
    #   install_requires=install_requires,
      packages=find_packages(exclude=('test', 'test.*', 'fabfile'))
)
