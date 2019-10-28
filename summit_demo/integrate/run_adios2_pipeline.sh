#!/bin/bash

venv="$1"
outdir="$2"
apps_rootdir="$3"
nodes=$4
channels_per_node=$5
start_freq=$6
freq_step=$7
time_steps=$8
repetitions=$9
use_gpus=${10}
verbosity=${11}
telescope_model=${12}
adios2_bufsize=${13}
adios2_engine=${14}

. common.sh

banner "Arguments passed from job script"
echo venv = $venv
echo outdir = $outdir
echo apps_rootdir = $apps_rootdir
echo nodes = $nodes
echo channels_per_node = $channels_per_node
echo start_freq = $start_freq
echo freq_step = $freq_step
echo time_steps = $time_steps
echo repetitions = $repetitions
echo use_gpus = $use_gpus
echo verbosity = $verbosity
echo telescope_model = $telescope_model
echo adios2_bufsize = $adios2_bufsize
echo adios2_engine = $adios2_engine
echo "**************************************"

load_modules
if [ -n "${LSB_JOBINDEX}" ]; then
	runner="jsrun -n$(($channels_per_node * $nodes)) -a1 -c7 -g1"
else
	error "Queue mechanism not recognized, exiting now"
	exit 1
fi
echo "Using $runner to start dlg cluster using the $remote_mechanism mechanism"

export PYTHONPATH="${apps_rootdir}:$PYTHONPATH"
env > $outdir/env.txt
git rev-parse HEAD > $outdir/commit.txt

cd "$outdir"

# See run_ingest_pipeline.sh for an explanation on this
export OMP_NUM_THREADS=1

export OUTPUT=$outdir/output.ms
export VERBOSE=`if [ "$verbosity" = 2 ]; then echo 1; else echo 0; fi`
export TM=$telescope_model
export START_FREQ=$start_freq
export FREQ_STEP=$freq_step
export USE_GPUS=$use_gpus
export NUM_CHANNELS=1
export NUM_TIME_STEPS=$time_steps
export NUM_REPETITIONS=$repetitions
export CHANNELS_PER_NODE=$channels_per_node
export ADIOS2_MAX_BUF_SIZE=$adios2_bufsize
export ADIOS2_ENGINE=$adios2_engine
export ADIOS2_ALL_COLUMNS=1

$runner \
    python -m test_adios_pipeline
