#/bin/bash

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
	else
		echo "Unsupported system, exiting now"
		exit 1
	fi

    if [ "${LMOD_SYSTEM_NAME}" == "summit" ]; then
        module load gcc/6.4.0
        module load cmake
        module load cuda
        module load netlib-lapack
        module load python
        module load py-pip
        module load py-setuptools
        module load boost
        module load fftw
        module load gsl
        alias gcc='/sw/summit/gcc/6.4.0/bin/gcc'
        alias g++='/sw/summit/gcc/6.4.0/bin/g++'
        alias gfortran='/sw/summit/gcc/6.4.0/bin/gfortran'
        export CC=/sw/summit/gcc/6.4.0/bin/gcc
        export CXX=/sw/summit/gcc/6.4.0/bin/g++
        export FC=/sw/summit/gcc/6.4.0/bin/gfortran
        export PATH=/gpfs/alpine/csc303/scratch/wangj/jacal_dep/bin:$PATH
        export CPATH=/gpfs/alpine/csc303/scratch/wangj/jacal_dep/include:$CPATH
        export LIBRARY_PATH=/gpfs/alpine/csc303/scratch/wangj/jacal_dep/lib:/gpfs/alpine/csc303/scratch/wangj/jacal_dep/lib64:$LIBRARY_PATH
        export LD_LIBRARY_PATH=/gpfs/alpine/csc303/scratch/wangj/jacal_dep/lib:/gpfs/alpine/csc303/scratch/wangj/jacal_dep/lib64:$LD_LIBRARY_PATH
        source /gpfs/alpine/csc303/scratch/wangj/jacal_dep/bin/activate
    fi

	if [ -n "$venv" ]; then
		source $venv/bin/activate
	fi
}

get_runner() {
    if [ "$1" = slurm ]; then
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
