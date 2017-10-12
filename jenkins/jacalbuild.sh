#!/bin/bash -l

if [ $# -gt 0 ]; then
    TOPDIR=$1
else
    TOPDIR=${WORKSPACE}/jacal
    ENVDIR=${WORKSPACE}/daliuge_env
    ASKAP_ROOT=${WORKSPACE}/../rialto_askap_build_galaxy/askapsoft
fi

# we assume daliuge is built via its build script
# we need to source the virtual environment
# test are we on galaxy

if [[ $(hostname -s) = galaxy-? ]]; then
    module load virtualenv
fi


cd ${ENVDIR}/bin
if [ $? -ne 0 ]; then
    echo "Error: Failed to chdir to  ${ENVDIR}/bin"
    exit 1
fi

source ./activate


#
#
#v
#
#
cd ${TOPDIR}
if [ $? -ne 0 ]; then
    echo "Error: Failed to chdir to  ${WORKSPACE}/${TOPDIR}"
    exit 1
fi

make ASKAP_ROOT=${ASKAP_ROOT}

if [ $? -ne 0 ]; then
    echo "Error: make failed"
    exit 1
fi

deactivate
