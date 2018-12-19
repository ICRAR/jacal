#!/usr/bin/env bash

for i in {1..5};
do
   echo "Running sender: $i"
   python spead_send.py ./conf/send0$i.json ./conf/eor0$i.ini &
done

wait
