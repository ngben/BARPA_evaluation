import numpy as np
import os
import datetime as dt
import iris
import iris.cube
import iris.analysis
from iris.coord_categorisation import add_day_of_year as add_doyr
from subprocess import call
import sys
from mpi4py import MPI

comm = MPI.COMM_WORLD
rank = comm.Get_rank()
print(rank)
size = comm.Get_size()
assert size==40
i = rank%4
j = rank//4
alpha_w = iris.coords.AuxCoord(1/1000.,units='m**3*kg**-1')

cx = iris.Constraint(longitude=lambda x: 110<=x<=155)
cy = iris.Constraint(latitude=lambda x: -45<=x<=10)

path = "/g/data/tp28/dev/barpa/trials/{owner}/{trial}/{yearmon}01T0000Z/nc/{time}/"

def vapour_pressure(data):
    eps = iris.coords.AuxCoord(0.622, units=1)
    q = data.extract("specific_humidity")[0]
    P = data.extract("surface_air_pressure")[0]
    e = P * q / (eps + q - q*eps)
    e.rename("vapour_pressure")
    return e
 
def wind_speed(data):
    u = data.extract('x_wind')[0]
    v = data.extract('y_wind')[0]
    u=u.regrid(v,iris.analysis.Linear())
    w = (u**2+v**2)**0.5
    w.rename('wind_speed')
    return w

varlist = {'prcp':['av_prcp_rate','SLV1H',1],
#        'int_qu':['av_mois_flux_u','SLV3H',iris.analysis.MEAN],
#        'canopy_water':['av_canopy_wtr_cont','SLV1H',iris.analysis.MEAN],
#        'int_qv':['av_mois_flux_v','SLV3H',iris.analysis.MEAN],
        'low_cloud':['av_low_cld','SLV1H',0.1],
        'mid_cloud':['av_mid_cld','SLV1H',0.1],
        'high_cloud':['av_hi_cld','SLV1H',0.1]}

varlist1= {'canopy_water':['av_canopy_wtr_cont','SLV1H',iris.analysis.MEAN]}

file_p = "{var}-{sim}-barpa_r-v1-{yearmon}*.nc"

mon_aggs = {'mean':(iris.analysis.MEAN,1),'max':(iris.analysis.MAX,1),'min':(iris.analysis.MAX,1),'square':(iris.analysis.MEAN,2)}

def monthly_stats(trial,year,sim,owner,varlist):
    out = iris.cube.CubeList([])
    for mon in range(1,13):
      yearmon = "%04d%02d"%(year,mon)
      for var in varlist:
        print(var)
        name,time,threshold = varlist[var]
        if type(name) is list:
          data=iris.load([(path+file_p).format(trial=trial,yearmon=yearmon,sim=sim,var=n,time=time,owner=owner) for n in name[1:]],cx&cy)
          iris.util.equalise_attributes(data)
          data=data.concatenate().merge()
          data = name[0](data)
          name = name[0]
        else:
          data=iris.load((path+file_p).format(trial=trial,yearmon=yearmon,sim=sim,var=name,time=time,owner=owner),cx&cy)
          iris.util.equalise_attributes(data)
          data=data.concatenate_cube()
        if len(data.cell_methods)==0:
          data.coord('time').points = data.coord('time').points - 1/24/16
          add_doyr(data,'time','doyr')
          data.coord('time').points = data.coord('time').points + 1/24/16
        else:
          add_doyr(data,'time','doyr')
        data=data.aggregated_by('doyr',iris.analysis.MEAN)
        if data.units in ["K","Kelvin"]:
            data.convert_units("Celsius")
        if var == "prcp":
            data = data*alpha_w
            data.convert_units("mm/day")
        data.rename("frac "+var+" days")
        out.append(data.collapsed('time',iris.analysis.PROPORTION,function=lambda x: x>threshold))
    iris.util.equalise_attributes(out)
    out = out.merge()
    iris.save(out,outdir.format(trial=trial,year=year),zlib=True)

outdir = "/scratch/tp28/eh6215/monthly/{trial}/{year}_fracs.nc"
owner='chs548'


trials = {"cg282_ACCESS-CM2_historical_1979_r4p": ("CMIP6-ACCESS-CM2-historical-r4i1p1f1",np.arange(1980,1990)),
          "cg282_ACCESS-CM2_ssp370_2090_r4": ("CMIP6-ACCESS-CM2-ssp370-r4i1p1f1",np.arange(2090,2100)),
          "cg282_ACCESS-CM2_historical_1979_r6p": ("CMIP6-ACCESS-CM2-historical-r4i1p1f1",np.arange(1980,1990)),
          "cg282_ACCESS-CM2_ssp370_2090_r6":("CMIP6-ACCESS-CM2-ssp370-r4i1p1f1",np.arange(2090,2100))}


#i = int(sys.argv[1])
#j = int(sys.argv[2])

trial = ["cg282_ACCESS-CM2_historical_1979_r4p","cg282_ACCESS-CM2_ssp370_2090_r4","cg282_ACCESS-CM2_historical_1979_r6p","cg282_ACCESS-CM2_ssp370_2090_r6"][i]
sim = trials[trial][0]
year = trials[trial][1][j]
print(trial,year)
call("mkdir -p /scratch/tp28/eh6215/monthly/{trial}/".format(trial=trial),shell=True)
if not os.path.exists(outdir.format(trial=trial,year=year)):
  monthly_stats(trial,year,sim,owner,varlist)

"""
for trial in trials:
    call("mkdir -p /scratch/tp28/eh6215/monthly/{trial}/".format(trial=trial),shell=True)
    sim,years = trials[trial]
    for year in years:
        if not os.path.exists(outdir.format(trial=trial,year=year)):
          print(year)
          monthly_stats(trial,year,sim,owner,varlist)
"""
