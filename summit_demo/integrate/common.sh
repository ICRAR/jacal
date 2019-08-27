#/bin/bash

banner() {
	msg="** $@ **"
	echo "$msg" | sed -n '{h; x; s/./*/gp; x; h; p; x; s/./*/gp}';
}

error() {
	echo "error: $@" 1>&2
}

warning() {
	echo "warning: $@" 1>&2
}

try() {
	"$@"
	status=$?
	if [ $status -ne 0 ]; then
		error "Command exited with status $status, exiting now: $@"
		exit 1
	fi
}

ceil_div() {
	echo $(( ($1 + $2 - 1) / $2 ))
}

load_modules() {

	if [ "$SLURM_CLUSTER_NAME" = pleiades ]; then
		module use /scratch/summit_demo/modulefiles
		module load summit_demo
		module load openmpi/default
		module load gcc/6.3.0
	elif [ "$SLURM_SUBMIT_HOST" = bracewell-login ]; then
		module use /flush1/tob020/modulefiles
		module load summit_demo/default
    elif [ "${LMOD_SYSTEM_NAME}" == "summit" ]; then
		source ../summit_bashrc
	else
		echo "Unsupported system, exiting now"
		exit 1
	fi

	if [ -n "$venv" ]; then
		echo "Activating $venv"
		source $venv/bin/activate
	fi
}

get_runner() {
	# $1 is the remote_mechanism, $2 is the #nodes allocated
	if [ "${LMOD_SYSTEM_NAME}" == "summit" ]; then
		runner="jsrun -n$2 -a1 -g6 -c42 -bpacked:42"
	elif [ "$1" = slurm ]; then
		runner=srun
	elif [ "$1" = lsf ]; then
		runner=jsrun
	elif [ "$1" = mpi ]; then
		runner=mpirun
	else
		echo "Unsupported remote mechanims: $1" 1>&2
		exit 1
	fi
	echo $runner
}

ifconfig_usage() {
	if [ "${LMOD_SYSTEM_NAME}" == "summit" ]; then
		echo --use-ifconfig
	fi
}

get_interface_index() {
	if [ "${LMOD_SYSTEM_NAME}" == "summit" ]; then
		echo 1
	else
		echo 0
	fi
}

abspath() {
	p="$1"
	dirname="`dirname $p`"
	basename="`basename $p`"
	cd $dirname
	echo "$PWD/$basename"
	cd $OLDPWD
}
