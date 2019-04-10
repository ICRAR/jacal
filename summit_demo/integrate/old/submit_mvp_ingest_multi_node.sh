#!/bin/bash

# Common start
cmd="cd \$(dirname $0); echo \$PWD; cd \$OLDPWD"
this_dir=`eval "$cmd"`

. $this_dir/common.sh

logical_graph=`abspath bracewell_mvp_multinode_multifile.json`
receiver_nodes=5
sender_nodes=2
gpus_per_node=2

source $this_dir/_submit_ingest_pipeline.sh
