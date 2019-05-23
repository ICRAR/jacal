#/bin/bash

load_modules() {

	if [ "$SLURM_CLUSTER_NAME" = pleiades ]; then
		module use /scratch/summit_demo/modulefiles
		module load summit_demo
		module load openmpi/default
		module load gcc/6.3.0
	elif [ "$SLURM_SUBMIT_HOST" = bracewell-login ]; then
		module use /flush1/tob020/modulefiles
		module load oskar/2.7.1-adios
		module load yandasoft/default
		module load spead2/1.10.0
	else
		echo "Unsupported system, exiting now"
		exit 1
	fi

	if [ -n "$venv" ]; then
		source $venv/bin/activate
	fi
}

get_runner() {
	if [ "$1" = slurm ]; then
		runner=srun
	elif [ "$1" = mpi ]; then
		runner=mpirun
	else
		echo "Unsupported remote mechanims: $1" 1>&2
		exit 1
	fi
	echo $runner
}

abspath() {
	p="$1"
	dirname="`dirname $p`"
	basename="`basename $p`"
	cd $dirname
	echo "$PWD/$basename"
	cd $OLDPWD
}
