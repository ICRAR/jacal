#!/bin/bash

venv="$1"
outdir="$2"
apps_rootdir="$3"
islands=$4
direct_run=$5
remote_mechanism=$6
files="${@:7}"

. common.sh

if [ $direct_run != yes ]; then
	load_modules
	runner="`get_runner $remote_mechanism`"
	echo "Using $runner to start dlg cluster using the $remote_mechanism mechanism"
fi

export PYTHONPATH="${apps_rootdir}:$PYTHONPATH"
env > $outdir/env
cd "$outdir"

if [ $direct_run = yes ]; then
	dlg unroll-and-partition -L image_lg.json | python -m modify_image_pg -i "$files" -o $outdir | dlg submit -p 8000
	exit 0
fi

$runner \
    python -m dlg.deploy.pawsey.start_dfms_cluster \
    -l . \
    -L image_lg.json \
    --part-algo mysarkar \
    --remote-mechanism $remote_mechanism \
    -d \
    -s $islands \
    -v 2 \
    --pg-modifiers "modify_image_pg.modify_pg,inputs=$files,out_dir=$outdir"
