#!/bin/bash

# Use mssplit to split the file
docker run -it --rm  --name mssplit --mount type=bind,source=/home/kevin/Work/jacal/shao_demo/data,target=/data \
    jacal-006-build-jacal \
    \
    mssplit --config /data/mssplit_parset.in
