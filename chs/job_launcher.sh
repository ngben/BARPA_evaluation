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
export metric=RX5day
export workdir=/g/data/tp28/dev/chs548/BARPA_evaluation/chs/${metric}
# evaluation expt
#export data_source=BARPA
#export barpa_gcm=ERA
#export scenario=evaluatio
# historical BARPA
export data_source=BARPA
export barpa_gcm=ACCESS-CM2
export scenario=historical
# historical CMIP6
export data_source=CMIP6
export gcm=ACCESS-CM2
export scenario=historical

years="1960"
#years=`seq 1980 2020`
#years="1980 1986 1987 1988 1989 1990 1991 1996 2000 2013 2020"
#years="1982 1986 1987 1988 1989 1994 1995 1996 1997 2001 2007 2015 2019 2020"
for year in $years; do
	export yearstart=$year
	export yearend=$year

	jobname=xc.${metric}.${data_source}.${year}
	echo "Submitting $jobname"
	echo "qsub -N $jobname -v metric,yearstart,yearend,data_source,workdir,barpa_gcm,scenario,gcm looprun_pr_xclim.sh"
done
