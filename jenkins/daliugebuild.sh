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
if [[ $(hostname -s) = galaxy-? ]]; then
    module load gcc/4.9.0
    module load python/2.7.10
    module load virtualenv

fi

mkdir ${WORKSPACE}/${ENVDIR}
virtualenv --version
virtualenv -p python2.7 ${WORKSPACE}/${ENVDIR}

source ${WORKSPACE}/${ENVDIR}/bin/activate
pip install --trusted-host pypi.python.org --upgrade pip wheel
pip install --trusted-host pypi.python.org python-daemon pyzmq
pip install --trusted-host pypi.python.org ${WORKSPACE}/${TOPDIR}
if [ $? -ne 0 ]; then
    echo "Error: installation failed"
    exit -1
fi

deactivate
