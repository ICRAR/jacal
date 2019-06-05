#!/bin/bash

venv="$1"
outdir="$2"
apps_rootdir="$3"
start_freq=$4
freq_step=$5
gpus_per_node=$6
islands=$7
verbosity=$8
remote_mechanism=$9
pgtp_path=${10}

echo "**************************************"
echo "** Arguments passed from job script **"
echo "venv = $venv"
echo "outdir = $outdir"
echo "apps_rootdir = $apps_rootdir"
echo "start_freq = $start_freq"
echo "freq_step = $freq_step"
echo "gpus_per_node = $gpus_per_node"
echo "island = $islands"
echo "verbosity = $verbosity"
echo "remote_mechanism = $remote_mechanism"
echo "**************************************"

. common.sh

load_modules
runner="jsrun"
echo "Using $runner to start dlg cluster using the $remote_mechanism mechanism"

export PYTHONPATH="${apps_rootdir}:$PYTHONPATH"
env > $outdir/env

cd "$outdir"
if [ -z "$pgtp_path" ]
then
    graph_option="-L lg.json" 
else
    graph_option="-P $pgtp_path"
fi

$runner \
    python -m dlg.deploy.pawsey.start_dfms_cluster \
    -l . \
    $graph_option \
    --part-algo mysarkar \
    --algo-param max_cpu=1 \
    --remote-mechanism $remote_mechanism \
    -d \
    -s $islands \
    -v $verbosity \
    --pg-modifiers modify_ingest_pg.modify_pg,start_freq=$start_freq,freq_step=$freq_step,channels_per_drop=$gpus_per_node
