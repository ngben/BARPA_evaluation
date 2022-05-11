import iris
import iris.coords
import datetime as dt
import os
import numpy as np
import matplotlib.pyplot as plt
import iris.plot as iplt
import cmocean
import cartopy.crs as ccrs

from plotting_functions import bias_plots
from load_cmip import load_cmip

cy=iris.Constraint(latitude=lambda y: -45<y<-10)
cx=iris.Constraint(longitude=lambda x: 110<x<155)
trials = {"cg282_ACCESS-CM2_historical_1979_r4p": ("CMIP6-ACCESS-CM2-historical-r4i1p1f1",np.arange(1980,1990)),
          "cg282_ACCESS-CM2_ssp370_2090_r4": ("CMIP6-ACCESS-CM2-ssp370-r4i1p1f1",np.arange(2090,2100)),
          "cg282_ACCESS-CM2_historical_1979_r6p": ("CMIP6-ACCESS-CM2-historical-r4i1p1f1",np.arange(1980,1990)),
          "cg282_ACCESS-CM2_ssp370_2090_r6":("CMIP6-ACCESS-CM2-ssp370-r4i1p1f1",np.arange(2090,2100))}

alpha_w = iris.coords.AuxCoord(1/1000.,units='m**3*kg**-1')


data= {}
path = "/scratch/tp28/eh6215//monthly/{trial}/{year}_fracs.nc"
for trial in  ["cg282_ACCESS-CM2_historical_1979_r4p","cg282_ACCESS-CM2_ssp370_2090_r4","cg282_ACCESS-CM2_historical_1979_r6p","cg282_ACCESS-CM2_ssp370_2090_r6"]:
  tmp = iris.load([path.format(trial=trial,year=year) for year in trials[trial][1]],cx&cy)
  iris.util.equalise_attributes(tmp)
  tmp = tmp.concatenate()
  trial=trial.split("_")[-1]
  data[trial] = {}
  for var in ['frac prcp days']:
      data[trial]['prcp'] =tmp.extract_cube(var.lower()).collapsed('time',iris.analysis.MEAN)
      data[trial]['prcp'].units=1

topo=iris.load_cube("../trials/orog.nc",cx&cy)
lapse = iris.coords.AuxCoord(-6,units="K/km")
cmip_info = {"ACCESS-CM2":("CSIRO-ARCCSS","r4i1p1f1")}

mask = topo.data<=0
years = trials["cg282_ACCESS-CM2_historical_1979_r4p"][1]
data['ref'] = {}
for var in ['prcp','Tmax','Tmin','vapourpres_15'][:1]:
  if var=='prcp':
    data['ref'][var] = iris.load(["/g/data/zv2/agcd/v1/precip/total/r005/01day/agcd_v1_precip_total_r005_daily_%d.nc"%year for year in years],cx&cy)
  else:
    data['ref'][var] = iris.load(["/g/data/zv2/agcd/v1/{t}/mean/r005/01day/agcd_v1_{t}_mean_r005_monthly_{year}.nc".format(year=year,t=var.lower()) for year in years],cx&cy)
  iris.util.equalise_attributes(data['ref'][var] )
  data['ref'][var] =data['ref'][var] .concatenate_cube()
  data['ref'][var].coord('longitude').coord_system=None
  data['ref'][var].coord('latitude').coord_system=None
  data['ref'][var] = data['ref'][var].collapsed('time',iris.analysis.PROPORTION,function=lambda x:x>1)
  data['ref'][var] =data['ref'][var].regrid(data['r4p'][var],iris.analysis.Linear(extrapolation_mode='mask'))


data['ref']['prcp'].units=1

"""

def bias_plots(data,var,mask,keys,vmin,vmax,vdiff,cmap1,cmap2,units,offset=0):
  n = len(keys)
  for i,trial1 in enumerate(keys):
    for j,trial2 in enumerate(keys):
      if i==j:
          cube = data[trial1][var]#.collapsed('time',iris.analysis.MEAN)
          cube.convert_units(units)
          cube.data = np.ma.masked_array(cube.data,mask)
          ax=plt.subplot(n,n,n*i+j+1,projection=ccrs.PlateCarree(offset))
          iplt.pcolormesh(cube,vmin=vmin,vmax=vmax,cmap=cmap1)
          plt.colorbar()
          ax.coastlines(zorder=6)
          plt.title(trial1)
      elif i<j:
          cube1 = data[trial1][var]#.collapsed('time',iris.analysis.MEAN)
          cube1.convert_units(units)
          cube1.data = np.ma.masked_array(cube1.data,mask)
          cube2 = data[trial2][var]#.collapsed('time',iris.analysis.MEAN)
          cube2.convert_units(units)
          cube2.data = np.ma.masked_array(cube2.data,mask)
          rmse = np.sqrt(((cube1 - cube2)**2).collapsed(['latitude','longitude'],iris.analysis.MEAN).data)
          ax=plt.subplot(n,n,n*i+j+1,projection=ccrs.PlateCarree())
          iplt.pcolormesh(cube1-cube2,vmin=-vdiff,vmax=vdiff,cmap=cmap2)
          plt.title("%s - %s (%.2f)"%(trial1,trial2,rmse))
          ax.coastlines(zorder=6)
          plt.colorbar()
  plt.suptitle(var)

from iris.coord_categorisation import add_month
def ts_bias_plots(data,var,mask,keys,ref_key,units):
  n = len(keys)
  ref = data[ref_key][var]
  ref.convert_units(units)
  ref.data = np.ma.masked_array(ref.data,mask[np.newaxis]*np.zeros(ref.shape))
  if not 'month' in [c.name() for c in ref.coords()]:
    add_month(ref,'time','month')
  ref = ref.aggregated_by('month',iris.analysis.MEAN)
  ref.remove_coord('time')
  for i,trial in enumerate(keys):
    cube = data[trial][var] 
    cube.convert_units(units)
    cube.data = np.ma.masked_array(cube.data,mask[np.newaxis]*np.zeros(cube.shape))
    if not "month" in [c.name() for c in cube.coords()]:
      add_month(cube,'time','month')
    cube = cube.aggregated_by('month',iris.analysis.MEAN)
    cube.remove_coord('time')
    bias = ((cube-ref)).collapsed(['longitude','latitude'],iris.analysis.MEAN)
    iplt.plot(bias,label=trial)
    plt.xticks(range(12),["J","F","M","A","M","J","J","A","S","O","N","D"])
  plt.legend()



from iris.coord_categorisation import add_month
def rmse_plots(data,var,mask,keys,ref_key,units):
  n = len(keys)
  ref = data[ref_key][var]
  ref.convert_units(units)
  ref.data = np.ma.masked_array(ref.data,mask[np.newaxis]*np.zeros(ref.shape))
  if not 'month' in [c.name() for c in ref.coords()]:
    add_month(ref,'time','month')
  ref = ref.aggregated_by('month',iris.analysis.MEAN)
  ref.remove_coord('time')
  for i,trial in enumerate(keys):
    cube = data[trial][var] 
    cube.convert_units(units)
    cube.data = np.ma.masked_array(cube.data,mask[np.newaxis]*np.zeros(cube.shape))
    if not "month" in [c.name() for c in cube.coords()]:
      add_month(cube,'time','month')
    cube = cube.aggregated_by('month',iris.analysis.MEAN)
    cube.remove_coord('time')
    rmse = ((cube-ref)**2).collapsed(['longitude','latitude'],iris.analysis.MEAN)**0.5
    iplt.plot(rmse,label=trial)
    plt.xticks(range(12),["J","F","M","A","M","J","J","A","S","O","N","D"])
  plt.legend()

"""
     

for key1 in data.keys():
    for key2 in data[key1].keys():
        data[key1][key2].coord('longitude').points = data[key1][key2].coord('longitude').points.astype(np.float32)
        data[key1][key2].coord('latitude').points  = data[key1][key2].coord('latitude').points.astype(np.float32)
        data[key1][key2].coord('longitude').coord_system = None
        data[key1][key2].coord('latitude').coord_system = None

plt.figure(figsize=(15,10))
bias_plots(data,'prcp',mask,['r4p','r6p','ref'],0,1,0.2,cmocean.cm.rain,'bwr_r','1')
plt.tight_layout()
plt.show()


