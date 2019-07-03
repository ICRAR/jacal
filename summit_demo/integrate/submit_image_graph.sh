#/bin/bash

# Load common functionality
cmd="cd \$(dirname $0); echo \$PWD; cd \$OLDPWD"
this_dir=`eval "$cmd"`
. $this_dir/common.sh

function print_usage {
	cat <<EOF
$0 [opts]

General options:
 -h/-?                    Show this help and leave
 -V <venv-root>           A virtual environment to load
 -o <output-dir>          The base directory for all outputs

 Runtime options:
 -n <nodes>               Number of nodes to request, defaults to #inputs / 4
 -s <num-islands>         Number of data islands
 -i <input>               Measurement Sets i.e. "in01.ms in02.ms in03.ms"
 -d                       Direct run (no queueing system, no mpirun)"

EOF
}

function get_measurement_sets {
	inputs="$@"
	for file in $inputs; do
		# Skip current and parent directories
		bfname=`basename $file`
		if [ "$bfname" == . -o "$bname" == .. ]; then
			continue
		fi
		file=`abspath $file`
		# An actual measurement set
		if [ -f "$file/table.dat" ]; then
			files+=("$file")
		elif [ -d "$file" ]; then
			get_measurement_sets "$file/*"
		else
			warning "Ignoring $file, not a measurement set"
		fi
	done
}

# Command line parsing
venv=
outdir=`abspath .`
direct_run=no
nodes=
islands=1

while getopts "h?V:o:n:i:ds:" opt
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
		i)
			inputs="$OPTARG"
			;;
		d)
			direct_run=yes
			;;
		s)
			islands=$OPTARG
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

declare -a files
get_measurement_sets "$inputs"

if [ ${#files[@]} -eq 0 ]; then
    echo "No input"
    exit -1
else
	banner "Going to image the following Measurement Sets:"
	for file in $files; do
		echo " - $file"
	done
fi

# nodes defaults to #files/4 using ceiling division
if [ -z "$nodes" ]; then
	nodes=$(( (${#files[@]} + 4  - 1) / 4 ))
fi

# However nodes we request, we actually need 1 more to account for the DIM
if [ $islands -gt 1 ]; then
    nodes=$((${nodes} + ${islands} + 1))
else
    nodes=$((${nodes} + 1))
fi

# Turn LG "template" into actual LG for this run
sed "
# Replace num_of_copies's value in scatter component with ${#files[@]}
/.*num_of_copies.*/ {
  N
  N
  s/\"value\": \".*\"/\"value\": \"${#files[@]}\"/
}
" `abspath $this_dir/graphs/image_graph.json` > $outdir/image_lg.json


# Submit differently depending on your queueing system
if [ ${direct_run} = yes ]; then
	. $this_dir/run_image_graph.sh "$venv" "$outdir" "$apps_rootdir" yes "${files[@]}"
fi
if [ ! -z "$(command -v sbatch 2> /dev/null)" ]; then
	sbatch --ntasks-per-node=1 \
	       -o "$outdir"/image_graph.log \
	       -N $nodes \
	       -t 00:30:00 \
	       -J image_graph \
	       $this_dir/run_image_graph.sh \
	         "$venv" "$outdir" "$apps_rootdir" $islands no slurm "${files[@]}"
else
	error "Queueing system not supported, add support please"
fi
