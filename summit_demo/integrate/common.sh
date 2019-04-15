#/bin/bash

function load_modules {

	if [ "$SLURM_CLUSTER_NAME" = pleiades ]; then
		module use /scratch/summit_demo/modulefiles
		module load summit_demo
		module load openmpi/default
		module load gcc/6.3.0
	else
		# Bracewell; put inside an "elif" if we need
		# to add more environments
		module use /flush1/tob020/modulefiles
		module load yandasoft/default
		module load oskar/2.7.1-adios
		module load spead2/1.10.0
		module load casacore/3.0.0-adios
		module load adios/2.2.0
	fi

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
