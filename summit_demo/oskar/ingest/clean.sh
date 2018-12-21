#!/usr/bin/env bash

# Create an image and then deconvolve it.
# This task will work for single-field data, or for multi-field mosaics
# in both narrow and wide-field imaging modes.

function clean() {
    # niter      (1): Maximum number of clean iterations.
    # imsize_x   (2): x image size in pixels.
    # imsize_y   (3): y image size in pixels.
    # cell_x     (4): x cell size. default unit arcsec.
    # cell_y     (5): y cell size. default unit arcsec.
    # image_name (6): name of output images.
    # vis     (7..n): visibility input file(s).

    if (( "$#" < 7 )); then
        return 1;
    fi

    vis=""
    arr=("${@:7}")
    for i in "${arr[@]}"
    do
        vis+=\""$i\","
    done

    local niter="${1}";
    local imsize_x="${2}";
    local imsize_y="${3}";
    local cell_x="${4}";
    local cell_y="${5}";
    local image_name="${6}";

    local cmd="clean(vis=[${vis}],imagename=\"${image_name}\",niter=${niter},imsize=[${imsize_x},${imsize_y}],cell=['${cell_x}','${cell_y}'],weighting=\"natural\")"
    casapy --nologger --agg --nogui --nologfile -c ${cmd} > /dev/null 2>&1
    return $?
}