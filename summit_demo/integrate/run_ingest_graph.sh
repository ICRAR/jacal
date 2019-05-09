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

. common.sh

load_modules
runner="`get_runner $remote_mechanism`"
echo "Using $runner to start dlg cluster using the $remote_mechanism mechanism"

export PYTHONPATH="${apps_rootdir}:$PYTHONPATH"
env > $outdir/env

cd "$outdir"
$runner \
    python -m dlg.deploy.pawsey.start_dfms_cluster \
    -l . \
    -L lg.json \
    --part-algo mysarkar \
    --remote-mechanism $remote_mechanism \
    -d \
    -s $islands \
    -v $verbosity \
    --pg-modifiers modify_ingest_pg.modify_pg,start_freq=$start_freq,freq_step=$freq_step,channels_per_drop=$gpus_per_node
