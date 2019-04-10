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

Runtime paths:
 -b <baseline-exclusion>  The file containing the baseline exclusion map
 -t <telescope-model>     The directory with the telescope model to use
 -S <sky-model>           The sky model to use
EOF
}

# Command line parsing
venv=
outdir=`abspath .`
nodes=1
gpus_per_node=2
start_freq=210200000
freq_step=4000
baseline_exclusion=
telescope_model=
sky_model=

while getopts "h?V:o:n:g:f:s:b:t:S:" opt
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
		b)
			baseline_exclusion="$OPTARG"
			;;
		t)
			telescope_model="$OPTARG"
			;;
		S)
			sky_model="$OPTARG"
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

# Turn LG "template" into actual LG for this run
sed "
# Replace filepaths to match our local filepaths
s%\"baseline_exclusion_map_path=\\(.*\\)\"%\"baseline_exclusion_map_path=$baseline_exclusion\"%
s%\"telescope_model_path=\\(.*\\)\"%\"telescope_model_path=$telescope_model\"%
s%\"sky_model_file_path=\\(.*\\)\"%\"sky_model_file_path=$sky_model\"%

# Replace num_of_copies's value in scatter component with $nodes
/.*num_of_copies.*/ {
  N
  N
  s/\"value\": \".*\"/\"value\": \"$nodes\"/
}
" `abspath $this_dir/graphs/ingest_graph.json` > $outdir/lg.json

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
	         "$venv" "$outdir" "$apps_rootdir" \
	         $start_freq $freq_step $gpus_per_node
else
	error "Queueing system not supported, add support please"
fi
