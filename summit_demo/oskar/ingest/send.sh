#!/usr/bin/env bash

for i in {1..5};
do
   echo "Running sender: $i"
   python simple_send.py --conf ./conf/send0$i.json &
done

wait
