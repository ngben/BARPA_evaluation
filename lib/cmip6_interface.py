"""
 Interface to extract the CMIP6 data. Only works for the models used in
 BAPRA experiments so far.
"""

import os, sys
import iris
import iris.cube
import xarray as xr
from datetime import datetime as dt
from datetime import timedelta as delt
import glob
import calendar
import numpy as np
import cftime

#
# Default values
#
# Root directory path
_DATA_ROOTDIR = '/g/data/r87/DRSv3/CMIP6'
_DEFAULT_MIP = 'ScenarioMIP'
_HIST_MIP = 'CMIP'
# _GCM_ENS has the originating-centre, realisation identifier, historical version, ssp version
_GCM_ENS = {'ACCESS-CM2': ('CSIRO-ARCCSS', 'r4i1p1f1', 'v20210921', 'v20210921'),
            'ACCESS-ESM1-5': ('CSIRO', 'r6i1p1f1', 'v20200529', 'v20211213'),
            'EC-Earth3': ('EC-Earth-Consortium', 'r1i1p1f1', 'v20200310', 'v20200310')}

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
            return dt(y, m, 1, 0, 0)
        else:
            return dt(y, m, 12, 23, 59, 59)
        
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
        
def screen_files(files, trange=(None, None)):
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
        timerange = os.path.splitext(bn)[0].split("_")[-1]
        t0 = str2dt(timerange.split("-")[0], start=True)
        t1 = str2dt(timerange.split("-")[1], start=False)
        #print("{:},{:} v {:},{:}".format(t0, t1, tstart, tend))
        if t1 < tstart:
            #print("{:} < {:}".format(t1, tstart))
            continue
        if t0 > tend:
            continue
        files_filt.append(file)
    
    files_filt.sort()
    
    return files_filt

def choose_directory(gcm, scenario, datadirs):
    if len(datadirs) == 1:
        return datadirs[0]
    
    index = 2 if scenario == 'historical' else 3
    version = _GCM_ENS[gcm][index]
    if version is None:
        'latest'
        
    for datadir in datadirs:
        b = os.path.basename(datadir)
        if b == version:
            return datadir
        
    return None
        
def get_cmip6_files(gcm, scenario, freq, var, trange=(None, None), rootdir=None, ens=None):
    """
    Returns all the matching files.

    Parameters
    ----------
    gcm: str
        GCM name
    scenario: str
        historical, ssp*, evaluation
    freq: str
        1hr, day, mon, etc
    var: str
        variable name
    trange: tuple or an array of datetime objects (optional)
        Time range
    rootdir: str (optional)
        Root directory to find the data
    ens: str (optional)
        Realisation, e.g., r1i1p1f1

    Returns
    -------
    A list of string
        A list of matching filenames
    """
    # Construct the file paths
    
    assert gcm in _GCM_ENS.keys(), "Unknown gcm. Need to update _GCM_ENS"
    mip = _HIST_MIP if scenario == 'historical' else _DEFAULT_MIP
    
    assert freq in ['15min', '1hr' , '3hr', '6hr', 'day', 'mon'], "Unknown freq"
    
    if rootdir is None:
        rootdir = _DATA_ROOTDIR
    
    if ens is None:
        ens = _GCM_ENS[gcm][1]
        
    datadir = os.path.join(rootdir, mip, _GCM_ENS[gcm][0], gcm, scenario, ens)
    freq_list = [v for v in os.listdir(datadir) if os.path.isdir(os.path.join(datadir, v)) ]
    assert freq in freq_list, "Cannot find freq={:} in {:}".format(freq, datadir)
    
    datadir = os.path.join(datadir, freq)
    var_list = [v for v in os.listdir(datadir) if os.path.isdir(os.path.join(datadir, v)) ]
    assert var in var_list, "Cannot find var={:} in {:}".format(var, datadir)
    
    datadirs = glob.glob(os.path.join(datadir, var, 'g*', '*'))
    print_msg("Directories found are: {:}".format(datadirs))
    datadir = choose_directory(gcm, scenario, datadirs)
    
    assert datadir is not None, "Cannot resolve multiple directories: {:}".format(datadirs)
    print_msg("Looking at files in {:}".format(datadir))
    
    # Find all the files within the time range
    files = glob.glob(os.path.join(datadir, '%s_*.nc' % var))
    files.sort()
    files = screen_files(files, trange=trange)
    
    return files

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

def get_calendar(f):
    """
    Returns the calendar name in the given netcdf file.

    Parameters
    ----------
    file: str
        Path to the file

    Returns
    -------
    str
        Name of the calendar type in this file
    """
    cube = iris.load(f)
    return cube[0].coords('time')[0].units.calendar
    
def get_cmip6(gcm, scenario, freq, var, 
                trange=(None, None), latrange=(None, None), lonrange=(None, None),
                rootdir=None, ens=None,
                save=None,
                as_iris=True,
                verbose=True):
    """
    Extract CMIP6 data, in iris.Cube or xarray.Dataset
    
    Parameters
    ----------
    gcm: str
        GCM name
    scenario: str
        historical, ssp*, evaluation
    freq: str
        1hr, day, mon, etc
    var: str
        variable name
    trange: tuple or an array of datetime objects (optional)
        Time range
    latrange: tuple or an array of floats
        Latitude range
    lonrange: tuple or an array of floats
        Longitude range
    rootdir: str (optional)
        Root directory to find the data
    ens: str (optional)
        Realisation, e.g., r1i1p1f1
    save: str (optional)
        Path to an output netcdf file if writing the extracted data
    as_iris: boolean (optional)
        Whether to return as iris.Cubes or xarray.Dataset
    verbose: boolean (optional)
        Whether to be verbose with the operation

    Returns
    -------
    iris.Cubes or xarray.Dataset
        Extracted data
    """
    _VERBOSE = verbose 
    files = get_cmip6_files(gcm, scenario, freq, var, trange=trange, rootdir=rootdir, ens=ens)
    print_msg("Found {:} files".format(len(files)))
    [print_msg(os.path.basename(f)) for f in files]
    
    latmin = -90  if latrange[0] is None else latrange[0]
    latmax = 90   if latrange[1] is None else latrange[1]
    lonmin = -360 if lonrange[0] is None else lonrange[0]
    lonmax = 360  if lonrange[1] is None else lonrange[1]
    
    cal = get_calendar(files[0])
    if 'gregorian' in cal:
        tstart = dt(1900, 1, 1) if trange[0] is None else trange[0]
        tend = dt(2200, 1, 1) if trange[1] is None else trange[1]
    elif '360' in cal:
        tstart = cftime.Datetime360Day(1900, 1, 1) if trange[0] is None else cftime.Datetime360Day(trange[0].year, trange[0].month, trange[0].day, trange[0].hour)
        tend = cftime.Datetime360Day(2200, 1, 1) if trange[0] is None else cftime.Datetime360Day(trange[1].year, trange[1].month, trange[1].day, trange[1].hour)
    elif '365' in cal:
        tstart = cftime.DatetimeAllLeap(1900, 1, 1) if trange[0] is None else cftime.DatetimeAllLeap(trange[0].year, trange[0].month, trange[0].day, trange[0].hour)
        tend = cftime.DatetimeAllLeap(2200, 1, 1) if trange[0] is None else cftime.DatetimeAllLeap(trange[1].year, trange[1].month, trange[1].day, trange[1].hour)
    
    if as_iris:
        cx = iris.Constraint(longitude=lambda x: lonmin<=x<=lonmax)
        cy = iris.Constraint(latitude=lambda x: latmin<=x<=latmax)
        ct = iris.Constraint(time=lambda x: tstart<=x.point<=tend)
        
        out = iris.cube.CubeList([])
        for file in files:
            print_msg("Opening {:}".format(file))
            data = iris.load(file, ct&cx&cy)
            iris.util.equalise_attributes(data)
            data = data.concatenate_cube()
            out.append(data)
        
        iris.util.equalise_attributes(out)
        out = out.concatenate()
        print_msg(str(out))
    
        if save is not None:
            iris.save(out, save,zlib=True)
            print_msg("Saving to {:}".format(save))
    else:
        ds = xr.open_mfdataset(files)
        #ds.coords['longitude'] = (ds.coords['longitude'] + 360) % 360
        #ds = ds.sortby(ds.longitude)
        #ds = ds.sortby(ds.latitude)
        out = ds.sel(time=slice(tstart, tend), latitude=slice(latmin, latmax), longitude=slice(lonmin, lonmax))
    
        if save is not None:
            out.to_netcdf(save)
            print_msg("Saving to {:}".format(save))
        
    return out