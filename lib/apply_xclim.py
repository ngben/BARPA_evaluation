from __future__ import annotations

import xarray as xr
import os
import xclim

"""
Compute monthly xclim indices from daily BARPA and AGCD data
"""


def xclim_for_agcd(indicator,var,agg,years,outpath=None,outname=None):
    """
    indicator: xclim indicator: e.g. xclim.indicators.icclim.RX1day
    var: agcd variable to read. Can be precip,tmin,tmax
    agg: AGCD aggregation: such as total, calib, mean
    years: year range to apply indicator to
    outpath: directory to save output to, or none if output is not to be written
    outname: output file name. If none, name is constructed to be consistent with agcd labelling
    """
    agcdpath = "/g/data/zv2/agcd/v1/{var}/{agg}/r005/01day/agcd_v1_{var}_{agg}_r005_daily_{year}.nc"
    filepaths=[agcdpath.format(var=var,agg=agg,year=yr) for yr in years]
    if len(filepaths)==1:
        filepaths = filepaths[0]
        reader = xr.open_dataset
    elif len(filepaths)>0:
        reader = xr.open_mfdataset
    with reader(filepaths) as DS:
        ds=DS[var]
        if var =='precip':
            ds=ds.assign_attrs(units='mm/day')
        new = indicator(ds,freq='M')
        if outpath is not None:
            if outname==None:
                outname = "agcd_v1_{var}_{agg}_r005_monthly_{year1}01-{year2}12.nc".format(var=new.name,agg=agg,year1=years[0],year2=years[-1])
            new.to_netcdf(os.path.join(outpath1,outname))
    return new
        

def xclim_for_barpa(gcm,indicator,var,scen,years,outpath=None,outname=None):
    """
    gcm: downscaled GCM to compute metric for
    indicator: xclim indicator: e.g. xclim.indicators.icclim.RX1day
    var: agcd variable to read. Can be precip,tmin,tmax
    scen: CMIP experiment. Can be evaluation, historical, ssp126, ssp370
    years: year range to apply indicator to
    outpath: directory to save output to, or none if output is not to be written
    outname: output file name. If none, name is constructed to be consistent with drs labelling
    """
    revisions = {"ERA5":('ECMWF','r1i1p1f1'),"ACCESS-CM2":("CSIRO-BOM","r4i1p1f1"),"ACCESS-ESM1-5":('CSIRO-BOM','r6i1p1f1'),'NorESM2-MM':('NCC','r1i1p1f1'),'EC-Earth3':('EC-Earth-Consortium','r1i1p1f1')}
    ia39path = "/g/data/ia39/australian-climate-service/test-data/CORDEX-CMIP6/output/AUS-15/BOM/{model}/{scen}/{rev}/BOM-BARPA-R/v1/{time}/{var}/{var}_AUS-15_{model}_{scen}_{rev}_BOM-BARPA-R_v1_{time}_{year}01-{year}12.nc"
    centre,rev = revisions[gcm]
    filepaths=[ia39path.format(model=centre+'-'+gcm,scen=scen,time='day',var=var,year=yr,rev=rev) for yr in years]
    if len(filepaths)==1:
        reader = xr.open_dataset
        filepaths=filepaths[0]
    elif len(filepaths)>0:
        reader = xr.open_mfdataset
    with reader(filepaths) as ds:        
        new = indicator(ds[var],freq='M')
        if outpath is not None:
            if outname==None:
                outname = "{var}_AUS-15_{model}_{scen}_{rev}_BOM-BARPA-R_v1_{time}_{year1}01-{year2}12.nc".format(var=new.name,model=gcm,scen=scen,rev=rev,time='month',year1=years[0],year2=years[-1])
            new.to_netcdf(os.path.join(outpath,outname))
    return new
