#!/bin/bash

cmd="cd \$(dirname $0); echo \$PWD; cd \$OLDPWD"
this_dir=`eval "$cmd"`

if [ $# -lt 1 ]; then
	echo "Usage: $0 <ingest_output_directory> ..."
	exit 1
fi

for ingest_outdir in "$@"; do
	test -d "$ingest_outdir/analysis" || mkdir "$ingest_outdir/analysis"
	oldpwd="$PWD"
	cd "$ingest_outdir/analysis"
	MPLBACKEND=${MPLBACKEND:-cairo} python "$this_dir"/heatmap.py ..
	echo "Produced outputs under $ingest_outdir/analysis"
	cd "$oldpwd"
done
