#!/bin/bash

#SBATCH --nodes=1
#SBATCH --time=01:00:00
#SBATCH --ntasks-per-node=1
#SBATCH --gres=gpu:1
#SBATCH --mem=32g
#SBATCH --job-name=MPI_Sender

module use /flush1/tob020/modulefiles
module load oskar/2.7.1-adios
module load spead2/1.10.0
module load casacore/3.0.0-adios
module load adios/2.2.0

APP_ROOT="/home/wu082/proj/jacal/summit_demo/oskar/ingest"

mpirun -np 1 /flush1/wu082/summit_env/bin/python $APP_ROOT"/spead_send.py" --conf $APP_ROOT"/conf/send01.json"