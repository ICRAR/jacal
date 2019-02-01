#!/bin/bash

#SBATCH --nodes=1
#SBATCH --time=00:10:00
#SBATCH --ntasks-per-node=1
#SBATCH --mem=2g
#SBATCH --job-name=MPI_Relay

module use /flush1/tob020/modulefiles
module load oskar/2.7.1-adios
module load spead2/1.10.0
module load casacore/3.0.0-adios
module load adios/2.2.0

APP_ROOT="/home/wu082/proj/jacal/summit_demo/oskar/ingest"
source /flush1/wu082/summit_env/bin/activate
srun -n 1 python $APP_ROOT"/spead_recv.py" --conf $APP_ROOT"/conf/recv_relay.json"
