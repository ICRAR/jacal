#!/usr/bin/env bash
echo -n "Imaging..."
./clean.sh 500 512 512 60arcsec 60arcsec ./output/summit_cube ./output/summit.ms/
if (( $? == 0 )); then
   echo "Done"
else
    echo "Error: $?"
fi
