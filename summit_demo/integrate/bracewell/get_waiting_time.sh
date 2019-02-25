#!/bin/bash

if [ $# -lt 1 ]; then
	echo "Usage: $0 <jobID>"
	exit 1
fi

times=`sacct -n -X -j $1 --format Submit,Start --parsable2`
submit=`echo $times | cut -f1 -d'|'`
start=`echo $times | cut -f2 -d'|'`
diff=$((`date -d $start +%s` - `date -d $submit +%s`))
echo "Waiting time was $diff [s]"
