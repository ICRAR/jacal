#!/bin/bash

this_dir=`eval "cd \$(dirname $0); echo \$PWD; cd \$OLDPWD"`
. $this_dir/common.sh

load_common

APP_ROOT="$this_dir/../../oskar/ingest"
srun -n 1 python $APP_ROOT"/spead_recv.py" --conf $APP_ROOT"/conf/recv.json"

