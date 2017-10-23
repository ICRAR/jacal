#!/bin/bash -l

if [ $# -gt 0 ]; then
    TOPDIR=$1
else
    TOPDIR=daliuge
    ENVDIR=daliuge_env
fi
#
# first we need to build daliuge
# via a virtualenv
#
# test are we on galaxy
cd $WORKSPACE

if [[ $(hostname -s) = galaxy-? ]]; then
    module load gcc/4.9.0
    module load python/2.7.10
    module load virtualenv

fi

mkdir ${WORKSPACE}/${ENVDIR}
virtualenv --version
virtualenv -p python2.7 ${WORKSPACE}/${ENVDIR}
cd ${WORKSPACE}/${ENVDIR}/bin
if [ $? -ne 0 ]; then
    echo "Error: Failed to chdir to  ${WORKSPACE}/${ENVDIR}/bin"
    exit -1
fi

source ./activate

${WORKSPACE}/${ENVDIR}/bin/pip install --trusted-host pypi.python.org --upgrade pip
${WORKSPACE}/${ENVDIR}/bin/pip install --trusted-host pypi.python.org python-daemon
${WORKSPACE}/${ENVDIR}/bin/pip install --trusted-host pypi.python.org pyzmq


cd ${WORKSPACE}/${TOPDIR}
if [ $? -ne 0 ]; then
    echo "Error: Failed to chdir to  ${WORKSPACE}/${TOPDIR}"
    exit -1
fi

#
#
pip install --trusted-host pypi.python.org ${WORKSPACE}/${TOPDIR}

if [ $? -ne 0 ]; then
    echo "Error: installation failed"
    exit -1
fi

cd ${WORKSPACE}/${ENVDIR}/bin
deactivate
