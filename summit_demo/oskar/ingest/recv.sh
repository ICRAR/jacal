#!/usr/bin/env bash
mkdir -p ./output/
python spead_recv.py --conf ./conf/recv.json --out ./output/summit "$@"
