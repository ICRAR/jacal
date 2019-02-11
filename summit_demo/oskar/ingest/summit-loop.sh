#!/bin/bash
# 
# OSKAR2 job submission script for parallel GPU usage on summit node
#
# Usage: summit-loop.sh
# Job Submission: jsrun -n1 -a6 -g1 summit-loop.sh

#BSUB -P csc303
#BSUB -J rialto2-142
#BSUB -W 00:05
#BSUB -nnodes 1
!!#BSUB --stdio_stdout ...
!!#BSUB --stdio_stderr ...


# scenario: AA4 telescope config, 1 channel per GPU with 6 GPUs running in parallel
SCENARIO="rialto2-142"
GPU_COUNT=6
USE_GPUS="true"
let "uidx = $GPU_COUNT - 1"

# push some info to stdout showing that the job has started
echo "SLURMD_NODENAME: <`hostname`>"
echo "SLURM_ARRAY_TASK_ID: <${LSB_JOBINDEX}>"
echo "CUDA_VISIBLE_DEVICES: <${CUDA_VISIBLE_DEVICES}>"
#echo "all SLURM_* variables:"
#env | grep -i slurm[_d]

idx=$LSB_JOBINDEX

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

# EoR sky model partitioning test case
DOUBLE_PRECISION="false"
START_TIME_UTC="01-01-2000 20:00:00"
OBS_LENGTH="06:00:00"
NUM_TIME_STEPS=1000
START_FREQUENCY_HZ=(210000000 211000000 212000000 213000000 214000000 215000000)
NUM_CHANNELS=1
FREQUENCY_INC_HZ=1000000
#SM_NAME=$SCENARIO
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

for idx in $(seq 0 $uidx) ; do

	# copy template settings files and then customize the copies
	cp $INTER_INI "${INTER_INI}.${idx}"
	cp $IMAGER_INI "${IMAGER_INI}.${idx}"

	# patch OSKAR settings to tune workload to given scenario
	oskar_sim_interferometer --set "${INTER_INI}.${idx}" simulator/double_precision $DOUBLE_PRECISION
	oskar_sim_interferometer --set "${INTER_INI}.${idx}" simulator/use_gpus $USE_GPUS
	oskar_sim_interferometer --set "${INTER_INI}.${idx}" simulator/max_sources_per_chunk $MAX_SOURCES_PER_CHUNK

	oskar_sim_interferometer --set "${INTER_INI}.${idx}" observation/phase_centre_ra_deg $PHASE_CENTRE_RA_DEG
	oskar_sim_interferometer --set "${INTER_INI}.${idx}" observation/phase_centre_dec_deg $PHASE_CENTRE_DEC_DEG

	oskar_sim_interferometer --set "${INTER_INI}.${idx}" observation/num_channels $NUM_CHANNELS

	oskar_sim_interferometer --set "${INTER_INI}.${idx}" observation/start_time_utc "$START_TIME_UTC"
	oskar_sim_interferometer --set "${INTER_INI}.${idx}" observation/length $OBS_LENGTH
	oskar_sim_interferometer --set "${INTER_INI}.${idx}" observation/num_time_steps $NUM_TIME_STEPS

	oskar_sim_interferometer --set "${INTER_INI}.${idx}" telescope/pol_mode $POL_MODE
	oskar_sim_interferometer --set "${INTER_INI}.${idx}" telescope/input_directory $TM_DIR

    # make max samples a multiple of the GPUs; 12 is a multiple of 4 (Bracewell) as well as 6 (Summit)
    oskar_sim_interferometer --set "${INTER_INI}.${idx}" interferometer/max_time_samples_per_block 12
	oskar_sim_interferometer --set "${INTER_INI}.${idx}" interferometer/oskar_vis_filename "${VISNAME}.${idx}"

	oskar_sim_interferometer --set "${INTER_INI}.${idx}" simulator/cuda_device_ids $idx
	oskar_sim_interferometer --set "${INTER_INI}.${idx}" observation/start_frequency_hz ${START_FREQUENCY_HZ[$idx]}
	oskar_sim_interferometer --set "${INTER_INI}.${idx}" observation/frequency_inc_hz ${FREQUENCY_INC_HZ}
	oskar_sim_interferometer --set "${INTER_INI}.${idx}" sky/oskar_sky_model/file ${SM_FILE[$idx]}

	# FITS image settings
	oskar_imager --set "${IMAGER_INI}.${idx}" image/double_precision $DOUBLE_PRECISION
	oskar_imager --set "${IMAGER_INI}.${idx}" image/use_gpus $USE_GPUS
	oskar_imager --set "${IMAGER_INI}.${idx}" image/fov_deg $FOV_DEG
	oskar_imager --set "${IMAGER_INI}.${idx}" image/size $IMG_SIZE
	oskar_imager --set "${IMAGER_INI}.${idx}" image/channel_snapshots $CHANNEL_SNAPSHOTS
	oskar_imager --set "${IMAGER_INI}.${idx}" image/input_vis_data "${VISNAME}.${idx}"
	oskar_imager --set "${IMAGER_INI}.${idx}" image/root_path "$FITSROOT.${idx}"

	# run simulator
!!#	jsrun -n1 -a1 -g1 oskar_sim_interferometer "${INTER_INI}.${idx}" &
	oskar_sim_interferometer "${INTER_INI}.${idx}" &
done


# wait for OSKAR instances to terminate
wait

# create image preview
for idx in $(seq 0 $uidx) ; do
!!#	jsrun -n1 -a1 -g1 oskar_imager "${IMAGER_INI}.${idx}"
	oskar_imager "${IMAGER_INI}.${idx}"
done


# show visibility volume
echo "Visibility files:"
ls -l ${VISNAME}.*

# clean up run specific settings files; runtime settings are captured in the OSKAR log
rm ${INTER_INI}.? ${IMAGER_INI}.?

