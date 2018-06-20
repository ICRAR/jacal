#!/bin/bash

# Make sure we're standing alongside this script
# in order to properly execute the rest of the stuff
this=$0
if [ -h $0 ]
then
	this=$(readlink -f $0)
fi
cd "$(dirname $this)"

if [ -e setup_askap.sh ]; then
    source setup_askap.sh
else
    echo "Cannot find setup_askap.sh"
    exit -1
fi

if [ -e setup_daliuge.sh ]; then

    if [ $# -gt 0 ]; then

        source setup_daliuge.sh $1
    else
        source setup_daliuge.sh
    fi
else
    exit -1
fi

sleep 5

JACAL_LIB=../../jacal/apps/askap/libaskapsoft_dlg.so
if [ -e $JACAL_LIB ]; then
  cp $JACAL_LIB /tmp/libaskapsoft_dlg.so
else
  echo "$JACAL_LIB not found"
  exit -1
fi

if [ -e /tmp/single.in ]; then
    rm /tmp/single.in
fi


cp single.in /tmp
if [ -e /tmp/single.in ]; then
    if [ -e run_jacal.sh ]; then
        source run_jacal.sh
    else
#        exit -1
    fi
else
    echo "Failed to copy parfile to /tmp"
fi
