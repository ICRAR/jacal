#/bin/bash

# Load common functionality
cmd="cd \$(dirname $0); echo \$PWD; cd \$OLDPWD"
this_dir=`eval "$cmd"`
. $this_dir/common.sh

function print_usage {
	cat <<EOF
$0 [opts]

General options:

 -h/-?                 Show this help and leave
 -V <venv-root>        A virtual environment to load
 -o <output-dir>       The base directory for all outputs

Runtime options:
 -n <nodes>            Number of nodes to use for simulating data
 -g <gpus-per-node>    #GPUs per node to use
 -f <start-freq>       Global start frequency, in Hz. Default=210200000
 -s <freq-step>        Frequency step, in Hz. Default=4000
EOF
}

# Command line parsing
venv=
outdir=`abspath .`
nodes=1
gpus_per_node=2
start_freq=210200000
freq_step=4000

while getopts "V:o:n:g:f:s:h?" opt
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
		g)
			gpus_per_node="$OPTARG"
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
		*)
			print_usage 1>&2
			exit 1
			;;
	esac
done

logical_graph=`abspath $this_dir/graphs/ingest_graph.json`
apps_rootdir="`abspath $this_dir/../oskar/ingest`"

# Create a new output dir with our date, *that* will be the base output dir
outdir="$outdir/`date -u +%Y-%m-%dT%H-%M-%S`"
mkdir -p "$outdir"

# Whatever number of nodes we want to use for simulation, add 1 to them
# to account for the DIM node
nodes=$((${nodes} + 1))

# Submit differently depending on your queueing system
if [ ! -z "$(command -v sbatch 2> /dev/null)" ]; then
	sbatch --ntasks-per-node=1 \
	       -o "$outdir"/ingest_graph.log \
	       -N $nodes \
	       -t 00:30:00 \
	       -J ingest_graph \
	       --gres=gpu:${gpus_per_node} \
	       $this_dir/run_ingest_graph.sh \
	         "$venv" "$outdir" "$apps_rootdir" "$logical_graph" \
	         $start_freq $freq_step $gpus_per_node
else
	error "Queueing system not supported, add support please"
fi
