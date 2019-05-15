#!/bin/bash
#
# OSKAR2 job submission script for parallel GPU usage on summit node
#
# Usage: summit-loop.sh
# Job Submission: bsub summit-mpmd.sh

#BSUB -P csc143
#BSUB -J oskar-mpmd
#BSUB -W 00:05
#BSUB -nnodes 1

##BSUB -o /gpfs/alpine/csc303/scratch/wangj/data/log/rialto2-142-%J-%I.log
##BSUB -e /gpfs/alpine/csc303/scratch/wangj/data/log/rialto2-142-%J-%I.err

# scenario: AA4 telescope config, 1 channel per GPU with 6 GPUs running in parallel
SCENARIO="rialto2-142"
GPU_COUNT=2
USE_GPUS="true"

let "gcount = $GPU_COUNT - 1"

# push some info to stdout showing that the job has started
echo "LSB_NODENAME: <`hostname`>"

# directory setup
APP_ROOT="/gpfs/alpine/csc303/scratch/wangj/jacal"
SKY_DIR=${APP_ROOT}/summit_demo/oskar/models
TM_DIR=${APP_ROOT}/summit_demo/oskar/ingest/conf/aa4.tm
WRK_ROOT="/gpfs/alpine/csc303/scratch/wangj/data"
LOG_DIR=${WRK_ROOT}/log
IMG_DIR=${WRK_ROOT}/img
VIS_DIR=${WRK_ROOT}/vis
mkdir -p $LOG_DIR $IMG_DIR $VIS_DIR

VISNAME=${VIS_DIR}/${SCENARIO}-${LSB_JOBID}.vis
FITSROOT=${IMG_DIR}/${SCENARIO}-${LSB_JOBID}
INTER_INI=summit_demo/oskar/ingest/conf/${SCENARIO}-sim.ini
IMAGER_INI=summit_demo/oskar/ingest/conf/${SCENARIO}-imager.ini

source ${APP_ROOT}/summit_demo/summit_bashrc

# EoR sky model partitioning test case
DOUBLE_PRECISION="false"
START_TIME_UTC="01-01-2000 20:00:00"
OBS_LENGTH="06:00:00"
NUM_TIME_STEPS=1000
START_FREQUENCY_HZ=(210000000 211000000 212000000 213000000 214000000 215000000)
NUM_CHANNELS=1
FREQUENCY_INC_HZ=1000000
POL_MODE="Full"
IMG_SIZE=512
FOV_DEG=6
CHANNEL_SNAPSHOTS="false"

# sky model
PHASE_CENTRE_RA_DEG="201"
PHASE_CENTRE_DEC_DEG="-44"
MAX_SOURCES_PER_CHUNK=50000
SKY_DIR=${SKY_DIR}/EOR
SM_NAME=("sky_eor_model_f210.12" "sky_eor_model_f211.13" "sky_eor_model_f212.16" "sky_eor_model_f213.19" "sky_eor_model_f214.24" "sky_eor_model_f215.03")
SM_FILE=()
for fidx in "${SM_NAME[@]}"; do SM_FILE+=("${SKY_DIR}/${fidx}.osm"); done

cd $APP_ROOT

for gidx in $(seq 0 $gcount) ; do

    # copy template settings files and then customize the copies
    cp $INTER_INI "${INTER_INI}.${LSB_JOBID}.${gidx}"
    cp $IMAGER_INI "${IMAGER_INI}.${LSB_JOBID}.${gidx}"

    # patch OSKAR settings to tune workload to given scenario
    oskar_sim_interferometer --set "${INTER_INI}.${LSB_JOBID}.${gidx}" simulator/double_precision $DOUBLE_PRECISION
    oskar_sim_interferometer --set "${INTER_INI}.${LSB_JOBID}.${gidx}" simulator/use_gpus $USE_GPUS
    oskar_sim_interferometer --set "${INTER_INI}.${LSB_JOBID}.${gidx}" simulator/max_sources_per_chunk $MAX_SOURCES_PER_CHUNK
    oskar_sim_interferometer --set "${INTER_INI}.${LSB_JOBID}.${gidx}" observation/phase_centre_ra_deg $PHASE_CENTRE_RA_DEG
    oskar_sim_interferometer --set "${INTER_INI}.${LSB_JOBID}.${gidx}" observation/phase_centre_dec_deg $PHASE_CENTRE_DEC_DEG
    oskar_sim_interferometer --set "${INTER_INI}.${LSB_JOBID}.${gidx}" observation/num_channels $NUM_CHANNELS
    oskar_sim_interferometer --set "${INTER_INI}.${LSB_JOBID}.${gidx}" observation/start_time_utc "$START_TIME_UTC"
    oskar_sim_interferometer --set "${INTER_INI}.${LSB_JOBID}.${gidx}" observation/length $OBS_LENGTH
    oskar_sim_interferometer --set "${INTER_INI}.${LSB_JOBID}.${gidx}" observation/num_time_steps $NUM_TIME_STEPS
    oskar_sim_interferometer --set "${INTER_INI}.${LSB_JOBID}.${gidx}" telescope/pol_mode $POL_MODE
    oskar_sim_interferometer --set "${INTER_INI}.${LSB_JOBID}.${gidx}" telescope/input_directory $TM_DIR

    # make max samples a multiple of the GPUs; 12 is a multiple of 4 (Bracewell) as well as 6 (Summit)
    oskar_sim_interferometer --set "${INTER_INI}.${LSB_JOBID}.${gidx}" interferometer/max_time_samples_per_block 12
    oskar_sim_interferometer --set "${INTER_INI}.${LSB_JOBID}.${gidx}" interferometer/oskar_vis_filename ${VISNAME}.${LSB_JOBID}.${gidx}
    oskar_sim_interferometer --set "${INTER_INI}.${LSB_JOBID}.${gidx}" simulator/cuda_device_ids 0
    oskar_sim_interferometer --set "${INTER_INI}.${LSB_JOBID}.${gidx}" observation/start_frequency_hz ${START_FREQUENCY_HZ[$gidx]}
    oskar_sim_interferometer --set "${INTER_INI}.${LSB_JOBID}.${gidx}" observation/frequency_inc_hz ${FREQUENCY_INC_HZ}
    oskar_sim_interferometer --set "${INTER_INI}.${LSB_JOBID}.${gidx}" sky/oskar_sky_model/file ${SM_FILE[$gidx]}

    # FITS image settings
    oskar_imager --set "${IMAGER_INI}.${LSB_JOBID}.${gidx}" image/double_precision $DOUBLE_PRECISION
    oskar_imager --set "${IMAGER_INI}.${LSB_JOBID}.${gidx}" image/use_gpus $USE_GPUS
    oskar_imager --set "${IMAGER_INI}.${LSB_JOBID}.${gidx}" image/fov_deg $FOV_DEG
    oskar_imager --set "${IMAGER_INI}.${LSB_JOBID}.${gidx}" image/size $IMG_SIZE
    oskar_imager --set "${IMAGER_INI}.${LSB_JOBID}.${gidx}" image/channel_snapshots $CHANNEL_SNAPSHOTS
    oskar_imager --set "${IMAGER_INI}.${LSB_JOBID}.${gidx}" image/input_vis_data ${VISNAME}.${LSB_JOBID}.${gidx}
    oskar_imager --set "${IMAGER_INI}.${LSB_JOBID}.${gidx}" image/root_path $FITSROOT.${LSB_JOBID}.${gidx}

    echo "app ${gidx}: oskar_sim_interferometer ${INTER_INI}.${LSB_JOBID}.${gidx}" >> ${LOG_DIR}/summit_simulator_erf.${LSB_JOBID}
    echo "app ${gidx}: oskar_imager ${IMAGER_INI}.${LSB_JOBID}.${gidx}" >> ${LOG_DIR}/summit_imager_erf.${LSB_JOBID}
done

echo "overlapping-rs: warn" >> ${LOG_DIR}/summit_simulator_erf.${LSB_JOBID}
echo "overlapping-rs: warn" >> ${LOG_DIR}/summit_imager_erf.${LSB_JOBID}

echo "oversubscribe_cpu: warn" >> ${LOG_DIR}/summit_simulator_erf.${LSB_JOBID}
echo "oversubscribe_cpu: warn" >> ${LOG_DIR}/summit_imager_erf.${LSB_JOBID}

echo "oversubscribe_mem: allow" >> ${LOG_DIR}/summit_simulator_erf.${LSB_JOBID}
echo "oversubscribe_mem: allow" >> ${LOG_DIR}/summit_imager_erf.${LSB_JOBID}

echo "oversubscribe_gpu: allow" >> ${LOG_DIR}/summit_simulator_erf.${LSB_JOBID}
echo "oversubscribe_gpu: allow" >> ${LOG_DIR}/summit_imager_erf.${LSB_JOBID}

echo "launch_distribution : packed" >> ${LOG_DIR}/summit_simulator_erf.${LSB_JOBID}
echo "launch_distribution : packed" >> ${LOG_DIR}/summit_imager_erf.${LSB_JOBID}

for gidx in $(seq 0 $gcount) ; do
    echo "rank: ${gidx} : {host: 1; cpu: {${gidx}}; gpu :{${gidx}} } : app ${gidx}" >> ${LOG_DIR}/summit_simulator_erf.${LSB_JOBID}
    echo "rank: ${gidx} : {host: 1; cpu: {${gidx}}; gpu :{${gidx}} } : app ${gidx}" >> ${LOG_DIR}/summit_imager_erf.${LSB_JOBID}
done

# run simulator
jsrun --erf_input ${LOG_DIR}/summit_simulator_erf.${LSB_JOBID} | sort > ${LOG_DIR}/${LSB_JOBID}.simulator.log

# create image preview
jsrun --erf_input ${LOG_DIR}/summit_imager_erf.${LSB_JOBID} | sort > ${LOG_DIR}/${LSB_JOBID}.imager.log

# show visibility volume
echo "Visibility files:"
ls -l ${VISNAME}.*

# clean up run specific settings files; runtime settings are captured in the OSKAR log
rm ${INTER_INI}.${LSB_JOBID}.? ${IMAGER_INI}.${LSB_JOBID}.?

