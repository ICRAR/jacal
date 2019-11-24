#!/bin/bash

# Use mssplit to split the file
docker run -it --rm  --name split_ms --mount type=bind,source=/o9000/ASKAP/dingo-data/G12_test,target=/data_in \
    --mount type=bind,source=/ssd/ASKAP/dingo-data,target=/data_out \
    casa-007 \
    \
    /bin/bash
