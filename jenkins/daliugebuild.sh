#!/bin/bash

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
    module load virtualenv
fi

# Make sure there is nothing in the PYTHONPATH
# which could come from somewhere else
env
mkdir ${WORKSPACE}/${ENVDIR}
virtualenv --version
virtualenv -p python2.7 ${WORKSPACE}/${ENVDIR}

source ${WORKSPACE}/${ENVDIR}/bin/activate
pip install --trusted-host pypi.python.org python-daemon pyzmq
pip install --trusted-host pypi.python.org ${WORKSPACE}/${TOPDIR}
if [ $? -ne 0 ]; then
    echo "Error: installation failed"
    exit -1
fi

deactivate
