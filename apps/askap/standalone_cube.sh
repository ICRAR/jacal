#!/usr/bin/env bash
source activate daliuge
. ~/scripts/askap_setup.sh
ulimit -s 2048

export LD_LIBRARY_PATH=.:${LD_LIBRARY_PATH}
./standalone_cube ./test_cube.in
