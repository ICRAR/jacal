#!/bin/bash

venv="$1"
outdir="$2"
apps_rootdir="$3"
files="${@:4}"

. common.sh

#load_modules

export PYTHONPATH="${apps_rootdir}:$PYTHONPATH"
cd "$outdir"

dlg unroll-and-partition -L image_lg.json | python -m modify_image_pg -i "$files" -o $outdir | dlg submit -p 8000