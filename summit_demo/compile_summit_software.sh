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
	echo " -s <system>   Target system, supported values are centos (default) and ubuntu"
	echo " -c <compiler> Compiler suite to use, supported values are gcc (default) and clang"
	echo " -m <cmake>    Cmake binary to use, must be >= 3.1, defaults to cmake"
	echo " -j <jobs>     Number of parallel compilation jobs, defaults to 1"
	echo " -p <prefix>   Prefix for installation, defaults to /usr/local"
	echo " -w <workdir>  Working directory, defaults to ."
	echo " -W            Remove the working directory at the end of the build"
	echo " -E            Build extras (i.e. cfitsio, wcslib, apr, apr-util, log4cxx and metis, useful in HPC centers)"
	echo " -o            Do *not* build OSKAR"
	echo " -i            Do *not* install system dependencies"
	echo " -a            Do *not* build ADIOS2, implies -C 2.4.0"
	echo " -C <version>  Casacore version to build, values are master (default), 2.4.0 and 2.1.0"
	echo " -A <opts>     Extra casacore cmake options"
	echo " -r <opts>     Extra casarest cmake options"
	echo " -y <opts>     Extra yandasoft common cmake options"
	echo " -O <opts>     Extra OSKAR cmake options"
	echo " -P            Use Python 3 - NOTE: Only tested with CentOS7 on POWER9"
}

banner() {
	msg="** $@ **"
	echo "$msg" | sed -n '{h; x; s/./*/gp; x; h; p; x; s/./*/gp}';
}

try() {
	"$@"
	status=$?
	if [ $status -ne 0 ]; then
		echo "Command exited with status $status, aborting build now: $@" 1>&2
		exit 1
	fi
}

check_supported_values() {
	val_name=$1
	given_val=$2
	shift; shift
	for supported in "$@"; do
		if [ "$given_val" == "$supported" ]; then
			return
		fi
	done
	echo "Unsupported $val_name: $given_val" 1>&2
	echo "Supported $val_name values are: $@" 1>&2
	exit 1
}

system=centos
compiler=gcc
cmake=
jobs=1
prefix=/usr/local
workdir=.
remove_workdir=no
build_extras=no
build_oskar=yes
use_python3=yes
install_dependencies=yes
build_adios=yes
casacore_version=master
casacore_opts=
casarest_opts=
yandasoft_opts=
oskar_opts=-DCUDA_ARCH="7.0"

while getopts "h?s:c:m:j:p:w:WPEoiaC:A:r:y:O:" opt
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
		m)
			cmake="$OPTARG"
			;;
		j)
			jobs="$OPTARG"
			;;
		p)
			prefix="$OPTARG"
			;;
		w)
			workdir="$OPTARG"
			;;
		W)
			remove_workdir=yes
			;;
		E)
			build_extras=yes
			;;
		o)
			build_oskar=no
			;;
		i)
			install_dependencies=no
			;;
		a)
			build_adios=no
			;;
		C)
			casacore_version="$OPTARG"
			;;
		A)
			casacore_opts="$OPTARG"
			;;
		r)
			casarest_opts="$OPTARG"
			;;
		y)
			yandasoft_opts="$OPTARG"
			;;
		O)
			oskar_opts="$OPTARG"
			;;
		P)
			use_python3=yes
			;;
		*)
			print_usage 1>&2
			exit 1
			;;
	esac
done

check_supported_values system $system centos ubuntu
check_supported_values compiler $compiler gcc clang cray intel
check_supported_values casacore_version $casacore_version master 2.4.0 2.0.3
if [ $casacore_version != master ]; then
	build_adios=no
fi

if [ $EUID == 0 ]; then
	SUDO=
else
	SUDO=sudo
fi

if [ -z "$cmake" ]; then
	if [ $system == centos ]; then
		cmake=cmake3
	else
		cmake=cmake
	fi
fi

install_dependencies() {
	if [ $system == ubuntu ]; then
		$SUDO apt update
		$SUDO apt install -y \
		    cmake                         `# many` \
		    flex bison                    `# casacore` \
		    gfortran                      `# many` \
		    git                           `# many` \
		    g++                           `# many` \
		    libboost-dev                  `# casacore` \
		    libboost-filesystem-dev       `# yandasoft` \
		    libboost-program-options-dev  `# base-askap` \
		    libboost-signals-dev          `# base-askap` \
		    libboost-system-dev           `# casarest` \
		    libboost-thread-dev           `# casarest` \
		    libcfitsio-dev                `# casacore` \
		    libffi-dev                    `# cryptography (python) -> paramiko -> daliuge` \
		    libfftw3-dev                  `# casacore` \
		    libgsl-dev                    `# many` \
		    liblog4cxx-dev                `# yandasoft` \
		    libopenblas-dev               `# casacore` \
		    libopenmpi-dev                `# adios, casacore, oskar` \
		    libpython-dev                 `# casacore, few python packages` \
		    make                          `# many` \
		    patch                         `# lofar-common` \
		    python-pip                    `# so we can pip install virtualenv` \
		    subversion                    `# lofar-blob, lofar-common` \
		    wcslib-dev                    `# casacore`
		$SUDO apt clean
		if [ $compiler == clang ]; then
			$SUDO apt install -y clang
		fi
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
		if [ $use_python3 == yes ]; then
			$SUDO yum --assumeyes install python34 python34-devel python34-pip boost-python34-devel
		fi
		$SUDO yum clean all
	fi
}

repo2dir() {
	d=`basename $1`
	echo ${d%%.git}
}

url2tarball() {
	t="`basename $1`"
	echo $t
}

tarball2dir() {
	d=`basename $1`
	d=${d%%.tar.gz}
	d=${d%%.tar.bz2}
	echo $d
}

download() {
	try wget "$1"
}

_build() {
	banner Running make all -j${jobs}
	try make all -j${jobs}
	try make install -j${jobs}
}

_prebuild_cmake() {
	test -d build || try mkdir build
	cd build
	if [ $compiler == clang ]; then
		comp_opts="-DCMAKE_CXX_COMPILER=clang++ -DCMAKE_C_COMPILER=clang"
	elif [ $compiler == cray ]; then
		comp_opts="-DCMAKE_CXX_COMPILER=CC -DCMAKE_C_COMPILER=cc"
	elif [ $compiler == intel ]; then
		comp_opts="-DCMAKE_CXX_COMPILER=icpc -DCMAKE_C_COMPILER=icc"
	else
		comp_opts="-DCMAKE_CXX_COMPILER=g++ -DCMAKE_C_COMPILER=gcc"
	fi
	banner Running ${cmake} .. -DCMAKE_INSTALL_PREFIX="$prefix" $comp_opts "$@"
	try ${cmake} .. -DCMAKE_INSTALL_PREFIX="$prefix" $comp_opts "$@"
}

_prebuild_configure() {
	if [ $compiler == clang ]; then
		CC=clang
		CXX=clang++
	elif [ $compiler == cray ]; then
		CC=CC
		CXX=cc
	elif [ $compiler == intel ]; then
		CC=icc
		CXX=icpc
	else
		CC=gcc
		CXX=g++
	fi
	banner Running CC=$CC CXX=$CXX ./configure --prefix="$prefix" "$@"
	CC=$CC CXX=$CXX ./configure --prefix="$prefix" "$@"
}

# Build macro
build_and_install() {

	url="$1"
	if [[ "$url" == *.tar.gz || "$url" == *.tar.bz2 ]]; then
		srcdir=$(tarball2dir $(url2tarball "$url"))
		srctype=tarball
	else
		srcdir=`repo2dir $1`
		srctype=git
	fi

	# Download/clone
	if [ ! -d "$srcdir" ]; then
		if [ $srctype = tarball ]; then
			banner Downloading $url
			mkdir -p tarballs || true
			tarname=`url2tarball "$url"`
			download "$url"
			mv $tarname tarballs/
			try tar xf tarballs/$tarname
		else
			is_branch=yes
			ref=$2
			if [[ "$ref" =~ COMMIT-(.*) ]]; then
				ref=${BASH_REMATCH[1]}
				is_branch=no
			fi
			banner Cloning $url
			try git clone $1
			cd `repo2dir $url`
			if [ $is_branch == yes ]; then
				git checkout -b $ref origin/$ref
			else
				git checkout -b working_copy
				git reset --hard $ref
			fi
			cd ..
		fi
	fi

	# Remove arguments used for downloading
	# (a bit ugly, but it works)
	if [ $srctype = tarball ]; then
		shift
	else
		shift; shift
	fi

	# Build
	banner Building $srcdir
	cd $srcdir
	if [ -e configure ]; then
		_prebuild_configure "$@"
		_build
		cd ..
	elif [ -e CMakeLists.txt ]; then
		_prebuild_cmake "$@"
		_build
		cd ../..
	elif [ -x autogen.sh ]; then
		try ./autogen.sh
		_prebuild_configure "$@"
		_build
		cd ..
	fi
}

source_venv() {
	if [ ! -f $prefix/bin/activate ]; then
		if [ $use_python3 == yes ]; then
			python3 -m venv $prefix
		else
			if [ -n "`command -v virtualenv 2> /dev/null`" ]; then
				try virtualenv $prefix
			else
				try pip install --user virtualenv
				try ~/.local/bin/virtualenv $prefix
			fi
		fi
	fi
	source $prefix/bin/activate
}

original_dir="$PWD"
if [ ! -d "$workdir" ]; then
	try mkdir -p "$workdir"
fi
cd "$workdir"

if [ $install_dependencies == yes ]; then
	install_dependencies
fi

# CentOS, you cheecky...
if [ $system == centos ]; then
	source /etc/profile.d/modules.sh
	module load mpi
fi

# Setup our environment
export LD_LIBRARY_PATH=$prefix/lib64:$LD_LIBRARY_PATH

# Let's work with a virtualenv
banner Setting up Python virtrual environment

source_venv
try pip install numpy
try pip install mpi4py

# Extras, not always needed
if [ $build_extras = yes ]; then
	build_and_install http://heasarc.gsfc.nasa.gov/FTP/software/fitsio/c/cfitsio-3.47.tar.gz --disable-curl --enable-reentrant
	build_and_install ftp://ftp.atnf.csiro.au/pub/software/wcslib/wcslib-6.4.tar.bz2 --without-pgplot
	build_and_install http://apache.spinellicreations.com/apr/apr-1.7.0.tar.bz2
	build_and_install http://mirrors.ibiblio.org/apache/apr/apr-util-1.6.1.tar.bz2 --with-apr="$prefix"
	build_and_install https://github.com/apache/logging-log4cxx master --with-apr="$prefix" --with-apr-util="$prefix"
fi

# ADIOS2, casacore and casarest
if [ $build_adios == yes ]; then
	build_and_install https://github.com/ornladios/ADIOS2 master -DADIOS2_BUILD_TESTING=OFF -DADIOS2_USE_Fortran=OFF -DADIOS2_USE_Python=OFF -DADIOS2_USE_Table=ON
fi

if [ $casacore_version == master -a $build_adios == yes ]; then
	casacore_opts+=" -DUSE_ADIOS2=ON"
fi
if [ $casacore_version == master ]; then
	casacore_version=summit_demo
else
	casacore_version=COMMIT-v$casacore_version
fi
build_and_install https://github.com/rtobar/casacore $casacore_version -DBUILD_TESTING=OFF -DBUILD_PYTHON=OFF $casacore_opts
if [ $casacore_version == summit_demo ]; then
	# Lets reset this back to master to save handling lots os special cases below!
	casacore_version=master
fi

if [ $casacore_version == master ]; then
	casarest_version=master
elif [ $casacore_version == COMMIT-v2.4.0 ]; then
	casarest_version=COMMIT-467ed6d
else
	casarest_version=COMMIT-v1.4.1
fi
build_and_install https://github.com/casacore/casarest $casarest_version -DBUILD_TESTING=OFF $casarest_opts

# Go, go, go, yandasoft!
if [ $casacore_version == master ]; then
	yandasoft_opts+=" -DCMAKE_CXX_FLAGS=-Dcasa=casacore"
fi
build_and_install https://bitbucket.csiro.au/scm/askapsdp/lofar-common.git master $yandasoft_opts
build_and_install https://bitbucket.csiro.au/scm/askapsdp/lofar-blob.git master $yandasoft_opts
build_and_install https://bitbucket.csiro.au/scm/askapsdp/base-askap.git operator-overload-fix $yandasoft_opts
build_and_install https://bitbucket.csiro.au/scm/askapsdp/base-logfilters.git refactor $yandasoft_opts
build_and_install https://bitbucket.csiro.au/scm/askapsdp/base-imagemath.git refactor $yandasoft_opts
build_and_install https://bitbucket.csiro.au/scm/askapsdp/base-scimath.git refactor $yandasoft_opts
build_and_install https://bitbucket.csiro.au/scm/askapsdp/base-askapparallel.git refactor $yandasoft_opts
build_and_install https://bitbucket.csiro.au/scm/askapsdp/base-accessors.git refactor $yandasoft_opts
build_and_install https://bitbucket.csiro.au/scm/askapsdp/yandasoft.git cmake-improvements $yandasoft_opts

# OSKAR
if [ $build_oskar == yes ]; then
	# Required when building with clang on centos
	if [ $system == centos -a $compiler == clang ]; then
		oskar_opts+=" -DFORCE_LIBSTDC++=ON"
	fi
	build_and_install https://github.com/ICRAR/OSKAR master $oskar_opts

	cd OSKAR/python
	sed -i "s|include_dirs.*\$|\\0:$prefix/include|" setup.cfg
	sed -i "s|library_dirs.*\$|\\0:$prefix/lib:$prefix/lib64|" setup.cfg
	if [ $system == centos -a $compiler == clang ]; then
		sed -i "s|library_dirs.*\$|\\0:$MPI_HOME/lib|" setup.cfg
	fi
	try pip install mpi4py
	try pip install .
	cd ../..
fi

banner Installing DALiuGE
# DALiuGE
# 'centos' here means 'power9', where we need to build pyzmq ourselves
# since the src dist from PyPI fails to build
if [ $system == centos -a $use_python3 == yes ]; then
	try pip install cython
	try git clone https://github.com/zeromq/pyzmq
	cd pyzmq
	try python setup.py install
	cd ..
fi
try pip install git+https://github.com/ICRAR/daliuge

# spead2
banner Installing spead2
try pip install spead2==1.10

if [ $remove_workdir == yes ]; then
	cd $original_dir
	rm -rf "$workdir"
fi
