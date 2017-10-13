#!/bin/bash
RUNDIR=${WORKSPACE}/jacal/apps/askap/functests/basic

source ${RUNDIR}//setup_askap.sh

if [ $# -gt 0 ]; then
    echo "have argument"
    source ${RUNDIR}/setup_daliuge.sh $1
else
    source ${RUNDIR}/setup_daliuge.sh 
fi

sleep 5

source ${RUNDIR}/run_jacal.sh


