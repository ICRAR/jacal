#!/bin/bash

venv="$1"
outdir="$2"
apps_rootdir="$3"
islands=$4
direct_run=$5
remote_mechanism=$6
nodes=$7
files="${@:8}"

. common.sh

banner "Arguments passed from job script"
echo "venv = $venv"
echo "outdir = $outdir"
echo "apps_rootdir = $apps_rootdir"
echo "island = $islands"
echo "direct_run = $direct_run"
echo "remote_mechanism = $remote_mechanism"
echo "nodes = $nodes"
echo "files = $files"
echo "**************************************"

if [ $direct_run != yes ]; then
	load_modules
	runner="`get_runner $remote_mechanism $nodes`"
	echo "Using $runner to start dlg cluster using the $remote_mechanism mechanism"
fi

export PYTHONPATH="${apps_rootdir}:$PYTHONPATH"
env > $outdir/env.txt
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
    --algo-param max_cpu=1 \
    --remote-mechanism $remote_mechanism \
    -d \
    -s $islands \
    -v 2 \
    --pg-modifiers "modify_image_pg.modify_pg,inputs=$files,out_dir=$outdir"
