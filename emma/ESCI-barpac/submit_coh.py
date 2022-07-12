#!/bin/bash

#PBS -N job_coh
#PBS -l walltime=04:00:00
#PBS -q normal
#PBS -P tp28
# PBS -W umask=0007
#PBS -l storage=scratch/tp28+gdata/tp28+gdata/hh5+gdata/access+gdata/dp9+gdata/rt52
#PBS -l mem=18G
#PBS -l ncpus=10

module use ~access/modules
module use /g/data/hh5/public/modules
module load conda/analysis3

export PYTHONPATH=$PYTHONPATH:/home/548/eh6215/python/BARPA_evaluation/emma/lib
export PYTHONPATH=$PYTHONPATH:/home/548/eh6215/python/ASoP/ASoP-Spectral
export PYTHONPATH=$PYTHONPATH:/home/548/eh6215/python/ASoP/ASoP-Coherence

cd /home/548/eh6215/python/BARPA_evaluation/emma/ESCI-barpac

mpiexec -n 10 python compute_coherence.py
