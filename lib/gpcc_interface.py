"""
 Interface to extract GPCC precip data from the ia39 project.
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

_VERSION = "v2020"
_DATA_ROOTDIR = '/g/data/ia39/aus-ref-clim-data-nci/gpcc/data/full_data_{freq}_{version}/{res}'
_FILENAME_MONTHLY = "full_data_monthly_{version}_*_{res}.nc"
_FILENAME_DAILY = "full_data_daily_{version}_{res}_*.nc"
_VERBOSE = False

def str2dt(t, start=True):
    """
    Convert the datetime string to datetime object.

    Parameters
    -----------
    t: str
        Datetime in string, either y, ym, ymd, ymdH format
    start: boolean
        True to return the earliest time for that year, month, day or hour
        else return the latest time for that year, month, day or hour
    
    Returns
    -------
    datetime.datetime
        datetime object of the datetime matching t
    """
    assert len(t) in [4, 6, 8, 10, 12], "Undefine time range information: {:}".format(t)
    if len(t) == 4:
        # Assume yyyy
        y = int(t)
        if start:
            return dt(y, 1, 1, 0, 0)
        else:
            return dt(y, 12, 12, 23, 59, 59)
    elif len(t) == 6:
        # Assume yyyymm
        y = int(t[:4])
        m = int(t[4:])
        if start:
            return dt(y, m, 1, 0, 0)
        else:
            return dt(y, m, calendar.monthrange(y, m)[1], 23, 59, 59)
    elif len(t) == 8:
        # Assume yyyymmdd
        y = int(t[:4])
        m = int(t[4:6])
        d = int(t[6:])
        if start:
            return dt(y, m, d, 0, 0)
        else:
            return dt(y, m, d, 23, 59, 59)
    elif len(t) == 10:
        # Assume yyyymmddHH
        y = int(t[:4])
        m = int(t[4:6])
        d = int(t[6:8])
        HH = int(t[8:])
        if start:
            return dt(y, m, d, HH, 0)
        else:
            return dt(y, m, d, HH, 59, 59)
    elif len(t) == 12:
        # Assume yyyymmddHHMM
        y = int(t[:4])
        m = int(t[4:6])
        d = int(t[6:8])
        HH = int(t[8:10])
        MM = int(t[10:])
        if start:
            return dt(y, m, d, HH, MM, 0)
        else:
            return dt(y, m, d, HH, MM, 59)
    return

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

def screen_files(files, freq="monthly", trange=(None, None)):
    """
    Filters the list of files based on prescribed time range.

    Parameters
    ----------
    files: list of string
        A list of filenames, assumes that the time information in filename
        exists in *_<t0>-<t1>.nc
    trange: tuple of datetime objects
        Time range, earliest time and latest time

    Returns
    -------
    A list of str
        A list of filenames that match the time range.
    """
    tstart = trange[0]
    tend = trange[1]
    
    if tstart is None:
        tstart = dt(1900, 1, 1)
    if tend is None:
        tend = dt(2200, 1, 1)
    
    files_filt = []
    for file in files:
        bn = os.path.basename(file)
        b = os.path.splitext(bn)[0]
        toks = b.split("_")
        if freq == 'daily':
            t0 = str2dt(toks[-1], start=True)
            t1 = str2dt(toks[-1], start=False)
        else:
            t0 = str2dt(toks[4], start=True)
            t1 = str2dt(toks[5], start=False)
            
        #print("{:},{:} v {:},{:}".format(t0, t1, tstart, tend))
        if t1 < tstart:
            #print("{:} < {:}".format(t1, tstart))
            continue
        if t0 > tend:
            continue
        files_filt.append(file)
    
    files_filt.sort()
    
    return files_filt

def get_files(freq, res, trange=(None, None)):
    """
    Returns all the matching files.

    Parameters
    ----------
    freq: str
        Either daily or monthly per /g/data/ia39/aus-ref-clim-data-nci/gpcc/data
    res: str
        Resolution, choosing from g10, g025 g05 g10 g25
    trange: tuple or an array of datetime objects (optional)
        Time range
        
    Daily data is from 1982 to 2019
    Monthly data can go back to 1900
    
    Returns
    -------
    A list of string
        A list of matching filenames
    """    
    assert freq in ["daily", "monthly"], "Undefined freq, either monthly or daily"
    assert res in ["g025", "g05", "g10", "g25"], "Undefined res"
    
    datadir = _DATA_ROOTDIR.format(freq=freq, res=res, version=_VERSION)
    print_msg("Looking at files in {:}".format(datadir))
    
    if freq == "monthly":
        bn = _FILENAME_MONTHLY.format(res=res[1:], version=_VERSION)
    else:
        bn = _FILENAME_DAILY.format(res=res[1:], version=_VERSION)
        
    files = glob.glob(os.path.join(datadir, bn))
    files.sort()
    print_msg("Number of files in there is: {:}".format(len(files)))
              
    files = screen_files(files, freq=freq, trange=trange)
    print_msg("Number of files within time range is: {:}".format(len(files)))
    
    return files

def get_gpcc(freq, res, 
             trange=(None, None), latrange=(None, None), lonrange=(None, None), 
             save=None, 
             verbose=True):
    """
    Returns GPCC data as xarray.dataset
    
    Parameters
    ----------
    freq: str
        Either daily or monthly per /g/data/ia39/aus-ref-clim-data-nci/gpcc/data
    res: str
        Resolution, choosing from g10, g025 g05 g10 g25
    trange: tuple or an array of datetime objects (optional)
        Time range
    latrange: tuple or an array of floats
        Latitude range
    lonrange: tuple or an array of floats
        Longitude range
    save: str (optional)
        Path to an output netcdf file if writing the extracted data
    verbose: boolean (optional)
        Whether to be verbose with the operation
        
    Returns
    -------
    xarray.dataset
        Extracted data
    """
    global _VERBOSE
    _VERBOSE = verbose 
    
    files = get_files(freq, res, trange=trange)
    print_msg("Found {:} files".format(len(files)))
    [print_msg(os.path.basename(f)) for f in files]
    
    if len(files) == 0:
        print_msg("No files found")
        return None
    
    latmin = -90  if latrange[0] is None else latrange[0]
    latmax = 90   if latrange[1] is None else latrange[1]
    lonmin = -360 if lonrange[0] is None else lonrange[0]
    lonmax = 360  if lonrange[1] is None else lonrange[1]
    
    tstart = dt(1900, 1, 1) if trange[0] is None else trange[0]
    tend = dt(2200, 1, 1) if trange[1] is None else trange[1]
    
    ds = xr.open_mfdataset(files)
    
    ds.coords['lon'] = (ds.coords['lon'] + 360) % 360
    ds = ds.sortby(ds.lon)
    ds = ds.sortby(ds.lat)
    #ds = ds.reindex(lat=list(reversed(ds.lat)))
    
    out = ds.sel(time=slice(tstart, tend), lat=slice(latmin, latmax), lon=slice(lonmin, lonmax))
    
    if save is not None:
        out.to_netcdf(save)
        print_msg("Saving to {:}".format(save))
        
    return out