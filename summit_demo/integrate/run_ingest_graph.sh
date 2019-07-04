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
nodes=${10}
relay_base_port=${11}
pgtp_path=${12}

. common.sh

banner "Arguments passed from job script"
echo "venv = $venv"
echo "outdir = $outdir"
echo "apps_rootdir = $apps_rootdir"
echo "start_freq = $start_freq"
echo "freq_step = $freq_step"
echo "gpus_per_node = $gpus_per_node"
echo "island = $islands"
echo "verbosity = $verbosity"
echo "remote_mechanism = $remote_mechanism"
echo "nodes = $nodes"
echo "relay_base_port = $relay_base_port"
echo "pgtp_path = $pgtp_path"
echo "**************************************"

load_modules
runner="`get_runner $remote_mechanism $nodes`"
echo "Using $runner to start dlg cluster using the $remote_mechanism mechanism"

export PYTHONPATH="${apps_rootdir}:$PYTHONPATH"
env > $outdir/env.txt

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
    --pg-modifiers modify_ingest_pg.modify_pg,start_freq=$start_freq,freq_step=$freq_step,channels_per_drop=$gpus_per_node,relay_base_port=$relay_base_port
