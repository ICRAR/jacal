#/bin/bash

DEFAULT_NODES=1
DEFAULT_CHANNELS_PER_NODE=6
DEFAULT_START_FREQ=45991200
DEFAULT_FREQ_STEP=6400
DEFAULT_NUM_TIME_STEPS=1
DEFAULT_NUM_REPETITIONS=100
DEFAULT_WALLTIME=00:30:00
DEFAULT_TELESCOPE_MODEL=AA4
DEFAULT_ADIOS2_BUFSIZE=10Gb

# Load common functionality
cmd="cd \$(dirname $0); echo \$PWD; cd \$OLDPWD"
this_dir=`eval "$cmd"`
. $this_dir/common.sh

print_usage() {
	cat <<EOF
$0 [opts]

General options:
 -h/-?                    Show this help and leave
 -V <venv-root>           A virtual environment to load (defaults to $SUMMIT_VENV)
 -o <output-dir>          The base directory for all outputs

Runtime options:
 -n <nodes>               Number of nodes to use for simulating data, defaults to $DEFAULT_NODES
 -c <channels-per-node>   #channels to simulate per node, defaults to $DEFAULT_CHANNELS_PER_NODE
 -f <start-freq>          Global start frequency, in Hz. Default=$DEFAULT_START_FREQ
 -s <freq-step>           Frequency step, in Hz. Default=$DEFAULT_FREQ_STEP
 -T <time-steps>          Number of time steps. Default=$DEFAULT_NUM_TIME_STEPS
 -r <repetitions>         Number of times each time step is written. Default=$DEFAULT_NUM_REPETITIONS
 -g                       Use GPUs (one per channel)
 -v <verbosity>           1=INFO (default), 2=DEBUG
 -w <walltime>            Walltime, defaults to $DEFAULT_WALLTIME
 -t <telescope-model>     The telescope model to use, defaults to $DEFAULT_TELESCOPE_MODEL
 -b <adios2-bufsize>      Maximum buffer size to be used by ADIOS2, defaults to $DEFAULT_ADIOS2_BUFSIZE
EOF
}

# Command line parsing
venv=$SUMMIT_VENV
outdir=`abspath .`
nodes=$DEFAULT_NODES
channels_per_node=$DEFAULT_CHANNELS_PER_NODE
start_freq=$DEFAULT_START_FREQ
freq_step=$DEFAULT_FREQ_STEP
time_steps=$DEFAULT_NUM_TIME_STEPS
repetitions=$DEFAULT_NUM_REPETITIONS
use_gpus=0
verbosity=1
walltime=$DEFAULT_WALLTIME
telescope_model=$DEFAULT_TELESCOPE_MODEL
adios2_bufsize=$DEFAULT_ADIOS2_BUFSIZE

while getopts "h?V:o:n:c:f:s:T:r:gv:w:t:b:" opt
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
		n)
			nodes="$OPTARG"
			;;
		c)
			channels_per_node="$OPTARG"
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
		r)
			repetitions=$OPTARG
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
		t)
			telescope_model="$OPTARG"
			;;
		b)
			adios2_bufsize="$OPTARG"
			;;
		*)
			print_usage 1>&2
			exit 1
			;;
	esac
done

apps_rootdir="`abspath $this_dir/../oskar/ingest`"

# Create a new output dir with our date, *that* will be the base output dir
outdir="$outdir/`date -u +%Y-%m-%dT%H-%M-%S`"
mkdir -p "$outdir"
echo "$0 $@" > $outdir/submission.log

# Submit differently depending on your queueing system
if [ ! -z "$(command -v bsub 2> /dev/null)" ]; then
	bsub -P ast157 -nnodes $nodes \
	     -W ${walltime} \
	     -o "$outdir"/adios2_pipeline.log \
	     -J adios2_pipeline \
	     $this_dir/run_adios2_pipeline.sh \
	        "$venv" "$outdir" "$apps_rootdir" \
	        $nodes $channels_per_node $start_freq $freq_step $time_steps $repetitions \
	        $use_gpus $verbosity $telescope_model $adios2_bufsize
elif [ ! -z "$(command -v sbatch 2> /dev/null)" ]; then
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
	       -c $((${channels_per_node} + 4)) \
	       $this_dir/run_adios2_pipeline.sh \
	           "$venv" "$outdir" "$apps_rootdir" \
	           $nodes $channels_per_node $start_freq $freq_step $time_steps $repetitions \
	           $use_gpus $verbosity $telescope_model $adios2_bufsize
else
	error "Queueing system not supported, add support please"
fi
