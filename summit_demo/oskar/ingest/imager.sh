#!/usr/bin/env bash
source clean.sh

echo -n "Imaging..."
clean 500 512 512 60arcsec 60arcsec ./output/summit_cube ./output/summit.ms/
if (( $? == 0 )); then
   echo "Done"
else
    echo "Error: $?"
fi
