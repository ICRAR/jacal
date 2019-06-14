#/bin/bash

# Load common functionality
cmd="cd \$(dirname $0); echo \$PWD; cd \$OLDPWD"
this_dir=`eval "$cmd"`
. $this_dir/common.sh

print_usage() {
	cat <<EOF
$0 [opts]

General options:
 -h/-?                    Show this help and leave
 -V <venv-root>           A virtual environment to load
 -o <output-dir>          The base directory for all outputs

Runtime options:
 -n <nodes>               Number of nodes to use for simulating data, defaults to 1
 -i <num-islands>         Number of data islandsm, defaults to 1
 -c <channels-per-node>   #channels to simulate per node, defaults to 2
 -f <start-freq>          Global start frequency, in Hz. Default=210200000
 -s <freq-step>           Frequency step, in Hz. Default=4000
 -T <time-steps>          Number of time steps. Default=5
 -a                       Use the ADIOS2 Storage Manager
 -g                       Use GPUs (one per channel)
 -v <verbosity>           1=INFO (default), 2=DEBUG
 -w <walltime>            Walltime, defaults to 00:30:00
 -M                       Use queue-specific, non-MPI-based daliuge cluster startup mechanism
 -p <pgtp path>           Absolute path to the physical graph template

Runtime paths:
 -b <baseline-exclusion>  The file containing the baseline exclusion map
 -t <telescope-model>     The directory with the telescope model to use
 -S <sky-model>           The sky model to use
EOF
}

# Command line parsing
venv=/gpfs/alpine/csc303/scratch/wangj/jacal_install
outdir=`abspath .`
nodes=1
islands=1
channels_per_node=6
start_freq=210200000
freq_step=4000
time_steps=5
baseline_exclusion=
telescope_model=
sky_model=
use_adios2=0
use_gpus=0
verbosity=1
remote_mechanism=mpi
walltime=00:30
# physical graph template partition
pgtp=

while getopts "h?V:o:n:c:f:s:T:b:t:S:agv:w:i:Mp:" opt
do
	case "$opt" in
		h?)
			print_usage
			exit 0
			;;
		V)
			venv="$OPTARG"
			;;
		o)
			outdir="`abspath $OPTARG`"
			;;
		c)
			channels_per_node="$OPTARG"
			;;
		n)
			nodes="$OPTARG"
			;;
		f)
			start_freq=$OPTARG
			;;
		s)
			freq_step=$OPTARG
			;;
		T)
			time_steps=$OPTARG
			;;
		b)
			baseline_exclusion="$OPTARG"
			;;
		t)
			telescope_model="$OPTARG"
			;;
		S)
			sky_model="$OPTARG"
			;;
		a)
			use_adios2=1
			;;
		g)
			use_gpus=1
			;;
		v)
			verbosity=$OPTARG
			;;
		w)
			walltime=$OPTARG
			;;
		i)
			islands=$OPTARG
			;;
		M)
			remote_mechanism=
			;;
		p)
			pgtp="`abspath $OPTARG`"
			;;
		*)
			print_usage 1>&2
			exit 1
			;;
	esac
done

apps_rootdir="`abspath $this_dir/../oskar/ingest`"
baseline_exclusion=${baseline_exclusion:-$apps_rootdir/conf/aa2_baselines.csv}
telescope_model=${telescope_model:-$apps_rootdir/conf/aa2.tm}
sky_model=${sky_model:-$apps_rootdir/conf/eor_model_list.csv}

# Create a new output dir with our date, *that* will be the base output dir
outdir="$outdir/`date -u +%Y-%m-%dT%H-%M-%S`"
mkdir -p "$outdir"
echo "$0 $@" > $outdir/submission.log

# Turn LG "template" into actual LG for this run
sed "
# Replace filepaths to match our local filepaths
s%\"baseline_exclusion_map_path=.*\"%\"baseline_exclusion_map_path=$baseline_exclusion\"%
s%\"telescope_model_path=.*\"%\"telescope_model_path=$telescope_model\"%
s%\"sky_model_file_path=.*\"%\"sky_model_file_path=$sky_model\"%

# Replace num_of_copies's value in scatter component with $nodes
/.*num_of_copies.*/ {
  N
  N
  s/\"value\": \".*\"/\"value\": \"$nodes\"/
}

# Set whether to use ADIOS2 or not
s/\"use_adios2=.*\"/\"use_adios2=$use_adios2\"/

# Set whether to use GPUs or not
s/\"use_gpus=.*\"/\"use_gpus=$use_gpus\"/

# Number of time steps to simulate
s%\"num_time_steps=.*\"%\"num_time_steps=$time_steps\"%
" `abspath $this_dir/graphs/ingest_graph.json` > $outdir/lg.json

# Whatever number of nodes we want to use for simulation, add 1 to them
# to account for the DIM node

if [ $islands -gt 1 ]; then
    nodes=$((${nodes} + ${islands} + 1))
else
    nodes=$((${nodes} + 1))
fi

# Submit differently depending on your queueing system
if [ ! -z "$(command -v sbatch 2> /dev/null)" ]; then
	request_gpus=
	if [ $use_gpus = 1 ]; then
		request_gpus="--gres=gpu:${channels_per_node}"
	fi
	sbatch --ntasks-per-node=1 \
	       -o "$outdir"/ingest_graph.log \
	       -N $nodes \
	       -t ${walltime} \
	       -J ingest_graph \
	       ${request_gpus} \
	       $this_dir/run_ingest_graph.sh \
	         "$venv" "$outdir" "$apps_rootdir" \
	         $start_freq $freq_step $channels_per_node $islands $verbosity ${remote_mechanism:-slurm} "$pgtp"
elif [ ! -z "$(command -v bsub 2> /dev/null)" ]; then
    echo "Submitting job using bsub"
    echo "walltime = ${walltime}"
    echo "nnodes = ${nodes}"
    bsub -P csc303 -nnodes $nodes -W ${walltime} -o "$outdir"/ingest_graph.log -J ingest_graph $this_dir/run_ingest_graph.sh "$venv" "$outdir" "$apps_rootdir" $start_freq $freq_step $channels_per_node $islands $verbosity ${remote_mechanism:-lsf} ${nodes}
    echo "$venv"
    echo "$outdir"
    echo "$apps_rootdir"
    echo "$start_freq"
    echo "$freq_step"
    echo "$channels_per_node"
    echo "$islands"
    echo "$verbosity"
    echo ${remote_mechanism:-lsf}
    echo ${nodes}
else
    error "Queueing system not supported, add support please"
fi
