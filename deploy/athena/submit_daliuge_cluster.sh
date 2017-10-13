# run "JACAL-enabled" DAliuGe node managers on multiple nodes on Athena


JACAL_HOME=/group/pawsey0245/software/jacal
ASKAP_HOME=/group/pawsey0245/software/askapsoft-CP-0.19.3
ASKAP_3RD=$ASKAP_HOME/3rdParty

JACAL_LIB_PATH=$JACAL_HOME/apps/askap/askapsoft_lib:\
$ASKAP_3RD/cfitsio/cfitsio-3.35/install/lib:\
$ASKAP_3RD/boost/boost-1.56.0/install/lib:\
$ASKAP_3RD/cmdlineparser/cmdlineparser-0.1.1/install/lib:\
$ASKAP_3RD/log4cxx/log4cxx-0.10.0/install/lib:\
$ASKAP_3RD/LOFAR/Common/Common-3.3/install/lib64:\
$ASKAP_3RD/LOFAR/Blob/Blob-1.2/install/lib64:\
$ASKAP_3RD/casacore/casacore-2.0.3/install/lib:\
$ASKAP_3RD/lapack/lapack-3.4.0/install/lib:\
$ASKAP_3RD/wcslib/wcslib-4.18/install/lib:\
$ASKAP_3RD/blas/blas-1.0/install/lib:\
$ASKAP_3RD/gsl/gsl-1.16/install/lib:\
$ASKAP_3RD/xerces-c/xerces-c-3.1.1/install/lib:\
$ASKAP_3RD/casa-components/casa-components-1.6.0/install/lib

source /group/pawsey0245/software/daliuge/bin/activate

LD_LIBRARY_PATH=$JACAL_LIB_PATH dlg nm -v --no-dlm
