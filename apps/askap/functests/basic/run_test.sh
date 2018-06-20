#!/bin/bash

# Make sure we're standing alongside this script
# in order to properly execute the rest of the stuff
this=$0
if [ -h $0 ]
then
    this=$(readlink -f $0)
fi
cd "$(dirname $this)"

JACAL_LIB=../../libaskapsoft_dlg.so
for f in setup_askap.sh setup_daliuge.sh $JACAL_LIB; do
    if [ ! -e ${f} ]; then
        echo "${f} not found, cannot continue" 1>&2
        exit -1
    fi
done

source setup_askap.sh
unset PYTHONPATH
source setup_daliuge.sh $@
cp $JACAL_LIB /tmp/libaskapsoft_dlg.so
cp single.in /tmp
sleep 5

if [ ! -e /tmp/single.in ]; then
    echo "Failed to copy parfile to /tmp"
	 exit -1
fi

echo "Starting basic test"
dlg unroll-and-partition -L ./basic_image.json | dlg map -N localhost,localhost -i 1 | dlg submit -H localhost -p 8001
sleep 20
echo "Finishing test now"
killall dlg
wait
