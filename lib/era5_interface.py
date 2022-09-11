"""
 Interface to extract ERA5 data from the rt52 project.
"""
import os, sys
import iris
import iris.cube
from datetime import datetime as dt
from datetime import timedelta as delt
import pandas as pd
import numpy as np
import xarray as xr
import glob

_DATA_ROOTDIR = '/g/data/rt52/era5'
_VERBOSE = False

def print_msg(msg):
    """
    Prints text to stdout for diagnosis.

    Parameters
    ----------
    msg: str
        Text to print
    """
    if _VERBOSE:
        print(msg)
    return

def get_era5_files(stream, freq, variable, trange=(None, None)):
    """
    Returns all the matching files.

    Parameters
    ----------
    stream: str
        Either pressure-levels or single-levels as per /g/data/rt52/era5/[stream]/[freq]/[variable]
    freq: str
        Either monthly-averaged or reanalysis, as per /g/data/rt52/era5/[stream]/[freq]/[variable]
    variable: str
        variable name, as per /g/data/rt52/era5/[stream]/[freq]/[variable]
    trange: tuple or an array of datetime objects (optional)
        Time range
    
    Returns
    -------
    A list of string
        A list of matching filenames
    """
    tstart = trange[0]
    tend = trange[1]
    
    tstart0 = dt(tstart.year, tstart.month, 1) if tstart is not None else dt(1979, 1, 1)
    # Data is available around 4 months behind present day
    today = dt.now() - delt(days=4*30)
    tend0 = dt(tend.year, tend.month, 1) if tend is not None else dt(today.year, today.month, 1)
    
    assert freq in ["monthly-averaged", "reanalysis"], "Undefined freq, either monthly-averaged or reanalysis"
    
    tspan = pd.date_range(tstart0, tend0, freq='1MS')
    files = []
    for time in tspan:
        print_msg("Looking for data for {:}".format(time))
        
        rootdir = os.path.join(_DATA_ROOTDIR, stream, freq, variable, "%d" % time.year)
        # use the era5-1 for the affected period
        if stream == "pressure-levels" and time.year >= 2000 and time.year <= 2006:
            rootdir = os.path.join(_DATA_ROOTDIR+"-1", stream, 'reanalysis', variable, "%d" % time.year)
        
        print_msg("Data directory: {:}".format(rootdir))
        
        file_match = os.path.join(rootdir, '%s_*_%s*.nc' % (variable, time.strftime("%Y%m%d")))
        files += glob.glob(file_match)
        
    print_msg("Number of files found is: {:}".format(len(files)))

    return files

def callback(cube, field, filename):
    """
    Shift the ERA5 along longitude so that it goes from 0..360deg
    """
    cube1 = cube.extract(iris.Constraint(longitude=lambda x: x>=0))
    cube2 = cube.extract(iris.Constraint(longitude=lambda x: x<0))
    cube2.coord('longitude').points = cube2.coord('longitude').points + 360
    if cube2.coord('longitude').has_bounds():
        cube2.coord('longitude').bounds = cube2.coord('longitude').bounds + 360
    return iris.cube.CubeList([cube1,cube2]).concatenate_cube()

def get_era5(stream, freq, variable, 
             trange=(None, None), latrange=(None, None), lonrange=(None, None), 
             save=None, as_iris=True,
             verbose=True):
    """
    Returns ERA5 data as iris data cubes.
    
    Parameters
    ----------
    stream: str
        Either pressure-levels or single-levels as per /g/data/rt52/era5/[stream]/[freq]/[variable]
    freq: str
        Either monthly-averaged or reanalysis, as per /g/data/rt52/era5/[stream]/[freq]/[variable]
    variable: str
        variable name, as per /g/data/rt52/era5/[stream]/[freq]/[variable]
    trange: tuple or an array of datetime objects (optional)
        Time range
    latrange: tuple or an array of floats
        Latitude range
    lonrange: tuple or an array of floats
        Longitude range
    save: str (optional)
        Path to an output netcdf file if writing the extracted data
    as_iris: boolean (optional)
        Whether to return as iris.Cubes or xarray.Dataset
    verbose: boolean (optional)
        Whether to be verbose with the operation
        
    Returns
    -------
    iris.Cubes
        Extracted data
    """
    global _VERBOSE 
    _VERBOSE = verbose
              
    latmin = -90  if latrange[0] is None else latrange[0]
    latmax = 90   if latrange[1] is None else latrange[1]
    lonmin = -360 if lonrange[0] is None else lonrange[0]
    lonmax = 360  if lonrange[1] is None else lonrange[1]
    tstart = dt(1900, 1, 1) if trange[0] is None else trange[0]
    tend = dt(2200, 1, 1) if trange[1] is None else trange[1]
        
    files = get_era5_files(stream, freq, variable, trange=trange)
    
    if as_iris:
        cx = iris.Constraint(longitude=lambda x: lonmin<=x<=lonmax)
        cy = iris.Constraint(latitude=lambda x: latmin<=x<=latmax)
        ct = iris.Constraint(time=lambda x: tstart<=x.point<=tend)

        print_msg("Opening files: {:}".format(files))
        data_list = iris.load(files, callback=callback) #, ct&cx&cy)
        iris.util.equalise_attributes(data_list)
        data = data_list.concatenate()
        data_slice = data.extract(ct&cx&cy)
    
        if save is not None:
            iris.save(data_slice, save, zlib=True)
            print_msg("Saving to {:}".format(save))
    
        print_msg("Returning as iris cubes")
    else:
        ds = xr.open_mfdataset(files)
        ds.coords['longitude'] = (ds.coords['longitude'] + 360) % 360
        ds = ds.sortby(ds.longitude)
        ds = ds.sortby(ds.latitude)
        data_slice = ds.sel(time=slice(tstart, tend), latitude=slice(latmin, latmax), longitude=slice(lonmin, lonmax))
    
        if save is not None:
            data_slice.to_netcdf(save)
            print_msg("Saving to {:}".format(save))
        
        print_msg("Returning as xarray.dataset")
        
    return data_slice