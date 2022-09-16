import os, sys
import xarray as xr

def boundary(margin=0):
    ds = xr.open_dataset('/g/data/tp28/dev/evaluation_datasets/BARPA-R_landseamask.nc')

    latmin = ds.latitude.data.min()
    latmax = ds.latitude.data.max()
    lonmin = ds.longitude.data.min()
    lonmax = ds.longitude.data.max()

    latmin -= margin
    latmax += margin
    lonmin -= margin
    lonmax += margin
    
    return latmin, latmax, lonmin, lonmax
    