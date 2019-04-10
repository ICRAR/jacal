#!/bin/bash

if [ $# -lt 1 ]; then
	echo "Usage: $0 <jobID1> ..."
	exit 1
fi

for job_id in $@; do
	times=`sacct -n -X -j $job_id --format Submit,Start --parsable2`
	submit=`echo $times | cut -f1 -d'|'`
	start=`echo $times | cut -f2 -d'|'`
	diff=$((`date -d $start +%s` - `date -d $submit +%s`))
	echo "Waiting time for job $job_id was $diff [s]"
done
