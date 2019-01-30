#!/bin/bash
# 
# job array submission script
#
# Usage: rialto2-20 [RIALTO2-20]
#
# Markus Dolensky, ICRAR, 2019-01-24
#

# SLURMify
#SBATCH --job-name=rialto2-20
#SBATCH --time=05:00
#SBATCH --nodes=2
#SBATCH --ntasks-per-node=4
#SBATCH --array=0-7
#SBATCH --gres=gpu:4
#SBATCH --mem=30g
#SBATCH --mail-type=ALL
#SBATCH --mail-user=markus.dolensky@uwa.edu.au
#SBATCH --output=/flush1/dol040/oskar/log/farmoskar-mjob%A-tid%a.log
#SBATCH --error=/flush1/dol040/oskar/log/farmoskar-mjob%A-tid%a.err

# enable OSKAR; Rodrigo's /modulefiles activates casacore among others 
export MODULEPATH=$MODULEPATH:/flush1/tob020/modulefiles:/flush1/dol040/modulefiles
module load oskar/2.7.1
# scenario of jira ticket RIALTO2-8 requires bugfixed local installation of OSKAR v2.7.1-dev
module swap intel-cc/16.0.4.258 intel-mkl/2017.2.174
module load cuda casacore/2.0.3

# epa-64k | aa1-64k | aa2-64k | aa3-64k | aa4-64k | epa-6h | aa1-6h | aa2-6h | aa3-6h | aa4-6h | aa4-1c | RIALTO2-8 | RIALTO2-20
SCENARIO=${1:-"RIALTO2-20"}

GPU_COUNT=4
USE_GPUS="true"

# push some info to stdout showing that the job has started
#echo "SLURM_JOB_NODELIST: <${SLURM_JOB_NODELIST}>"
echo "SLURMD_NODENAME: <${SLURMD_NODENAME}>"
echo "SLURM_ARRAY_TASK_ID: <${SLURM_ARRAY_TASK_ID}>"
echo "CUDA_VISIBLE_DEVICES: <${CUDA_VISIBLE_DEVICES}>"
#echo "all SLURM_* variables:"
#env | grep -i slurm[_d]

idx=$SLURM_ARRAY_TASK_ID
let "gpuidx = $idx % $GPU_COUNT"

# directory setup
APP_ROOT="${HOME}/proj/IDOS"
SKY_DIR=${APP_ROOT}/spead/sender
WRK_ROOT="/flush1/dol040/oskar"
LOG_DIR=${WRK_ROOT}/log
IMG_DIR=${WRK_ROOT}/img
VIS_DIR=${WRK_ROOT}/vis
mkdir -p $LOG_DIR $IMG_DIR $VIS_DIR

VISNAME=${VIS_DIR}/${SCENARIO}-${SLURM_JOBID}.vis
FITSROOT=${IMG_DIR}/${SCENARIO}-${SLURM_JOBID}
INTER_INI=conf/Bracewell/${SCENARIO}-oskar_sim_interferometer.ini
IMAGER_INI=conf/Bracewell/${SCENARIO}-oskar_imager.ini

case "$SCENARIO" in
  RIALTO2-20)
	  # EoR sky model partitioning test case; it's a logical expansion of the single channel setup aa4-1c
	  DOUBLE_PRECISION="false"
	  START_TIME_UTC="01-01-2000 20:00:00"
	  OBS_LENGTH="06:00:00"
	  NUM_TIME_STEPS=60
	  START_FREQUENCY_HZ=(210000000 211000000 212000000 213000000 214000000 215000000 216000000 217000000)
	  NUM_CHANNELS=1
	  FREQUENCY_INC_HZ=1000000
	  
	  SM_NAME=$SCENARIO
	  POL_MODE="Scalar"
	  IMG_SIZE=512
	  FOV_DEG=6
	  CHANNEL_SNAPSHOTS="false"
	  ;;
  *)
	  echo "unsupported scenario - aborting"
	  exit 1
	  ;;
esac

# sky model
case "$SM_NAME" in
  RIALTO2-20 )
	  PHASE_CENTRE_RA_DEG="201"
	  PHASE_CENTRE_DEC_DEG="-44"
	  MAX_SOURCES_PER_CHUNK=50000
	  SKY_DIR=${SKY_DIR}/EOR
	  SM_NAME=("sky_eor_model_f210.12" "sky_eor_model_f211.13" "sky_eor_model_f212.16" "sky_eor_model_f213.19" "sky_eor_model_f214.24" "sky_eor_model_f215.03" "sky_eor_model_f216.09" "sky_eor_model_f217.17")
	  SM_FILE=()
	  for fidx in "${SM_NAME[@]}"; do SM_FILE+=("${SKY_DIR}/${fidx}.osm"); done
	  ;;
  *)
	  echo "unsupported scenario - aborting"
	  exit 1
	  ;;
esac


cd $APP_ROOT
echo "CUDA device index: <${gpuidx}>"
		  
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

oskar_sim_interferometer --set "${INTER_INI}.${idx}" interferometer/oskar_vis_filename "${VISNAME}.${idx}"

# settings specific to an OSKAR instance
oskar_sim_interferometer --set "${INTER_INI}.${idx}" simulator/cuda_device_ids $gpuidx
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

# run simulator followed by imager
(oskar_sim_interferometer "${INTER_INI}.${idx}" && oskar_imager "${IMAGER_INI}.${idx}") &	  

# sync 
wait


# clean up run specific settings files; runtime settings are captured in the OSKAR log
rm ${INTER_INI}.${idx} ${IMAGER_INI}.${idx}
#rm ${LOG_DIR}/farmoskar-mjob*