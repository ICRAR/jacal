#!/bin/bash

# Use mssplit to split the file
docker run -it --rm  --name mssplit --mount type=bind,source=/mnt/hidata2/dingo/aws/g12/G12_test,target=/data \
    --mount type=bind,source=//scratch/kvinsen/jacal/shao_demo/scripts/hyrmine,target=/data_in \
    jacal-006-build-jacal \
    \
    mssplit --config /data_in/mssplit_parset.in
