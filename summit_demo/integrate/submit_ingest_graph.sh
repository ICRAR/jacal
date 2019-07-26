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
 -V <venv-root>           A virtual environment to load (defaults to $SUMMIT_VENV)
 -o <output-dir>          The base directory for all outputs

Runtime options:
 -n <nodes>               Number of nodes to use for simulating data, defaults to 1
 -i <num-islands>         Number of data islandsm, defaults to 1
 -c <channels-per-node>   #channels to simulate per node, defaults to 6
 -f <start-freq>          Global start frequency, in Hz. Default=210200000
 -s <freq-step>           Frequency step, in Hz. Default=4000
 -T <time-steps>          Number of time steps. Default=5
 -I <internal port base>  Base port for spead2 in signal drop, defaults to 12345
 -r <relay port base>     Base port for spead2 relay, defaults to 23456
 -E <error tolerance>     Error tolerance of the signal generator, as % (0-100), defaults to 0.
 -e <error tolerance>     Error tolerance of the sink, as % (0-100), defaults to 0.
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
 -m <ms-output-dir>       The output directory for MSs. An extra copy is put in <output-dir>.
EOF
}

# Command line parsing
venv=$SUMMIT_VENV
outdir=`abspath .`
nodes=1
islands=1
channels_per_node=6
start_freq=210200000
freq_step=4000
time_steps=5
internal_port=12345
relay_base_port=23456
signal_generator_error_tolerance=0
sink_error_tolerance=0
baseline_exclusion=
telescope_model=
sky_model=
use_adios2=0
use_gpus=0
verbosity=1
remote_mechanism=mpi
walltime=00:30:00
ms_outdir=
# physical graph template partition
pgtp=

while getopts "h?V:o:n:c:f:s:T:I:r:E:e:b:t:S:agv:w:i:Mp:m:" opt
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
		I)
			internal_port=$OPTARG
			;;
		r)
			relay_base_port=$OPTARG
			;;
		E)
			signal_generator_error_tolerance=$OPTARG
			;;
		e)
			sink_error_tolerance=$OPTARG
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
		m)
			ms_outdir="$OPTARG"
			;;
		*)
			print_usage 1>&2
			exit 1
			;;
	esac
done

apps_rootdir="`abspath $this_dir/../oskar/ingest`"
baseline_exclusion=${baseline_exclusion:-$apps_rootdir/conf/aa4_baselines.csv}
telescope_model=${telescope_model:-$apps_rootdir/conf/aa4.tm}
sky_model=${sky_model:-$apps_rootdir/conf/eor_model_list.csv}

# Create a new output dir with our date, *that* will be the base output dir
outdir="$outdir/`date -u +%Y-%m-%dT%H-%M-%S`"
mkdir -p "$outdir"
echo "$0 $@" > $outdir/submission.log

# When using a different output directory for MSs (most probably node-local)
# we use a different logical graph which includes an extra copying step
# to put the MSs into the global filesystem
logical_graph=ingest_graph.json
if [ -n "$ms_outdir" ]; then
	logical_graph=ingest_graph_local_ssd.json
fi

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

# Replace the MS output dirname, used by ingest_graph_local_ssd.json
/.*dirname.*/ {
  N
  N
  s%\"value\": \"ms_outdir\"%\"value\": \"$ms_outdir\"%
}

# Set whether to use ADIOS2 or not
s/\"use_adios2=.*\"/\"use_adios2=$use_adios2\"/

# Set whether to use GPUs or not
s/\"use_gpus=.*\"/\"use_gpus=$use_gpus\"/

# Number of time steps to simulate
s%\"num_time_steps=.*\"%\"num_time_steps=$time_steps\"%

# The base port used for internal spead2 communications
s%\"internal_port=.*\"%\"internal_port=$internal_port\"%

# The base port used for relaying spead2 packets from one avg to another
# This setting affets the AveragerSinkDrop; the signal generation drop is
# modified through the modify_ingest.py modifier during graph translation
s%\"stream_listen_port_start=.*\"%\"stream_listen_port_start=$relay_base_port\"%

# Error tolerances for the sink and signal generator drops
s%SIGNAL_GENERATOR_ERROR_TOLERANCE%$signal_generator_error_tolerance%
s%SINK_ERROR_TOLERANCE%$sink_error_tolerance%
" `abspath $this_dir/graphs/$logical_graph` > $outdir/lg.json

# Whatever number of nodes we want to use for simulation, add 1 to them
# to account for the DIM node

if [ $islands -gt 1 ]; then
    nodes=$((${nodes} + ${islands} + 1))
else
    nodes=$((${nodes} + 1))
fi

# Submit differently depending on your queueing system
if [ ! -z "$(command -v bsub 2> /dev/null)" ]; then
	bsub -P csc303 -nnodes $nodes \
	     -W ${walltime} \
	     -o "$outdir"/ingest_graph.log \
	     -J ingest_graph \
	     $this_dir/run_ingest_graph.sh \
	        "$venv" "$outdir" "$apps_rootdir" \
	        $start_freq $freq_step $channels_per_node \
	        $islands $verbosity ${remote_mechanism:-lsf} \
	        $nodes $relay_base_port "$pgtp"
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
	       $this_dir/run_ingest_graph.sh \
	         "$venv" "$outdir" "$apps_rootdir" \
	         $start_freq $freq_step $channels_per_node \
	         $islands $verbosity ${remote_mechanism:-slurm} \
	         $nodes $relay_base_port "$pgtp"
else
	error "Queueing system not supported, add support please"
fi
