#!/bin/bash

venv="$1"
outdir="$2"
apps_rootdir="$3"
logical_graph="$4"
start_freq=$5
freq_step=$6
gpus_per_node=$7

. common.sh

load_modules

export PYTHONPATH="${apps_rootdir}:$PYTHONPATH"
cd "$outdir"
mpirun --report-bindings --bind-to core --hetero-nodes \
    python -m dlg.deploy.pawsey.start_dfms_cluster \
    -l . \
    -L $logical_graph \
    -M \
    -d \
    --pg-modifiers modify_ingest_pg.modify_pg,start_freq=$start_freq,freq_step=$freq_step,channels_per_drop=$gpus_per_node
