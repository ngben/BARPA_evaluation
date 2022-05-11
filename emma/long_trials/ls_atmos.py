import iris
import numpy as np
#import iris.plot as iplt
import matplotlib.pyplot as plt
#import cartopy.crs as ccrs
from plotting_functions import season_bias

cx = iris.Constraint(latitude=lambda y: -45<=y<=15)
cy = iris.Constraint(longitude=lambda x: 90<=x<=180)

r4 = iris.load("/scratch/tp28/eh6215/mon_pl/cg282_ACCESS-CM2_historical_1979_r4p_198?.nc")
r6 = iris.load("/scratch/tp28/eh6215/mon_pl/cg282_ACCESS-CM2_historical_1979_r6p_198?.nc")

iris.util.equalise_attributes(r4)
iris.util.equalise_attributes(r6)

r4 = r4.concatenate()
r6 = r6.concatenate()

e5v = ['z','w']#,'v','z','q','t','w']

cp=iris.Constraint(pressure_level = lambda p: np.any([(np.abs(p.point-pp)<1) for pp in [200,500,850]]))
cp2=iris.Constraint(air_pressure = lambda p: np.any([(np.abs(p.point-pp)<1) for pp in [20000,50000,85000]]))

era5 = iris.load(["/g/data/rt52/era5/pressure-levels/monthly-averaged/%s/198*/*"%var for var in e5v],cp&cx&cy)
iris.util.equalise_attributes(era5)
era5=era5.concatenate()

for i,cube in enumerate(era5):
    if cube.name() == 'geopotential':
        era5[i] = cube/9.8
        era5[i].units = "m"
        era5[i].rename("geopotential_height")

ct= iris.Constraint(time=lambda t: t.point.year in range(1980,1990))
cmipv = ['zg','wap']
cmip = iris.load(["/g/data/r87/DRSv3/CMIP6/CMIP/CSIRO-ARCCSS/ACCESS-CM2/historical/r4i1p1f1/Amon/%s/gn/latest/*195001*"%var for var in cmipv],ct&cx&cy&cp2)

for i in range(len(cmip)):
    cmip[i] = cmip[i][:,::-1]

varlist =  {'u':['eastward_wind','x_wind'],
         'v':['northward_wind','y_wind'],
         'q':'specific_humidity',
         'z':'geopotential_height',
         'w':"lagrangian_tendency_of_air_pressure"}

from iris.coord_categorisation import add_season
for var in ['w','z']:
    for data in [r4,r6,cmip,era5]:
      cube = data.extract(varlist[var])[0]
      add_season(cube,'time','seas')
      try:
        cube.coord("longitude").guess_bounds()
        cube.coord("latitude").guess_bounds()
      except ValueError:
          1
      cube.coord("longitude").coord_system=None
      cube.coord("latitude").coord_system=None


var = 'z'
for p in [0,1,2]:
    plt.figure()
    ref = era5.extract(varlist[var])[0][:,p]
    subset = [data.extract(varlist[var])[0][:,p] for data in [r4,r6,cmip]]
    season_bias(ref,subset,subset[-1],[40,20,20][p],'BrBG',['FB','r6','cm2'])
    plt.show()

var = 'q'
for p in range(2,3):
    plt.figure()
    ref = era5.extract(varlist[var])[0][:,p]
    subset = [data.extract(varlist[var])[0][:,p] for data in [r4,r6,cmip]]
    season_bias(ref,subset,subset[-1],0.002,'BrBG',['FB','r6','cm2'])

plt.show()
var = 'w'
for p in [1]:
    plt.figure()
    ref = era5.extract(varlist[var])[0][:,p]
    subset = [data.extract(varlist[var])[0][:,p] for data in [r4,r6,cmip]]
    season_bias(ref,subset,subset[-1],0.08,'PiYG',['FB','r6','cm2'])

plt.show()
var = 'u'
for p in [0,1,2]:
    plt.figure()
    ref = era5.extract(varlist[var])[0][:,p]
    subset = [data.extract(varlist[var])[0][:,p] for data in [r4,r6,cmip]]
    season_bias(ref,subset,subset[-1],[10,5,5][p],'PiYG',['FB','r6','cm2'])

plt.show()

