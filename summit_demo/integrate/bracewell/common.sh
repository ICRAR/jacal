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

function abspath {
	p="$1"
	dirname="`dirname $p`"
	basename="`basename $p`"
	cd $dirname
	echo "$PWD/$basename"
	cd $OLDPWD
}

function print_usage {
	echo "$0 -g logical-graph [-V venv-root] [-o output-dir] [-a apps_rootdir] [-h/-?]"
}

venv=$VIRTUAL_ENV
outdir=`abspath .`
logical_graph=
apps_rootdir=
gpus_per_node=2
sender_nodes=1
receiver_nodes=3

while getopts "V:o:a:g:G:S:r:" opt
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
		a)
			apps_rootdir="`abspath $OPTARG`"
			;;
		g)
			logical_graph="`abspath $OPTARG`"
			;;
		G)
			gpus_per_node="$OPTARG"
			;;
		S)
			sender_nodes="$OPTARG"
			;;
		r)
			receiver_nodes="$OPTARG"
			;;
		*)
			exit 1
			;;
	esac
done
