#!/bin/bash

docker run -d -it --name daliuge --mount type=bind,source=/ssd/ASKAP/jacal,target=/ssd/ASKAP/jacal \
    --mount type=bind,source=/home/kvinsen,target=/user \
    -p 8084:8084 \
    192.168.6.123:5000/jacal/jacal-run  \
    \
    dlg lgweb -t /user/lgweb -d . -v