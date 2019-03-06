#!/bin/bash

# Common start
this_dir=`eval "cd \$(dirname $0); echo \$PWD; cd \$OLDPWD"`
. $this_dir/common.sh

load_common

APP_ROOT="$this_dir/../../oskar/ingest"
export PYTHONPATH="$APP_ROOT:$PYTHONPATH"
cd "$APP_ROOT"

echo "Sleeping for 15 seconds to make sure the AWS queue is valid"
sleep 15
mpirun --report-bindings --hetero-nodes python "$APP_ROOT/bw_send.py" --conf $APP_ROOT"/conf/send%02d.json"
