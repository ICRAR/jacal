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
 -i <input>               Measurement Sets i.e. "in01.ms in02.ms in03.ms"

EOF
}

# Command line parsing
venv=
outdir=`abspath .`

while getopts "h?V:o:i:" opt
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
		i)
			inputs=("$OPTARG")
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

for file in $inputs;do
    files+=($file)
done

if [ ${#files[@]} -eq 0 ]; then
    echo "No input"
    exit -1
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


. $this_dir/run_image_graph.sh "$venv" "$outdir" "$apps_rootdir" "${files[@]}"

