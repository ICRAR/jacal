#!/bin/bash

# Use mssplit to split the file
docker run -it --rm  --name mssplit --mount type=bind,source=/o9000/ASKAP/dingo-data/G12_test,target=/data_in \
    --mount type=bind,source=/ssd/ASKAP/dingo-data1,target=/data_out \
    --mount type=bind,source=/ssd/ASKAP/jacal/shao_demo/scripts/shao,target=/run_dir \
    192.168.6.123:5000/jacal/jacal-run \
    \
    mssplit --config /run_dir/mssplit_parset.in
