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
        elif [ -n "$DUGEO_SOFTWARE" ]; then
		module use /p8/mcc_uwaicrar/sw/modulefiles
		module add OSKAR/2.7.1-summit
		module add daliuge
		module rm Nemo
		module add openmpi/4.0.3-mlnx intel-rt
	else
		echo "Unsupported system, exiting now"
		exit 1
	fi

	if [ -n "$venv" ]; then
		echo "Activating $venv"
		source $venv/bin/activate
	fi
}

summit_runner() {
	nodes=$1
	shift
	nodes_per_world=6
	worlds=`ceil_div $nodes $nodes_per_world`
	echo "Launching $worlds worlds with maximum $nodes_per_world nodes each"

	# Adjust our limits to the maximum known
	ulimit -u 8192

	# Collect IPs first
	ips="`jsrun -n$nodes -c42 -bpacked:42 -a1 python -mdlg.deploy.pawsey.start_dfms_cluster --collect-interfaces -i 1`"
	export DALIUGE_CLUSTER_IPS="$ips"

	start=`date +%s`
	for i in `eval echo {1..$worlds}`; do
		_nodes=$nodes_per_world
		if [ $(($i * $nodes_per_world)) -gt $nodes ]; then
			_nodes=$(($nodes_per_world - $i * $nodes_per_world + $nodes))
		fi
		echo "Launching world with $_nodes nodes"
		jsrun -n $_nodes -a1 -g6 -c42 -bpacked:42 "$@" &
	done
	end=`date +%s`
	echo "All processes launched in $(($end - $start)) [s], waiting now"

	start=`date +%s`
	wait
	end=`date +%s`
	echo "Finished in $(($end - $start)) [s]"
}

get_runner() {
	# $1 is the remote_mechanism, $2 is the #nodes allocated
	if [ "${LMOD_SYSTEM_NAME}" == "summit" -a "$1" != mpi ]; then
		runner="summit_runner $2"
	elif [ "${LMOD_SYSTEM_NAME}" == "summit" ]; then
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
