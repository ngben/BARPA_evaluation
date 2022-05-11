#!/g/data3/hh5/public/apps/miniconda3/envs/analysis3-21.10/bin/python
  
import numpy as np
import os
import datetime as dt
import iris
import iris.cube
import iris.analysis
from iris.coord_categorisation import add_day_of_year as add_doyr
from subprocess import call

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


#path =  "/scratch/tp28/{owner}/cylc-run/{trial}/share/data/LM_History/nc/{time}/"
#path =  "/scratch/tp28/{owner}/barpa/trials/{owner}/{trial}/{yearmon}01T0000Z/nc/{time}/"

varlist = ["geop_ht_uv","spec_hum_uv","wnd_ucmp","wnd_vcmp","air_temp_uv","omega_uv"]

file_p = "{var}-{sim}-barpa_r-v1-{yearmon}*.nc"
cp=iris.Constraint(pressure = lambda p: np.any([(np.abs(p.point-pp)<1) for pp in [200,500,850,1000]]))
#cp=iris.Constraint(pressure = lambda p: np.any([(np.abs(p.point-pp)<1) for pp in [500]]))
ct = iris.Constraint(time=lambda t: t.point.hour in [0,6,12,18])
def monthly_mean(trial,year,sim,varlist):
    out = iris.cube.CubeList([])
    time  = "PRS3H"
    owner = "chs548"
    for mon in range(1,13):
      yearmon = "%04d%02d"%(year,mon)
      for var in varlist:
        print(var)
        data=iris.load((path+file_p).format(trial=trial,yearmon=yearmon,sim=sim,var=var,time=time,owner=owner),cp&ct)
        iris.util.equalise_attributes(data)
        try:
            data=data[:].concatenate_cube()
        except iris.exceptions.ConcatenateError:
            data=data[:].merge_cube()
        mean = data.collapsed("time",iris.analysis.MEAN)
        out += [mean]
    iris.util.equalise_attributes(out)
    out=out.merge()
    iris.save(out,outdir.format(trial=trial,year=year),zlib=True)

outdir = "/scratch/tp28/eh6215/mon_pl/{trial}_{year}.nc"

trials = {"cg282_ACCESS-CM2_historical_1979_r4p": ("CMIP6-ACCESS-CM2-historical-r4i1p1f1",np.arange(1980,1990)),
          "cg282_ACCESS-CM2_ssp370_2090_r4": ("CMIP6-ACCESS-CM2-ssp370-r4i1p1f1",np.arange(2090,2100)),
          "cg282_ACCESS-CM2_historical_1979_r6p": ("CMIP6-ACCESS-CM2-historical-r4i1p1f1",np.arange(1980,1990)),
          "cg282_ACCESS-CM2_ssp370_2090_r6":("CMIP6-ACCESS-CM2-ssp370-r4i1p1f1",np.arange(2090,2100))}

trial = ["cg282_ACCESS-CM2_historical_1979_r4p","cg282_ACCESS-CM2_ssp370_2090_r4","cg282_ACCESS-CM2_historical_1979_r6p","cg282_ACCESS-CM2_ssp370_2090_r6"][i]
sim = trials[trial][0]
year = trials[trial][1][j]

monthly_mean(trial,year,sim,varlist)

