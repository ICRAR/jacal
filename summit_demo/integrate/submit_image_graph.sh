#/bin/bash

generate_cimager_ini_file() {
	rank=$1
	input="$2"
	mkdir "$outdir"/$rank
	cat >> "$outdir"/$rank/imager.ini <<EOF
Cimager.dataset=$input
Cimager.MaxUV=6000.0
Cimager.imagetype=fits
Cimager.Images.Names=[image.fits]
Cimager.Images.shape=[512, 512]
Cimager.Images.cellsize=[20arcsec, 20arcsec]
Cimager.Images.direction=[13h24m00.00, -44.00.00.0, J2000]
Cimager.Images.restFrequency=HI
Cimager.nchanpercore=1
Cimager.usetmpfs=false
Cimager.tmpfs=/dev/shm
Cimager.barycentre=true
Cimager.solverpercore=true
Cimager.nwriters=1
Cimager.singleoutputfile=false
Cimager.gridder.snapshotimaging=false
Cimager.gridder.snapshotimaging.wtolerance=2600
Cimager.gridder.snapshotimaging.longtrack=true
Cimager.gridder.snapshotimaging.clipping=0.01
Cimager.gridder=WProject
Cimager.gridder.WProject.wmax=2600
Cimager.gridder.WProject.nwplanes=5
Cimager.gridder.WProject.oversample=4
Cimager.gridder.WProject.maxsupport=512
Cimager.gridder.WProject.variablesupport=true
Cimager.gridder.WProject.offsetsupport=true
Cimager.solver=Clean
Cimager.solver.Clean.algorithm=Basisfunction
Cimager.solver.Clean.niter=5000
Cimager.solver.Clean.gain=0.1
Cimager.solver.Clean.scales=[0, 10, 30]
Cimager.solver.Clean.verbose=false
Cimager.solver.Clean.tolerance=0.01
Cimager.solver.Clean.weightcutoff=zero
Cimager.solver.Clean.weightcutoff.clean=false
Cimager.solver.Clean.psfwidth=512
Cimager.solver.Clean.logevery=50
Cimager.threshold.minorcycle=[50%, 30mJy]
Cimager.threshold.majorcycle=18mJy
Cimager.ncycles=3
Cimager.Images.writeAtMajorCycle=false
Cimager.preconditioner.Names=[Wiener, GaussianTaper]
Cimager.preconditioner.GaussianTaper=[60arcsec, 60arcsec, 0deg]
Cimager.preconditioner.preservecf=true
Cimager.preconditioner.Wiener.robustness=0.5
Cimager.restore=true
Cimager.restore.beam=fit
Cimager.restore.beam.cutoff=0.5
Cimager.restore.beamReference=mid
EOF
}

get_output_fname() {
	if [ $daliuge_run = yes ]; then
		echo "\"$outdir\"/image_graph.log"
	elif [ $1 = slurm ]; then
		echo "\"$outdir\"/%a/cimager.log"
	else
		echo "\"$outdir\"/%I/cimager.log"
	fi
}

get_run_script() {
	if [ $daliuge_run = yes ]; then
		echo "\"$this_dir\"/run_image_graph.sh"
	else
		echo "\"$this_dir\"/run_image_graph_nodlg.sh"
	fi
}

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
 -n <nodes>               Number of nodes to request, defaults to #inputs / 4
 -s <num-islands>         Number of data islands (for daliuge-based pipeline only)
 -i <input>               Measurement Sets i.e. "in01.ms in02.ms in03.ms"
 -w <walltime>            Walltime, defaults to 00:30:00
 -d                       Direct run (no queueing system, no mpirun)"
 -D                       Use the daliuge-based imaging pipeline

EOF
}

function get_measurement_sets {
	inputs="$@"
	for file in $inputs; do
		# Skip current and parent directories
		bfname=`basename $file`
		if [ "$bfname" == . -o "$bname" == .. ]; then
			continue
		fi
		file=`abspath $file`
		# An actual measurement set
		if [ -f "$file/table.dat" ]; then
			files+=("$file")
		elif [ -d "$file" ]; then
			get_measurement_sets "$file/*"
		else
			warning "Ignoring $file, not a measurement set"
		fi
	done
}

# Command line parsing
venv=
outdir=`abspath .`
direct_run=no
daliuge_run=no
nodes=
islands=1
walltime=00:30:00

while getopts "h?V:o:n:i:dDs:w:" opt
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
		n)
			nodes="$OPTARG"
			;;
		i)
			inputs="$OPTARG"
			;;
		d)
			direct_run=yes
			;;
		D)
			daliuge_run=yes
			;;
		s)
			islands=$OPTARG
			;;
		w)
			walltime=$OPTARG
			;;
		*)
			print_usage 1>&2
			exit 1
			;;
	esac
done

if [ "$daliuge_run" = yes -a "$direct_run" = yes ]; then
	error "-d and -D cannot be given together"
fi

apps_rootdir="`abspath $this_dir/../oskar/ingest`"
# Create a new output dir with our date, *that* will be the base output dir
outdir="$outdir/`date -u +%Y-%m-%dT%H-%M-%S`"
mkdir -p "$outdir"
echo "$0 $@" > $outdir/submission.log

declare -a files
get_measurement_sets "$inputs"

if [ ${#files[@]} -eq 0 ]; then
	error "No input given, use -i"
else
	banner "Going to image the following Measurement Sets:"
	for file in "${files[@]}"; do
		echo " - $file"
	done
fi
n_files=${#files[@]}

# nodes defaults to #files/4 using ceiling division
if [ -z "$nodes" ]; then
	nodes=$(( ($n_files + 4  - 1) / 4 ))
fi
# We need one node per imager at the most; if more were given
# then reduce the amount
if [ $nodes -gt $n_files ]; then
	warning "$nodes nodes requested, but only $n_files need imaging; reducing nodes to $n_files"
	nodes=$n_files
fi

# Preparing things for specific running backends
# In the case of DALiuGE we need to adjust the number of nodes and prepare the LG
# In the case of no-DALiuGE we generate the .ini files for cimager
if [ "$daliuge_run" = yes ]; then
	# However nodes we request, we actually need more to account for the DIMs/MM
	if [ $islands -gt 1 ]; then
	    nodes=$((${nodes} + ${islands} + 1))
	else
	    nodes=$((${nodes} + 1))
	fi

	# Turn LG "template" into actual LG for this run
	sed "
# Replace num_of_copies's value in scatter component with $n_files
/.*num_of_copies.*/ {
  N
  N
  s/\"value\": \".*\"/\"value\": \"${n_files}\"/
}" `abspath $this_dir/graphs/image_graph.json` > $outdir/image_lg.json
else
	rank=0
	for file in "${files[@]}"; do
		generate_cimager_ini_file $rank "$file"
		let "rank = rank + 1"
	done
fi

# Submit differently depending on your queueing system
if [ ${direct_run} = yes ]; then
	. $this_dir/run_image_graph.sh "$venv" "$outdir" "$apps_rootdir" yes "${files[@]}"
	return
fi

# Prepare submission command
if [ ! -z "$(command -v bsub 2> /dev/null)" ]; then
	cmd="bsub -P csc303 -nnodes $nodes -W ${walltime}"
	cmd+=" -o `get_output_fname lfs`"
	job_name="image_graph"
	if [ $daliuge_run = no ]; then
		job_name+="[0-$(($n_files - 1))]"
	fi
	cmd+=" -J ${job_name}"
	dlg_remote=lfs
elif [ ! -z "$(command -v sbatch 2> /dev/null)" ]; then
	cmd="sbatch --ntasks-per-node=1 -N $nodes -t ${walltime} -J image_graph"
	cmd+=" -o `get_output_fname slurm`"
	if [ $daliuge_run = no ]; then
		cmd+=" --array 0-$(($n_files - 1))"
	fi
	dlg_remote=slurm
else
	error "Queueing system not supported, add support please"
fi

# Finish the submission command with the actual run script execution specification
cmd+=" `get_run_script` \"$venv\" \"$outdir\""
if [ $daliuge_run = yes ]; then
	cmd+=" \"$apps_rootdir\" $islands no $dlg_remote $nodes \"${files[@]}\""
fi

echo "$cmd" > "$outdir"/submission_command.txt
echo "Submitting with command: $cmd"
eval $cmd
