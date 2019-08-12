#!/bin/bash

venv="$1"
outdir="$2"
processes_per_node="$3"
total_processes="$4"

. common.sh

banner "Arguments passed from job script"
echo "venv = $venv"
echo "outdir = $outdir"
echo "processes_per_node = $processes_per_node"
echo "total_processes = $total_processes"
echo "**************************************"
load_modules
echo "**************************************"

env > $outdir/env.txt
git rev-parse HEAD > $outdir/commit.txt
subjob_id=${SLURM_ARRAY_TASK_ID:-$LSB_JOBINDEX}
starting_process_id=$(( ($subjob_id - 1) * ($processes_per_node) + 1 ))
ending_process_id=$(( $subjob_id * $processes_per_node ))
total_processes=$(( $total_processes + 1 ))

banner "Processing visibility data"
for r in `seq $starting_process_id $ending_process_id`
do
    if [ $total_processes -gt $r ]; then
        cd "$outdir/$r"
        pwd
        jsrun -n1 -a1 -c1 cimager -c imager.ini > cimager.log &
        cd "../.."
    fi
done
echo "**************************************"
