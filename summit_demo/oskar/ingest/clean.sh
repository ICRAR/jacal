#!/usr/bin/env bash

function clean() {
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