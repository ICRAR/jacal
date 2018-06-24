#!/bin/bash --login

#SBATCH   --account=askaprt
#SBATCH   --partition=workq
#SBATCH   --job-name=Daliuge-Jacal-Test
#SBATCH   --nodes=3
#SBATCH   --ntasks-per-node=1
#SBATCH   --time=01:00:00

module swap PrgEnv-cray PrgEnv-gnu
module load python/2.7.14
module load mpi4py

#
# run this for the first time
#pip install mpi4py

# run "JACAL-enabled" DAliuGe node managers on multiple nodes on Athena
SOFT_HOME=/home/sord/soft
JACAL_HOME=$SOFT_HOME/jacal
ASKAP_HOME=$SOFT_HOME/askapsdp
ASKAP_3RD=$ASKAP_HOME/3rdParty

JACAL_LIB_PATH=$JACAL_HOME/apps/askap/:\
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
$ASKAP_3RD/casa-components/casa-components-1.6.0/install/lib:\
$ASKAP_3RD/Ice/Ice-3.5.0/install/lib

source ${ASKAP_HOME}/Code/Base/askap/current/init_package_env.sh
source ${ASKAP_HOME}/Code/Components/Synthesis/synthesis/current/init_package_env.sh
source ${ASKAP_HOME}/Code/Components/CP/pipelinetasks/current/init_package_env.sh
#source ${ASKAP_HOME}/Code/Components/Analysis/analysis/current/init_package_env.sh
#source ${ASKAP_HOME}/Code/Components/CP/simager/current/init_package_env.sh
source ${ASKAP_HOME}/Code/Components/CP/askap_imager/current/init_package_env.sh
source ${ASKAP_HOME}/Code/Interfaces/cpp/current/init_package_env.sh
#source /group/pawsey0245/software/daliuge/bin/activate
#echo 'before: '$LD_LIBRARY_PATH
export LD_LIBRARY_PATH=$JACAL_LIB_PATH:$LD_LIBRARY_PATH
#echo $LD_LIBRARY_PATH

DALIUGE_SRC=$SOFT_HOME/daliuge
LOG_ROOT=$SOFT_HOME/jacal_logs
MYENV=$SOFT_HOME/daliuge_env/

source ${MYENV}"/bin/activate"

MYPYTHON=${MYENV}/bin/python

MYCLUSTER=$JACAL_HOME"/apps/askap/functests/calibration/start_dfms_bracewell.py"

#MYCLUSTER=" -m dlg.deploy.pawsey.start_dfms_cluster"
LG_GRAPH=$JACAL_HOME"/apps/askap/functests/SKA/ska_spectral_line_galaxy.json"

SID=$(date +"%Y-%m-%d_%H-%M-%S")
LOG_DIR=$LOG_ROOT"/"$SID
echo "Creating direcotry "$LOG_DIR
mkdir $LOG_DIR

#echo $LD_LIBRARY_PATH
#ulimit -c unlimited

#dlg nm -v --no-dlm
srun -N 3 -n 3 $MYPYTHON $MYCLUSTER -l $LOG_DIR -L $LG_GRAPH 
