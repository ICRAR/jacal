#!/bin/bash

if [ $# -lt 1 ]; then
	echo "Usage: $0 <ingest_graph_logfile>"
	exit 1
fi

ms_info="`sed -n "s/.*Creating.*under \(.*\) from .*/\\1/p" "$1"`"
if [ `echo "$ms_info" | wc -l` -gt 1 ]; then
	PREFIX="`echo "$ms_info" | sed -e "N;s/^\(.*\).*\n\1.*$/\1\n\1/;D"`"
else
	PREFIX="${ms_info%0}"
fi

while IFS= read -r line; do
	read hs ms ss mss he me se mse n  <<< ${line//[-:,]/ }
	echo $n $(( ((${he#0} - ${hs#0}) * 3600 + (${me#0} - ${ms#0}) * 60 + (${se#0} - ${ss#0})) * 1000 + (${mss#0} - ${mse#0})))
done < <(grep '\(Closing measurement set\)\|\(volume is\)' "$1" | sed "s/Closing measurement/Measurement/; s|\(.*\)${PREFIX}\(.*\)|\\1\\2|" | cut -f2,37- -d\ | sort --key 2n |  sed -n 'N; s/\(.\{1,\}\) \(.\{1,\}\)\n\(.\{1,\}\) volume.*/\1 \3/; p')
