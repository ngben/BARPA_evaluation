from __future__ import annotations

import xarray as xr
import os
import xclim
import cmip6_interface
from datetime import datetime as dt
import era5_interface

"""
Compute monthly xclim indices from daily BARPA, AGCD, CMIP6 and GPCC data, and hourly ERA5 data.
"""


def get_name(indicator):
    if 'identifier' in dir(indicator):
        return indicator.identifier
    else:
        return indicator.__name__
    
def xclim_for_agcd(indicator, var, agg, years, outpath=None, outname=None):
    """
    indicator: xclim indicator: e.g. xclim.indicators.icclim.RX1day
    var: agcd variable to read. Can be precip,tmin,tmax
    agg: AGCD aggregation: such as total, calib, mean
    years: year range to apply indicator to
    outpath: directory to save output to, or none if output is not to be written
    outname: output file name. If none, name is constructed to be consistent with agcd labelling
    """
    agcdpath = "/g/data/zv2/agcd/v1/{var}/{agg}/r005/01day/agcd_v1_{var}_{agg}_r005_daily_{year}.nc"
    metric = get_name(indicator)
    
    if type(years) == int:
        years = [years]
        
    filepaths = [agcdpath.format(var=var, agg=agg, year=yr) for yr in years]

    if len(filepaths) == 1:
        filepaths = filepaths[0]
        reader = xr.open_dataset
    elif len(filepaths) > 0:
        reader = xr.open_mfdataset

    with reader(filepaths) as DS:
        ds=DS[var]
        if var == 'precip':
            ds=ds.assign_attrs(units='mm/day')

        new = indicator(ds, freq='M')

        if outpath is not None:
            if outname is None:
                outname = "{metric}.agcd_v1_{var}_{agg}_r005_monthly_{year1}01-{year2}12.nc".format(metric=metric, var=new.name, agg=agg, year1=years[0], year2=years[-1])
            outfile = os.path.join(outpath, outname)
            new.to_netcdf(outfile)
            print("Written to {:}".format(outfile))
    return new
        

def xclim_for_barpa(gcm, indicator, var, scen, years, outpath=None, outname=None):
    """
    gcm: downscaled GCM to compute metric for
    indicator: xclim indicator: e.g. xclim.indicators.icclim.RX1day
    var: BARPA DRS variable to read. Can be pr, tasmax, tasmin
    scen: CMIP experiment. Can be evaluation, historical, ssp126, ssp370
    years: year range to apply indicator to
    outpath: directory to save output to, or none if output is not to be written
    outname: output file name. If none, name is constructed to be consistent with drs labelling
    """
    metric = get_name(indicator)
    if type(years) == int:
        years = [years]
        
    revisions = {"ERA5":('ECMWF','r1i1p1f1'),
                "ACCESS-CM2":("CSIRO-BOM","r4i1p1f1"),
                "ACCESS-ESM1-5":('CSIRO-BOM','r6i1p1f1'),
                'NorESM2-MM':('NCC','r1i1p1f1'),
                'EC-Earth3':('EC-Earth-Consortium','r1i1p1f1')}

    ia39path = "/g/data/ia39/australian-climate-service/test-data/CORDEX-CMIP6/output/AUS-15/BOM/{model}/{scen}/{rev}/BOM-BARPA-R/v1/{time}/{var}/{var}_AUS-15_{model}_{scen}_{rev}_BOM-BARPA-R_v1_{time}_{year}01-{year}12.nc"

    centre,rev = revisions[gcm]
    filepaths = [ia39path.format(model=centre+'-'+gcm, scen=scen, time='day', var=var, year=yr, rev=rev) for yr in years]

    if len(filepaths) == 1:
        reader = xr.open_dataset
        filepaths = filepaths[0]

    elif len(filepaths)>0:
        reader = xr.open_mfdataset

    with reader(filepaths) as ds:        
        new = indicator(ds[var], freq='M')

        if outpath is not None:
            if outname is None:
                outname = "{metric}.barpa_{var}_AUS-15_{model}_{scen}_{rev}_BOM-BARPA-R_v1_{time}_{year1}01-{year2}12.nc".format(metric=metric, var=new.name, model=gcm, scen=scen, rev=rev, time='month', year1=years[0], year2=years[-1])

            new.to_netcdf(os.path.join(outpath, outname))

    return new

def xclim_for_gpcc(indicator, years, res="g10", outpath=None, outname=None):
    """
    indicator: xclim indicator: e.g. xclim.indicators.icclim.RX1day
    years: year range to apply indicator to
    res: resolution, either g10, g05, g25, etc
    outpath: directory to save output to, or none if output is not to be written
    outname: output file name. If none, name is constructed to be consistent with gpcc labelling
    """
    metric = get_name(indicator)
    var = 'precip'
    version = "v2020"
    gpccpath = '/g/data/ia39/aus-ref-clim-data-nci/gpcc/data/full_data_daily_{version}/{res}/full_data_daily_{version}_{res0}_{year}.nc'
    
    if type(years) == int:
        years = [years]
        
    filepaths = [gpccpath.format(res=res, res0=res[1:], version=version, year=yr) for yr in years]

    if len(filepaths) == 1:
        filepaths = filepaths[0]
        reader = xr.open_dataset
    elif len(filepaths) > 0:
        reader = xr.open_mfdataset

    with reader(filepaths) as DS:
        ds = DS[var]
        ds = ds.assign_attrs(units='mm/day')

        new = indicator(ds, freq='M')

        if outpath is not None:
            if outname is None:
                outname = "{metric}.gpcc_{version}_{res}_monthly_{year1}01-{year2}12.nc".format(metric=metric, version=version, res=res, year1=years[0], year2=years[-1])
            outfile = os.path.join(outpath, outname)
            new.to_netcdf(outfile)
            print("Written to {:}".format(outfile))
    return new

def xclim_for_cmip6(gcm, indicator, var, scen, years, outpath=None, outname=None):
    """
    gcm: GCM name to compute for, e.g., ACCESS-CM2, ACCESS-ESM1-5, EC-Earth3
    indicator: xclim indicator: e.g. xclim.indicators.icclim.RX1day
    var: variable name
    scen: CMIP experiment. Can be evaluation, historical, ssp126, ssp370
    years: year range to apply indicator to
    outpath: directory to save output to, or none if output is not to be written
    outname: output file name. If none, name is constructed to be consistent with cmip6 labelling
    """
    metric = get_name(indicator)
    if type(years) == int:
        years = [years]
        
    freq = 'day'
    tstart = dt(years[0], 1, 1, 0)
    tend = dt(years[-1], 12, 31, 23, 59)
    filepaths = cmip6_interface.get_cmip6_files(gcm, scen, freq, var, trange=(tstart, tend))
    print(filepaths)
    
    if len(filepaths) == 1:
        filepaths = filepaths[0]
        reader = xr.open_dataset
    elif len(filepaths) > 0:
        reader = xr.open_mfdataset

    with reader(filepaths) as DS:
        ds = DS[var].sel(time=slice(tstart, tend))
        new = indicator(ds, freq='M')

        if outpath is not None:
            if outname is None:
                outname = "{metric}.{gcm}_{var}_{scen}_monthly_{year1}01-{year2}12.nc".format(metric=metric, gcm=gcm, var=var, scen=scen, year1=years[0], year2=years[-1])
            outfile = os.path.join(outpath,outname)
            new.to_netcdf(outfile)
            print("Written to {:}".format(outfile))
    return new

def xclim_for_era5(indicator, stream, var, operation, years, outpath=None, outname=None):
    """
    indicator: xclim indicator: e.g. xclim.indicators.icclim.RX1day
    stream: single-levels or pressure-levels
    var: variable name
    operation: xarray operation as a str, e.g., "resample(time="1D").sum()"
    years: year range to apply indicator to
    outpath: directory to save output to, or none if output is not to be written
    outname: output file name. If none, name is constructed to be consistent with era5 labelling
    """
    metric = get_name(indicator)
    if type(years) == int:
        years = [years]
        
    tstart = dt(years[0], 1, 1, 0)
    tend = dt(years[-1], 12, 31, 23, 59)
    freq = 'reanalysis'
    
    filepaths = era5_interface.get_era5_files(stream, freq, var, trange=(tstart, tend))

    if len(filepaths) == 1:
        filepaths = filepaths[0]
        reader = xr.open_dataset
    elif len(filepaths) > 0:
        reader = xr.open_mfdataset

    with reader(filepaths) as DS:
        ds = DS[var]

        ds_daily = eval("ds.%s" % operation)
        print(ds_daily)
        
        if var == "mtpr":
            ds_daily = ds_daily.assign_attrs(units='mm s-1')
            print(ds_daily.attrs)
            
        new = indicator(ds_daily, freq='M')

        if outpath is not None:
            if outname is None:
                outname = "{metric}.era5_{stream}_{var}_monthly_{year1}01-{year2}12.nc".format(metric=metric, stream=stream, var=var, year1=years[0], year2=years[-1])
            outfile = os.path.join(outpath, outname)
            new.to_netcdf(outfile)
            print("Written to {:}".format(outfile))
    return new
