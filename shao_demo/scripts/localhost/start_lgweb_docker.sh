#!/bin/bash

docker run -d -it --name daliuge --mount type=bind,source=/home/kevin/Work/jacal,target=/home/kevin/Work/jacal \
    -p 8004:8004 -p 5555:5555 -p 6666:6666 \
    jacal-007-jacal-run \
    \
    dlg lgweb -t /tmp -d . -v