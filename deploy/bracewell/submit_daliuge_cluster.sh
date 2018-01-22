#!/bin/bash --login
#SBATCH   --partition=knlq
#SBATCH   --job-name=Daliuge-Jacal-Test
#SBATCH   --nodes=3
#SBATCH   --ntasks-per-node=1
#SBATCH   --time=01:00:00
#SBATCH   --account=pawsey0245


# run this for the first time
#pip install mpi4py

# run "JACAL-enabled" DAliuGe node managers on multiple nodes on Bracewell

JACAL_HOME=/home/wu082/proj/jacal
ASKAP_HOME=/flush1/tob020/scm/git/askapsoft/
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

#source /group/pawsey0245/software/daliuge/bin/activate
#echo 'before: '$LD_LIBRARY_PATH
export LD_LIBRARY_PATH=$JACAL_LIB_PATH:$LD_LIBRARY_PATH
#echo $LD_LIBRARY_PATH

LOG_ROOT=/flush1/wu082/jacal_logs

MYPYTHON=/home/wu082/pyws/bin/python
MYCLUSTER=" -m dlg.deploy.pawsey.start_dfms_cluster"

LG_GRAPH=$JACAL_HOME"/deploy/bracewell/askap_LoadVis_bracewell.json"

SID=$(date +"%Y-%m-%d_%H-%M-%S")
LOG_DIR=$LOG_ROOT"/"$SID
echo "Creating direcotry "$LOG_DIR
mkdir $LOG_DIR

module load openmpi
echo $LD_LIBRARY_PATH
ulimit -c unlimited
mpirun -n 3 -N 3 $MYPYTHON $MYCLUSTER -l $LOG_DIR -L $LG_GRAPH
#dlg nm -v --no-dlm
