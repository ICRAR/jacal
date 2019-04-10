#/bin/bash

function load_modules {
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
