#!/g/data3/hh5/public/apps/miniconda3/envs/analysis3-22.01/bin/python

#PBS -N job_4
#PBS -l walltime=02:00:00
#PBS -q normal
#PBS -P tp28
# PBS -W umask=0007
#PBS -l storage=scratch/tp28+gdata/tp28+gdata/hh5+gdata/access+gdata/dp9+gdata/rt52
#PBS -l mem=16G
#PBS -l jobfs=2G
#PBS -l ncpus=4

import numpy as np
import iris
import iris.cube
import os
from iris.coord_categorisation import add_day_of_year,add_month
import iris.analysis

tmppath = os.environ['PBS_JOBFS']
outpath = '/g/data/tp28/dev/eh6215/comp/'

def callback(cube,field,filename):
    cube1 = cube.extract(iris.Constraint(longitude=lambda x: x>=0))
    cube2 = cube.extract(iris.Constraint(longitude=lambda x: x<0))
    cube2.coord('longitude').points = cube2.coord('longitude').points + 360
    if cube2.coord('longitude').has_bounds():
        cube2.coord('longitude').bounds = cube2.coord('longitude').bounds + 360
    return iris.cube.CubeList([cube1,cube2]).concatenate_cube()

def load_aggregate(var,path,years,constraints,aggregators,name=None):
    data= iris.load([os.path.join(path,var,str(year),"*.nc") for year in years],constraints,callback)
    iris.util.equalise_attributes(data)
    data = data.concatenate_cube()
    for a in aggregators:
        if a[0]=='collapse':
            data = data.collapsed(a[1],a[2])
        elif a[0] == 'aggregate':
            if a[1] == 'day':
                add_day_of_year(data,'time',a[1])
            elif a[1] == 'month':
                add_month(data,'time',a[1])
            else:
                exit(1,'implement')
            data = data.aggregated_by(a[1],a[2])
        else:
            exit(1,'implement')
    if not name is None:
       data.rename(data.name()+name)
    iris.save(data,os.path.join(tmppath,data.name()).replace(" ","_")+".nc")
    return os.path.join(tmppath,data.name()).replace(" ","_")+".nc"
    
def main(exp):
    files = []
    e5path_s = "/g/data/rt52/era5/single-levels/monthly-averaged/"
    e5path_p = "/g/data/rt52/era5/pressure-levels/monthly-averaged/"
    c_p2 = iris.Constraint(pressure_level=lambda p: p in [200,500,850])
    c_px = iris.Constraint(pressure_level=lambda p: p in [1000,950,925,850,700,600,500,400,300,200])
    c_aus = iris.Constraint(longitude=lambda x: 110<=x<=155)
    cx = iris.Constraint(longitude=lambda x: 90<=x<=200)
    cy = iris.Constraint(latitude=lambda y: -50<=y<=10)
    c_t6 = iris.Constraint(time=lambda t:t.point.hour in [0,6,12,18])
    for var in ['tcwv','mtnlwrf','msl','2t']:
        files.append(load_aggregate(var,e5path_s,np.arange(1990,2021),cx&cy,[('aggregate','month',iris.analysis.MEAN)]))
    for var in ['u','v','q','t']:
        files.append(load_aggregate(var,e5path_p,np.arange(1990,2021),cx&cy&c_p2,[('aggregate','month',iris.analysis.MEAN)]))
#    for var in ['u','v','w','t','q']:
#        files.append(load_aggregate(var,e5path_p,np.arange(1990,2021),cy&cx&c_px,[('aggregate','month',iris.analysis.MEAN),('collapse',['longitude'],iris.analysis.MEAN)],name='_zm'))
#    for var in ['u','v','w','t','q']:
#        files.append(load_aggregate(var,e5path_p,np.arange(1990,2021),cy&c_aus&c_px,[('aggregate','month',iris.analysis.MEAN),('collapse',['longitude'],iris.analysis.MEAN)],name='_au'))
    data = iris.load(files)
    iris.util.equalise_attributes(data)
    data=data.merge()
    iris.save(data,outpath+exp+".nc",zlib=True)
    for f in files:
      os.remove(f)

runs = {"cg282_ACCESS-CM2_historical_1960_sciB":('eh6215',1961,1969),
        "cg282_ACCESS-CM2_ssp126_2014_sciB":('eh6215',2015,2022),
        "cg282_ACCESS-CM2_ssp370_2014_sciB":('eh6215',2015,2024),
        "cg282_ACCESS-ESM1-5_ssp370_2014_sciB":('cst565',2015,2019),
        "cg282_ERA5_historical_1979_sciB":('chs548',1980,1983)}

main('era5')

