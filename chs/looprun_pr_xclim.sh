#!/bin/bash
#PBS -l walltime=00:40:00
#PBS -l ncpus=4
#PBS -l mem=40GB
#PBS -l wd
#PBS -m n
#PBS -P tp28
#PBS -q normal
#PBS -l storage=gdata/access+gdata/dp9+gdata/du7+gdata/tp28+scratch/tp28+scratch/dp9+gdata/hh5+gdata/hd50+scratch/hd50+gdata/cj37+gdata/rt52+gdata/zv2+gdata/ia39+gdata/fs38+gdata/r87+gdata/oi10+gdata/ua6

module use /g/data3/hh5/public/modules
module load conda/analysis3

# environment variable
# metric
# yearstart
# yearend
# data_source
# workdir
# barpa_gcm
# scenario
# gcm

years=`seq $yearstart $yearend`

script="python run_pr_xclim.py --metric $metric --data_source $data_source --workdir $workdir --years $years"

if [ "$data_source" == "BARPA" ]; then
	script="$script --scenario $scenario --barpa_gcm $barpa_gcm"
elif [ "$data_source" == "CMIP6" ]; then
	script="$script --scenario $scenario --gcm $gcm"
fi

echo "Running: $script"
$script
if [ $? -eq 0 ]; then
	exit 0
	echo "SUCCESS"
else
	exit 1
	echo "FAILED"
fi
