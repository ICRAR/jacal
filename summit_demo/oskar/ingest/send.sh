#!/usr/bin/env bash

for i in {1..6};
do
   echo "Running sender: $i"
   python spead_send.py ./conf/send0$i.json ./conf/aa0$i.ini &
done

