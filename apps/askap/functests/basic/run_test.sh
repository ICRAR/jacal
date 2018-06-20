#!/bin/bash

# Make sure we're standing alongside this script
# in order to properly execute the rest of the stuff
this=$0
if [ -h $0 ]
then
    this=$(readlink -f $0)
fi
cd "$(dirname $this)"

JACAL_LIB=../../jacal/apps/askap/libaskapsoft_dlg.so
for f in setup_askap.sh setup_daliuge.sh $JACAL_LIB; do
    if [ ! -e setup_askap.sh ]; then
        exit -1
    fi
done

source setup_askap.sh
source setup_daliuge.sh $@
sleep 5
cp $JACAL_LIB /tmp/libaskapsoft_dlg.so

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
