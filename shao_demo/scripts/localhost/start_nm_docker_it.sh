#!/bin/bash

docker run -it --rm  --name daliuge_nms --mount type=bind,source=/home/kevin/Work/jacal,target=/home/kevin/Work/jacal \
    -p 8000:8000 -p 5555:5555 -p 6666:6666 \
    jacal-006-build-jacal \
    \
    /bin/bash -c 'cd /home/kevin/Work/jacal/shao_demo/data && dlg nm -vvv --dlg-path=/tmp -H 0.0.0.0 --log-dir /tmp --dlg-path=/home/kevin/Work/jacal/shao_demo/daliuge'
