#!/bin/bash

venv="$1"
outdir="$2"
apps_rootdir="$3"
start_freq=$4
freq_step=$5
gpus_per_node=$6

. common.sh

load_modules

export PYTHONPATH="${apps_rootdir}:$PYTHONPATH"
cd "$outdir"
mpirun --report-bindings --bind-to core --hetero-nodes \
    python -m dlg.deploy.pawsey.start_dfms_cluster \
    -l . \
    -L lg.json \
    -M \
    -d \
    -v 1 \
    --pg-modifiers modify_ingest_pg.modify_pg,start_freq=$start_freq,freq_step=$freq_step,channels_per_drop=$gpus_per_node
