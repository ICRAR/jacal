#!/bin/bash

# Common start
this_dir=`eval "cd \$(dirname $0); echo \$PWD; cd \$OLDPWD"`
. $this_dir/common.sh

load_common

# Make sure our node managers see our drops
export PYTHONPATH="${apps_rootdir}:$PYTHONPATH"
cd "$outdir"
mpirun python -m dlg.deploy.pawsey.start_dfms_cluster \
    -l . \
    -L $this_dir/bracewell_mvp.json \
    --part-algo mysarkar \
    -M
