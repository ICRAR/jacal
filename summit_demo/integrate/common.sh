#/bin/bash

banner() {
	msg="** $@ **"
	echo "$msg" | sed -n '{h; x; s/./*/gp; x; h; p; x; s/./*/gp}';
}

error() {
	echo "$@" 1>&2
}

try() {
	"$@"
	status=$?
	if [ $status -ne 0 ]; then
		error "Command exited with status $status, exiting now: $@"
		exit 1
	fi
}

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
    elif [ "${LMOD_SYSTEM_NAME}" == "summit" ]; then
		module load gcc/6.4.0
		module load cmake
		module load cuda
		module load netlib-lapack
		module load boost
		module load fftw
		module load gsl
		alias gcc='/sw/summit/gcc/6.4.0/bin/gcc'
		alias g++='/sw/summit/gcc/6.4.0/bin/g++'
		alias gfortran='/sw/summit/gcc/6.4.0/bin/gfortran'
		export CC=/sw/summit/gcc/6.4.0/bin/gcc
		export CXX=/sw/summit/gcc/6.4.0/bin/g++
		export FC=/sw/summit/gcc/6.4.0/bin/gfortran
		export PATH=/gpfs/alpine/csc303/scratch/wangj/jacal_install/bin:$PATH
		export CPATH=/gpfs/alpine/csc303/scratch/wangj/jacal_install/include:$CPATH
		export LIBRARY_PATH=/gpfs/alpine/csc303/scratch/wangj/jacal_install/lib:/gpfs/alpine/csc303/scratch/wangj/jacal_install/lib64:$LIBRARY_PATH
		export LD_LIBRARY_PATH=/gpfs/alpine/csc303/scratch/wangj/jacal_install/lib:/gpfs/alpine/csc303/scratch/wangj/jacal_install/lib64:$LD_LIBRARY_PATH
	else
		echo "Unsupported system, exiting now"
		exit 1
	fi

	if [ -n "$venv" ]; then
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

abspath() {
	p="$1"
	dirname="`dirname $p`"
	basename="`basename $p`"
	cd $dirname
	echo "$PWD/$basename"
	cd $OLDPWD
}
