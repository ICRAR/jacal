#
# ASKAP auto-generated file
#
ASKAP_ROOT=/home/drew/repositories/ASKAPsoft
export ASKAP_ROOT
if [ "${PATH}" !=  "" ]
then
    PATH=${ASKAP_ROOT}/Code/Components/Services/correlatorsim/current/install/bin:${ASKAP_ROOT}/3rdParty/Ice/Ice-3.5.0/install/bin:${ASKAP_ROOT}/3rdParty/Berkeley-DB/db-5.3.21.NC/install/bin:${ASKAP_ROOT}/3rdParty/bzip2/bzip2-1.0.5/install/bin:${ASKAP_ROOT}/3rdParty/mcpp/mcpp-2.7.2/install/bin:${ASKAP_ROOT}/3rdParty/openssl/openssl-1.0.1h/install/bin:${ASKAP_ROOT}/3rdParty/gsl/gsl-1.16/install/bin:${ASKAP_ROOT}/Code/Base/askap/current/install/bin:${ASKAP_ROOT}/3rdParty/fftw/fftw-3.3.3/install/bin:${ASKAP_ROOT}/3rdParty/LOFAR/Blob/Blob-1.2/install/bin:${ASKAP_ROOT}/3rdParty/LOFAR/Common/Common-3.3/install/bin:${ASKAP_ROOT}/3rdParty/apr-util/apr-util-1.3.9/install/bin:${ASKAP_ROOT}/3rdParty/expat/expat-2.0.1/install/bin:${ASKAP_ROOT}/3rdParty/apr/apr-1.3.9/install/bin:${ASKAP_ROOT}/3rdParty/casacore/casacore-2.0.3/install/bin:${ASKAP_ROOT}/3rdParty/wcslib/wcslib-4.18/install/bin:${ASKAP_ROOT}/3rdParty/fftw/fftw-3.3.3/install/bin:${PATH}
else
    PATH=${ASKAP_ROOT}/Code/Components/Services/correlatorsim/current/install/bin:${ASKAP_ROOT}/3rdParty/Ice/Ice-3.5.0/install/bin:${ASKAP_ROOT}/3rdParty/Berkeley-DB/db-5.3.21.NC/install/bin:${ASKAP_ROOT}/3rdParty/bzip2/bzip2-1.0.5/install/bin:${ASKAP_ROOT}/3rdParty/mcpp/mcpp-2.7.2/install/bin:${ASKAP_ROOT}/3rdParty/openssl/openssl-1.0.1h/install/bin:${ASKAP_ROOT}/3rdParty/gsl/gsl-1.16/install/bin:${ASKAP_ROOT}/Code/Base/askap/current/install/bin:${ASKAP_ROOT}/3rdParty/fftw/fftw-3.3.3/install/bin:${ASKAP_ROOT}/3rdParty/LOFAR/Blob/Blob-1.2/install/bin:${ASKAP_ROOT}/3rdParty/LOFAR/Common/Common-3.3/install/bin:${ASKAP_ROOT}/3rdParty/apr-util/apr-util-1.3.9/install/bin:${ASKAP_ROOT}/3rdParty/expat/expat-2.0.1/install/bin:${ASKAP_ROOT}/3rdParty/apr/apr-1.3.9/install/bin:${ASKAP_ROOT}/3rdParty/casacore/casacore-2.0.3/install/bin:${ASKAP_ROOT}/3rdParty/wcslib/wcslib-4.18/install/bin:${ASKAP_ROOT}/3rdParty/fftw/fftw-3.3.3/install/bin
fi
export PATH
if [ "${CLASSPATH}" !=  "" ]
then
    CLASSPATH=${ASKAP_ROOT}/3rdParty/Ice/Ice-3.5.0/install/lib/Ice-3.5.0.jar:${ASKAP_ROOT}/3rdParty/Ice/Ice-3.5.0/install/lib/Freeze.jar:${ASKAP_ROOT}/3rdParty/Ice/Ice-3.5.0/install/lib/IceStorm.jar:${CLASSPATH}
else
    CLASSPATH=${ASKAP_ROOT}/3rdParty/Ice/Ice-3.5.0/install/lib/Ice-3.5.0.jar:${ASKAP_ROOT}/3rdParty/Ice/Ice-3.5.0/install/lib/Freeze.jar:${ASKAP_ROOT}/3rdParty/Ice/Ice-3.5.0/install/lib/IceStorm.jar
fi
export CLASSPATH
if [ "${LD_LIBRARY_PATH}" !=  "" ]
then
    LD_LIBRARY_PATH=${ASKAP_ROOT}/Code/Components/Services/correlatorsim/current/install/lib:${ASKAP_ROOT}/3rdParty/cmdlineparser/cmdlineparser-0.1.1/install/lib:${ASKAP_ROOT}/Code/Components/Services/icewrapper/current/install/lib:${ASKAP_ROOT}/Code/Interfaces/cpp/current/install/lib:${ASKAP_ROOT}/3rdParty/Ice/Ice-3.5.0/install/lib:${ASKAP_ROOT}/3rdParty/Berkeley-DB/db-5.3.21.NC/install/lib:${ASKAP_ROOT}/3rdParty/bzip2/bzip2-1.0.5/install/lib:${ASKAP_ROOT}/3rdParty/mcpp/mcpp-2.7.2/install/lib:${ASKAP_ROOT}/3rdParty/openssl/openssl-1.0.1h/install/lib:${ASKAP_ROOT}/Code/Components/Services/common/current/install/lib:${ASKAP_ROOT}/Code/Base/scimath/current/install/lib:${ASKAP_ROOT}/3rdParty/gsl/gsl-1.16/install/lib:${ASKAP_ROOT}/Code/Base/imagemath/current/install/lib:${ASKAP_ROOT}/Code/Base/askap/current/install/lib:${ASKAP_ROOT}/3rdParty/fftw/fftw-3.3.3/install/lib:${ASKAP_ROOT}/3rdParty/LOFAR/Blob/Blob-1.2/install/lib:${ASKAP_ROOT}/3rdParty/LOFAR/Common/Common-3.3/install/lib:${ASKAP_ROOT}/3rdParty/boost/boost-1.56.0/install/lib:${ASKAP_ROOT}/3rdParty/log4cxx/log4cxx-0.10.0/install/lib:${ASKAP_ROOT}/3rdParty/apr-util/apr-util-1.3.9/install/lib:${ASKAP_ROOT}/3rdParty/expat/expat-2.0.1/install/lib:${ASKAP_ROOT}/3rdParty/apr/apr-1.3.9/install/lib:${ASKAP_ROOT}/3rdParty/casa-components/casa-components-1.6.0/install/lib:${ASKAP_ROOT}/3rdParty/casacore/casacore-2.0.3/install/lib:${ASKAP_ROOT}/3rdParty/lapack/lapack-3.4.0/install/lib:${ASKAP_ROOT}/3rdParty/blas/blas-1.0/install/lib:${ASKAP_ROOT}/3rdParty/wcslib/wcslib-4.18/install/lib:${ASKAP_ROOT}/3rdParty/cfitsio/cfitsio-3.35/install/lib:${ASKAP_ROOT}/3rdParty/fftw/fftw-3.3.3/install/lib:${LD_LIBRARY_PATH}
else
    LD_LIBRARY_PATH=${ASKAP_ROOT}/Code/Components/Services/correlatorsim/current/install/lib:${ASKAP_ROOT}/3rdParty/cmdlineparser/cmdlineparser-0.1.1/install/lib:${ASKAP_ROOT}/Code/Components/Services/icewrapper/current/install/lib:${ASKAP_ROOT}/Code/Interfaces/cpp/current/install/lib:${ASKAP_ROOT}/3rdParty/Ice/Ice-3.5.0/install/lib:${ASKAP_ROOT}/3rdParty/Berkeley-DB/db-5.3.21.NC/install/lib:${ASKAP_ROOT}/3rdParty/bzip2/bzip2-1.0.5/install/lib:${ASKAP_ROOT}/3rdParty/mcpp/mcpp-2.7.2/install/lib:${ASKAP_ROOT}/3rdParty/openssl/openssl-1.0.1h/install/lib:${ASKAP_ROOT}/Code/Components/Services/common/current/install/lib:${ASKAP_ROOT}/Code/Base/scimath/current/install/lib:${ASKAP_ROOT}/3rdParty/gsl/gsl-1.16/install/lib:${ASKAP_ROOT}/Code/Base/imagemath/current/install/lib:${ASKAP_ROOT}/Code/Base/askap/current/install/lib:${ASKAP_ROOT}/3rdParty/fftw/fftw-3.3.3/install/lib:${ASKAP_ROOT}/3rdParty/LOFAR/Blob/Blob-1.2/install/lib:${ASKAP_ROOT}/3rdParty/LOFAR/Common/Common-3.3/install/lib:${ASKAP_ROOT}/3rdParty/boost/boost-1.56.0/install/lib:${ASKAP_ROOT}/3rdParty/log4cxx/log4cxx-0.10.0/install/lib:${ASKAP_ROOT}/3rdParty/apr-util/apr-util-1.3.9/install/lib:${ASKAP_ROOT}/3rdParty/expat/expat-2.0.1/install/lib:${ASKAP_ROOT}/3rdParty/apr/apr-1.3.9/install/lib:${ASKAP_ROOT}/3rdParty/casa-components/casa-components-1.6.0/install/lib:${ASKAP_ROOT}/3rdParty/casacore/casacore-2.0.3/install/lib:${ASKAP_ROOT}/3rdParty/lapack/lapack-3.4.0/install/lib:${ASKAP_ROOT}/3rdParty/blas/blas-1.0/install/lib:${ASKAP_ROOT}/3rdParty/wcslib/wcslib-4.18/install/lib:${ASKAP_ROOT}/3rdParty/cfitsio/cfitsio-3.35/install/lib:${ASKAP_ROOT}/3rdParty/fftw/fftw-3.3.3/install/lib
fi
export LD_LIBRARY_PATH
if [ "${PYTHONPATH}" !=  "" ]
then
    PYTHONPATH=${ASKAP_ROOT}/3rdParty/Ice/Ice-3.5.0/install/lib/python2.7/site-packages:${PYTHONPATH}
else
    PYTHONPATH=${ASKAP_ROOT}/3rdParty/Ice/Ice-3.5.0/install/lib/python2.7/site-packages
fi
export PYTHONPATH
