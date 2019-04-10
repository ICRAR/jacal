#!/bin/bash

# Common start
cmd="cd \$(dirname $0); echo \$PWD; cd \$OLDPWD"
this_dir=`eval "$cmd"`

. $this_dir/common.sh

logical_graph=`abspath bracewell_mvp.json`
receiver_nodes=2
sender_nodes=1
gpus_per_node=2

. _submit_ingest_pipeline.sh
