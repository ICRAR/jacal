#!/bin/bash

venv="$1"
outdir="$2"

. common.sh

banner "Arguments passed from job script"
echo "venv = $venv"
echo "outdir = $outdir"
echo "**************************************"

load_modules
runner="`get_runner mpi 1`"
echo "Using $runner to start cimager"

env > $outdir/env.txt
git rev-parse HEAD > $outdir/commit.txt
rank=${SLURM_ARRAY_TASK_ID:-$LSB_JOBINDEX}

cd "$outdir/$rank"

$runner cimager -c imager.ini
