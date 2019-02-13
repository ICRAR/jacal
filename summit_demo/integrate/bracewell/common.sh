#/bin/bash

function load_common {
	module use /flush1/tob020/modulefiles
	module load oskar/2.7.1-adios
	module load spead2/1.10.0
	module load casacore/3.0.0-adios
	module load adios/2.2.0

	if [ -n "$venv" ]; then
		source $venv/bin/activate
	fi
}

function print_usage {
	echo "$0 [-V venv-root] [-o output-dir] [-a apps_rootdir] [-h/-?]"
}

venv=$VIRTUAL_ENV
outdir=.
apps_rootdir=
while getopts "V:o:a:" opt
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
			outdir="$OPTARG"
			;;
		a)
			apps_rootdir="$OPTARG"
			;;
		*)
			exit 1
			;;
	esac
done
