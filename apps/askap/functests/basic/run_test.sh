#!/bin/bash
RUNDIR=${WORKSPACE}/jacal/apps/askap/functests/basic
if [ -e ${RUNDIR}/setup_askap.sh ]; then
    source ${RUNDIR}/setup_askap.sh
else
    echo "Cannot find ${RUNDIR}/setup_askap.sh"
    exit -1
fi

if [ -e ${RUNDIR}/setup_daliuge.sh ]; then

    if [ $# -gt 0 ]; then

        source ${RUNDIR}/setup_daliuge.sh $1
    else
        source ${RUNDIR}/setup_daliuge.sh
    fi
else
    exit -1
fi

sleep 5

if [ -e /tmp/single.in ]; then
    rm /tmp/single.in
fi

cd $RUNDIR
cp single.in /tmp
if [ -e /tmp/single.in ]; then
    if [ -e ${RUNDIR}/run_jacal.sh ]; then
        source ${RUNDIR}/run_jacal.sh
    else 
        exit -1
    fi
else
    echo "Failed to copy parfile to /tmp"
fi
