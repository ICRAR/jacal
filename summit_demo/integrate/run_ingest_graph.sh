#!/bin/bash

venv="$1"
outdir="$2"
apps_rootdir="$3"
direct_run="$4"
start_freq=$5
freq_step=$6
gpus_per_node=$7
islands=$8
verbosity=$9
remote_mechanism=$10
nodes=${11}
relay_base_port=${12}
pgtp_path=${13}

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
git rev-parse HEAD > $outdir/commit.txt

cd "$outdir"
if [ -z "$pgtp_path" ]
then
    graph_option="-L lg.json"
else
    graph_option="-P $pgtp_path"
fi

# In the case of the ingest pipeline, having a high CPU count
# is actually detrimental to the OSKAR instances, which slow
# down heavily in high-CPU environments during its sky setup
# OpenMP routines. Let's thus hardcode OMP_NUM_THREADS to 1
# to get acceptable runtimes.
export OMP_NUM_THREADS=1

# TODO: Just a copy from run_image_graph.sh, needs fixing
if [ $direct_run = yes ]; then
	dlg unroll-and-partition $graph_option | python -m modify_image_pg start_freq=$start_freq freq_step=$freq_step channels_per_drop=$gpus_per_node relay_base_port=$relay_base_port | dlg submit -p 8000
	exit 0
fi

$runner \
    python -m dlg.deploy.pawsey.start_dfms_cluster \
    -l . \
    $graph_option \
    --part-algo mysarkar \
    --algo-param max_cpu=1 \
    --remote-mechanism $remote_mechanism \
    --interface `get_interface_index` \
    -d \
    -s $islands \
    -v $verbosity \
    --pg-modifiers modify_ingest_pg.modify_pg,start_freq=$start_freq,freq_step=$freq_step,channels_per_drop=$gpus_per_node,relay_base_port=$relay_base_port
