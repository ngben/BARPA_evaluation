
import xarray as xr
import os
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
#import cmasher as cmr
import cmocean
import cartopy.crs as ccrs
from LCS import LCS
from LCS import trajectory
import cftime
import datetime as dt

path = "/g/data/tp28/dev/barpa/prod/eh6215//cg282_ACCESS-CM2_historical_1960_sciB/{year}{month:02d}01T0000Z/nc/"
fileend = "-CMIP6-ACCESS-CM2-historical-r4i1p1f1-barpa_r-v1-"

varlist = {"av_mois_flux_v":("SLV3H",1,"{year}{month:02d}{day:02d}0130-{year}{month:02d}{day:02d}2230"),
           "av_mois_flux_u":("SLV3H",1,"{year}{month:02d}{day:02d}0130-{year}{month:02d}{day:02d}2230"),
           "ttl_col_q":     ("SLV1H",3,"{year}{month:02d}{day:02d}0100-{year1}{month1:02d}{day1:02d}0000")}

outpath = "/scratch/tp28/eh6215/Lagrangian/"

calendar='gregorian'

def compute_trajectories(date):
    date1 = date + dt.timedelta(1)
    data = {}
    for var in varlist:
        stream,k,datestr = varlist[var]
        data[var]=xr.load_dataset((path+stream+'/'+var+fileend+datestr+".nc").format(year=date.year,month=date.month,day=date.day,year1=date1.year,month1=date1.month,day1=date1.day))[var]


    q=data["ttl_col_q"][:].resample(time='3H',loffset='1.5H').interpolate('linear')
    u = data["av_mois_flux_u"][:2,::,::]/q[:2,::,::]
    v = data["av_mois_flux_v"][:2,::,::]/q[:2,::,::]

    u.name = "u"
    v.name = "v"
    ds = xr.merge([u,v])
    ds = ds.reset_coords(drop=True)

    lon = ds.longitude.values
    ds =ds.drop('longitude')
    ds=ds.assign_coords({'longitude':lon-30})

    acs = LCS.LCS(timestep=-1 * 3600, timedim='time', SETTLS_order=4, )
    ftle_a, vec1,vec2,ratio = acs(ds.copy(), isglobal=False, )
#    ftle_a = np.log(ftle_a) / 2
    ftle_a.name = "ftle_a"
    vec1.name = 'eigenvector_x'
    vec2.name = 'eigenvector_y'
    ratio.name = 'ratio'
    out = [ftle_a,vec1,vec2,ratio]
    return out

def compute(year,month):
    if calendar == 'gregorian' or '365' in calendar:
        days = [31,28,31,30,31,30,31,31,30,31,30,31][month-1]
        if calendar=='gregorian':
            if month==2 and year%4==0 and year != 2100:
                days +=1
    elif '360' in calendar:
        days=30
    else:
        exit('no such calendar')
    data = []
    for day in range(days):
        print(day+1)
        date = cftime.datetime(year,month,day+1,calendar=calendar)
        data += compute_trajectories(date)
    ds = xr.merge(data)
    lon = ds.longitude.values
    ds =ds.drop('longitude')
    ds=ds.assign_coords({'longitude':lon+30})
    ds.to_netcdf(outpath+'ACCESS-CM2_historical_%04d%02d.nc'%(year,month))


compute(1993,1)
"""
k=5
ds2 = xr.merge([u[:,::k,::k], v[:,::k,::k]])
ds2=ds2.assign_coords({'longitude':lon[::k]-30})

vec=vec.drop('time')
x = vec.isel(derivatives=1)[:,::k,::k]*ftle_a[:,::k,::k]
y = vec.isel(derivatives=0)[:,::k,::k]*ftle_a[:,::k,::k]
x=x.drop('derivatives')
y=y.drop('derivatives')
x.name = "u"
y.name = "v"
ds3 = xr.merge([x,y])


plt.figure()
ax=plt.subplot(121,projection=ccrs.PlateCarree(30))
ftle_a.isel(time=0).plot.contourf(levels=20,vmin=0,vmax=2,cmap='cubehelix_r')
ds3.isel(time=0).plot.quiver('longitude', 'latitude', 'u', 'v')
ax.coastlines()

ax=plt.subplot(122,projection=ccrs.PlateCarree(30))
div.isel(time=0).plot.contourf(levels=20,vmin=-3,vmax=0,cmap='cubehelix')
ds2.isel(time=0).plot.quiver('longitude', 'latitude', 'u', 'v')
ax.coastlines()
plt.show()

"""
