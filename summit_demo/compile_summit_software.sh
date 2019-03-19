#!/bin/bash
#
# ICRAR - International Centre for Radio Astronomy Research
# (c) UWA - The University of Western Australia, 2019
# Copyright by UWA (in the framework of the ICRAR)
#
# (c) Copyright 2019 CSIRO
# Australia Telescope National Facility (ATNF)
# Commonwealth Scientific and Industrial Research Organisation (CSIRO)
# PO Box 76, Epping NSW 1710, Australia
# atnf-enquiries@csiro.au
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston,
# MA 02111-1307  USA
#

if [ $# -lt 3 ]; then
	echo "Usage: $0 <system> <num-jobs> <prefix>" 1>&2
	exit 1
fi

SYSTEM=$1
NUM_JOBS=$2
PREFIX=$3

if [ $SYSTEM != centos -a $SYSTEM != ubuntu ]; then
	echo "Unsupported system: $SYSTEM" 1>&2
	echo "Supported systems are centos and ubuntu" 1>&2
	exit 1
fi

if [ $EUID == 0 ]; then
	SUDO=
else
	SUDO=sudo
fi

install_dependencies() {
	if [ $SYSTEM == ubuntu ]; then
		$SUDO apt install -y \
		    boost-devel \    # casacore
		    cfitsio-devel \  # casacore
		    cmake3 \         # adios, casacore, oskar
		    fftw3-devel \    # casacore
		    flex bison \     # casascore
		    git \            # many
		    libffi-devel \   # cryptography (python) -> paramiko -> daliuge
		    openblas-devel \ # casacore
		    openmpi-devel \  # adios, casacore, oskar
		    openssl-devel \  # cryptography (see above)
		    patch \          # lofar-common
		    python-devel \   # casacore, few python packages
		    python-pip \     # so we can pip install virtualenv
		    python2-numpy \  # casacore, oskar, few python packages
		    svn \            # lofar-blob, lofar-common
		    wcslib-devel     # casacore
		CMAKE=cmake
	else
		$SUDO yum --assumeyes install \
		    boost-devel \ cfitsio-devel \
		    cmake3 \
		    fftw3-devel \
		    flex bison \
		    gcc-g++ \
		    git \
		    gsl-devel \
		    libffi-devel \
		    log4cxx-devel \
		    make \
		    openblas-devel \
		    openmpi-devel \
		    openssl-devel \
		    patch \
		    python-devel \
		    python-pip \
		    svn \
		    wcslib-devel
		CMAKE=cmake3
	fi
}

repo2dir() {
	d=`basename $1`
	echo ${d%%.git}
}

# Nice-to-use macro
build_and_install() {
	git clone --branch $2 $1
	cd `repo2dir $1`
	shift; shift
	mkdir build
	cd build
	${CMAKE} .. -DCMAKE_INSTALL_PREFIX="$PREFIX" "$@"
	make all -j${NUM_JOBS}
	make install -j${NUM_JOBS}
	cd ../..
}

install_dependencies

# CentOS, you cheecky...
if [ $SYSTEM == centos ]; then
	source /etc/profile.d/modules.sh
	module load mpi
fi

# Setup our environment
export LD_LIBRARY_PATH=$PREFIX/lib64:$LD_LIBRARY_PATH

# Let's work with a virtualenv from now on
pip install --user virtualenv
virtualenv $PREFIX
source $PREFIX/bin/activate
pip install numpy

# Go, go, go!
build_and_install https://github.com/ornladios/ADIOS2 master
build_and_install https://github.com/casacore/casacore master -DUSE_ADIOS2=ON -DBUILD_TESTING=OFF
build_and_install https://github.com/casacore/casarest master -DBUILD_TESTING=OFF
build_and_install https://github.com/ICRAR/OSKAR master -DCMAKE_CXX_FLAGS="-std=c++11"
build_and_install https://bitbucket.csiro.au/scm/askapsdp/lofar-common.git cmake-improvements -DCMAKE_CXX_FLAGS="-Dcasa=casacore"
build_and_install https://bitbucket.csiro.au/scm/askapsdp/lofar-blob.git cmake-improvements -DCMAKE_CXX_FLAGS="-Dcasa=casacore"
build_and_install https://bitbucket.csiro.au/scm/askapsdp/base-askap.git operator-overload-fix -DCMAKE_CXX_FLAGS="-Dcasa=casacore"
build_and_install https://bitbucket.csiro.au/scm/askapsdp/base-logfilters.git cmake-improvements -DCMAKE_CXX_FLAGS="-Dcasa=casacore"
build_and_install https://bitbucket.csiro.au/scm/askapsdp/base-imagemath.git compilation-fixes -DCMAKE_CXX_FLAGS="-Dcasa=casacore"
build_and_install https://bitbucket.csiro.au/scm/askapsdp/base-scimath.git cmake-improvements -DCMAKE_CXX_FLAGS="-Dcasa=casacore"
build_and_install https://bitbucket.csiro.au/scm/askapsdp/base-askapparallel.git cmake-improvements -DCMAKE_CXX_FLAGS="-Dcasa=casacore"
build_and_install https://bitbucket.csiro.au/scm/askapsdp/base-accessors.git compilation_fixes -DCMAKE_CXX_FLAGS="-Dcasa=casacore"
build_and_install https://bitbucket.csiro.au/scm/askapsdp/yandasoft.git compilation-fixes -DCMAKE_CXX_FLAGS="-Dcasa=casacore"

# Python stuff
pip install git+https://github.com/ICRAR/daliuge
cd OSKAR/python
sed -i "s|include_dirs.*\$|\\0:$PREFIX/include|" setup.cfg
sed -i "s|library_dirs.*\$|\\0:$PREFIX/lib:$PREFIX/lib64|" setup.cfg
pip install
cd ../..
