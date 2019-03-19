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

print_usage() {
	echo "Usage: $0 [options]"
	echo
	echo "Options:"
	echo " -s system. Supported values are centos and ubuntu"
	echo " -c compiler. Supported values are gcc and clang"
	echo " -j jobs. Number of parallel compilation jobs"
	echo " -p prefix. Prefix for installation, defaults to /usr/local"
}

jobs=1
prefix=/usr/local

while getopts "h?s:c:j:p:" opt
do
	case "$opt" in
		[h?])
			print_usage
			exit 0
			;;
		s)
			system="$OPTARG"
			;;
		c)
			compiler="$OPTARG"
			;;
		j)
			jobs="$OPTARG"
			;;
		p)
			prefix="$OPTARG"
			;;
		*)
			print_usage 1>&2
			exit 1
			;;
	esac
done

if [ "$system" != centos -a "$system" != ubuntu ]; then
	echo "Unsupported system: $system" 1>&2
	echo "Supported systems are centos and ubuntu" 1>&2
	exit 1
fi

if [ "$compiler" != gcc -a "$compiler" != clang ]; then
	echo "Unsupported compiler: $SYSTEM" 1>&2
	echo "Supported compilers are gcc and clang" 1>&2
	exit 1
fi

if [ $EUID == 0 ]; then
	SUDO=
else
	SUDO=sudo
fi

install_dependencies() {
	if [ $system == ubuntu ]; then
		$SUDO apt install -y \
		    boost-devel     `# casacore` \
		    cfitsio-devel   `# casacore` \
		    cmake3          `# many` \
		    fftw3-devel     `# casacore` \
		    flex bison      `# casacore` \
		    git             `# many` \
		    libffi-devel    `# cryptography (python) -> paramiko -> daliuge` \
		    openblas-devel  `# casacore` \
		    openmpi-devel   `# adios, casacore, oskar` \
		    openssl-devel   `# cryptography (see above)` \
		    patch           `# lofar-common` \
		    python-devel    `# casacore, few python packages` \
		    python-pip      `# so we can pip install virtualenv` \
		    python2-numpy   `# casacore, oskar, few python packages` \
		    svn             `# lofar-blob, lofar-common` \
		    wcslib-devel    `# casacore`
		CMAKE=cmake
	else
		$SUDO yum --assumeyes install \
		    boost-devel    `# casacore` \
		    cfitsio-devel  `# casacore` \
		    cmake3         `# many` \
		    fftw3-devel    `# casacore` \
		    flex bison     `# casacore, lofar-common` \
		    gcc-c++        `# many, including clang itself` \
		    git            `# many` \
		    gsl-devel      `# casacore, yandasoft` \
		    libffi-devel   `# cryptography (python) -> paramiko -> daliuge` \
		    log4cxx-devel  `# yandasoft` \
		    make           `# many` \
		    openblas-devel `# casacore` \
		    openmpi-devel  `# adios, casacore, oskar, yandasoft` \
		    openssl-devel  `# cryptography (see above)` \
		    patch          `# lofar-common` \
		    python-devel   `# casacore, oskar, few python packages` \
		    python-pip     `# so we can pip install virtualenv` \
		    svn            `# lofar-blob, lofar-common` \
		    wcslib-devel   `# casacore`
		if [ $compiler == clang ]; then
			$SUDO yum --assumeyes install clang
		fi
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
	if [ $compiler == clang ]; then
		comp_opts="-DCMAKE_CXX_COMPILER=clang++ -DCMAKE_C_COMPILER=clang"
	else
		comp_opts="-DCMAKE_CXX_COMPILER=g++ -DCMAKE_C_COMPILER=gcc"
	fi
	${CMAKE} .. -DCMAKE_INSTALL_PREFIX="$prefix" $comp_opts "$@"
	make all -j${jobs}
	make install -j${jobs}
	cd ../..
}

install_dependencies

# CentOS, you cheecky...
if [ $system == centos ]; then
	source /etc/profile.d/modules.sh
	module load mpi
fi

# Setup our environment
export LD_LIBRARY_PATH=$prefix/lib64:$LD_LIBRARY_PATH

# Let's work with a virtualenv from now on
pip install --user virtualenv
~/.local/bin/virtualenv $prefix
source $prefix/bin/activate
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
sed -i "s|include_dirs.*\$|\\0:$prefix/include|" setup.cfg
sed -i "s|library_dirs.*\$|\\0:$prefix/lib:$prefix/lib64|" setup.cfg
pip install
cd ../..
