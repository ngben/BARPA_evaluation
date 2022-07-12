import iris
import numpy as np
import os
#os.chdir("/home/548/eh6215/Desktop/python/ASoP/ASoP-Spectral/ASoP1_spectral")
from ASoP1_spectral import make_hist_maps
from ASoP1_spectral import plot_hist_maps
from ASoP1_spectral import plot_hist1d


path1 = "/g/data/tp28/BARPA/trials/{domain}*/era/erai/historical/r0/pp_unified/3hourly/av_prcp_rate/0p05deg/{year}/"
path2 = "/short/tp28/eh6215/ESCI/3hr_BARPAC-T/"

def compute(name,year):
    if name in ["BARPAC-M","BARPA-E"]:
        data=iris.load([(path1+"/*_{year:04d}{month:02d}*").format(domain=name,year=year1,month=month) for year1,month in [(year,12),(year+1,1),(year+1,2)]])
    else:
        data=iris.load([(path2+"/*_{year:04d}{month:02d}*").format(domain=name,year=year1,month=month) for year1,month in [(year,12),(year+1,1),(year+1,2)]])
    iris.util.equalise_attributes(data)
    data=data.concatenate_cube()
    data.units = "mm/s"
    data.convert_units("mm/day")
    hist = make_hist_maps.make_hist_ppn(data)
    iris.save(hist, "/short/tp28/eh6215/ESCI/ASoP/coherence_%s_%d.nc"%(name,year))
    #add_day_of_year(data[name],'time','day')
    #data[name]=data[name].aggregated_by('day',iris.analysis.MEAN)

for year in range(1991,2016):
  for name in ["BARPAC-M","BARPAC-T","BARPA-E"]:
    print(name,year)
    compute(name,year)
