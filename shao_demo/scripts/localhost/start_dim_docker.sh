#!/bin/bash


docker run -d -it --name daliuge --mount type=bind,source=/home/kevin/Work/jacal,target=/home/kevin/Work/jacal \
    -p 8001:8001 -p 5555:5555 -p 6666:6666 \
    jacal-006-build-jacal \
    \
    dlg dim -vvv -H 0.0.0.0  --nodes localhost --log-dir /tmp