#!/bin/bash

# metric
# yearstart
# yearend
# data_source
# workdir
# barpa_gcm
# scenario
# gcm

#List of metrics are, RR1 RX1day R10mm R20mm dry_days RX1day RX5day prcptot
export metric=prcptot
export workdir=/g/data/tp28/dev/chs548/BARPA_evaluation/chs/${metric}
# evaluation expt
#export barpa_gcm=ERA
#export scenario=evaluation
# historical BARPA
#export data_source=BARPA
export barpa_gcm=ACCESS-CM2
export scenario=historical
# historical CMIP6
export gcm=ACCESS-CM2
export scenario=historical

#data_sources="AGCD ERA5 BARPA GPCC"
data_sources="BARPA CMIP6"
years=`seq 1960 1960`

for data_source in $data_sources; do
	export data_source
	for year in $years; do
		export yearstart=$year
		export yearend=$year

		jobname=xc.${metric}.${data_source}.${year}
		echo "Submitting $jobname"
		qsub -N $jobname -v metric,yearstart,yearend,data_source,workdir,barpa_gcm,scenario,gcm looprun_pr_xclim.sh
	done
done
