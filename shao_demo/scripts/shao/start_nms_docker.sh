#!/bin/bash

docker run -d -it --name daliuge_dim --mount type=bind,source=/ssd/ASKAP/jacal,target=/ssd/ASKAP/jacal \
    --mount type=bind,source=/home/kvinsen,target=/home/user \
    -p 8000:8000 -p 5555:5555 -p 6666:6666 \
    192.168.6.123:5000/jacal/jacal-run  \
    \
    dlg nm -vvv -H 0.0.0.0 --log-dir "/home/user/daliuge-nm-$(hostname -I | grep -Po '192\.168\.6\.[0-9]+')" \
    --max-request-size 10
