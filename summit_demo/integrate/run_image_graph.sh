#!/bin/bash

venv="$1"
outdir="$2"
apps_rootdir="$3"
direct_run=$4
files="${@:5}"

. common.sh

if [ $direct_run != yes ]; then
	load_modules
fi

export PYTHONPATH="${apps_rootdir}:$PYTHONPATH"
cd "$outdir"

if [ $direct_run = yes ]; then
	dlg unroll-and-partition -L image_lg.json | python -m modify_image_pg -i "$files" -o $outdir | dlg submit -p 8000
	exit 0
fi

mpirun --report-bindings --bind-to core --hetero-nodes \
    python -m dlg.deploy.pawsey.start_dfms_cluster \
    -l . \
    -L image_lg.json \
    -M \
    -d \
    -v 2 \
    --pg-modifiers "modify_image_pg.modify_pg,inputs=$files,out_dir=$outdir"
