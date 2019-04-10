#!/bin/bash

#SBATCH --nodes=1
#SBATCH --time=00:10:00
#SBATCH --ntasks-per-node=1
#SBATCH --gres=gpu:4
#SBATCH --mem=2g
#SBATCH --job-name=get_gpu_info

module load tensorflow/1.2.1-py27-gpu

srun python /home/wu082/proj/jacal/summit_demo/integrate/bracewell/get_gpu_info.py
