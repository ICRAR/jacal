#!/bin/bash

docker run -d -it --name daliuge_dim --mount type=bind,source=/ssd/ASKAP/jacal,target=/ssd/ASKAP/jacal \
    --mount type=bind,source=/home/kvinsen,target=/user \
    -p 8001:8001 -p 5555:5555 -p 6666:6666 \
    192.168.6.123:5000/jacal/jacal-run  \
    \
    dlg dim -vvv -H 0.0.0.0 --ssh-pkey-path /user/.ssh/id_daliuge \
    --nodes 192.168.6.35,192.168.6.36,192.168.6.37,192.168.6.38,192.168.6.39,192.168.6.40,192.168.6.41,192.168.6.42 \
    --log-dir "/user/daliuge-dim-$(hostname -I | grep -Po '192\.168\.6\.[0-9]+')" --max-request-size 10