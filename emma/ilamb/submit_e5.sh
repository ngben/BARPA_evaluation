#!/bin/bash

#PBS -N job_e5
#PBS -l walltime=04:00:00
#PBS -q normal
#PBS -P tp28
# PBS -W umask=0007
#PBS -l storage=scratch/tp28+gdata/tp28+gdata/hh5+gdata/access+gdata/dp9+gdata/rt52
#PBS -l mem=66G
#PBS -l ncpus=11

module use ~access/modules
module use /g/data/hh5/public/modules
module load conda/analysis3

cd /home/548/eh6215/python/BARPA_evaluation/emma/ilamb/

mpiexec -n 11 python prep_era5.py
