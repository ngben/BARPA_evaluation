"""
Function to load data into python using iris. For CMIP6, Functional for the models used in BARPA only. Selects downscaled ensemble member. 


example usage:

cx=iris.Constraint(longitude=lambda x: 90 <= x <= 200)
cy=iris.Constraint(longitude=lambda x: -60 <= x <= 10)
load_iris.load_cmip6("historical","ACCESS-CM2","Amon","pr",dt.datetime(2012,1,1),dt.datetime(2013,1,1),cx&cy,callback = load_iris.dateline_callback)
load_iris.load_barpa_lev1("historical","ACCESS-CM2","month","ua",[2012],cx&cy,plevs=[850,200])

"""


import iris
import numpy as np
import datetime as dt
import os

def dateline_callback(cube,field,filename):
    """
    Callback function to load data either side of the dateline
    """
    cube1 = cube.extract(iris.Constraint(longitude=lambda x: x>=0))
    cube2 = cube.extract(iris.Constraint(longitude=lambda x: x<0))
    cube2.coord('longitude').points = cube2.coord('longitude').points + 360
    if cube2.coord('longitude').has_bounds():
        cube2.coord('longitude').bounds = cube2.coord('longitude').bounds + 360
    return iris.cube.CubeList([cube1,cube2]).concatenate_cube()

def load_cmip6(model,scenario,stream,var,t_s,t_e,Constraints,template=None,lapse=None,regrid_method=iris.analysis.Linear(),callback=None,pr_liquid_equiv=False):
    """
    model:           model name. Must be "ACCESS-CM2", "ACCESS-ESM1-5","NorESM2-MM","NCC","EC-Earth3", "CNRM-ESM2-1"
    scenario:        historical, ssp126, ssp370 etc.
    stream:          CMIP6 time frequency to load. E.g. day, Amon etc.
    t_s:             start time as a datetime object. Note, full months are loaded, so day is ignored/set to 1.
    t_e:             end time as a datetime object. Note, full months are loaded, so day is ignored/set to 1.
    Constraints:     iris loading constraints to apply. e.g. iris.Constraint(longitude=lambda x: 90 <= x <= 200)
    template:        A template to regrid the data to. Needs to be an iris cube.
    lapse:           Apply a lapse rate adjustment when regridding. Assumes the data in 'template' is orography on the new grid. Relevant for surface air temperature only
                     Value should be None or the desired lapse rate (usually 0.006: 6 degrees per km)
    regrid_method:   Method for regridding: 
    callback         Function for iris to apply to each cube while loading. Use this to load continuous data east and west of the dateline
    pr_liquid_equiv: Convert units of rainfall from kg/m2/[time] to mm/[time]
    """
    # data information specific to model
    cmip_info = {"ACCESS-CM2":("CSIRO-ARCCSS","r4i1p1f1",'gn','latest'),"ACCESS-ESM1-5":('CSIRO','r6i1p1f1','gn','latest'),'NorESM2-MM':('NCC','r1i1p1f1','gn','v20191108'),'EC-Earth3':('EC-Earth-Consortium','r1i1p1f1','gr','v20200310'),'CNRM-ESM2-1':("CNRM-CERFACS","r1i1p1f2",'gr',"v20181206")}
    group,rev,grid,date  = cmip_info[model]
    # build filepath
    if scenario == 'historical':
        mip = "CMIP"
    else:
        mip = "ScenarioMIP"
    if model in ['NorESM2-MM','EC-Earth3'] and scenario =='ssp370' and var=='hfls': # missing data
        path = '/scratch/tp28/eh6215/hfls_noresm/'
    else:
        path = "/g/data/r87/DRSv3/CMIP6/{mip}/{group}/{model}/{scenario}/{rev}/{stream}/{var}/{grid}/{date}/".format(mip=mip,scenario=scenario,rev=rev,stream=stream,var=var,group=group,model=model,grid=grid,date=date)
    # identify which files to load based on time period. Should probably use glob instead
    filepart = "{var}_{stream}_{model}_{scenario}_{rev}_{grid}".format(mip=mip,scenario=scenario,rev=rev,stream=stream,var=var,group=group,model=model,grid=grid)
    files = [f for f in os.listdir(path) if filepart in f]
    starts = [f.split("_")[-1].split("-")[0] for f in files]
    ends = [f.split("_")[-1].split("-")[1] for f in files]
    starts = [dt.datetime(int(x[:4]),int(x[4:6]),1) for x in starts]
    ends = [dt.datetime(int(x[:4]),int(x[4:6]),1) for x in ends]
    files = [ os.path.join(path,f) for (i,f) in enumerate(files) if ((t_e  - starts[i]).days >0  and (ends[i] - t_s).days >= 0) ]
    ct = iris.Constraint(time = lambda t: ((dt.datetime(t.point.year,t.point.month,1) - t_s).days >= 0) and ((dt.datetime(t.point.year,t.point.month,1) - t_e).days < 0))
    # load data
    data = iris.load(files,Constraints&ct)
    iris.util.equalise_attributes(data)
    data=data.concatenate_cube()
    if not template is None:
        # if template is supplied, regrid. 
        data.coord('longitude').coord_system = template.coord('longitude').coord_system
        data.coord('latitude').coord_system = template.coord('latitude').coord_system
        data = data.regrid(template,regrid_method)
        if lapse is not None:
            # compute altitude lapse rate correction if provided
            topo_CMIP = iris.load_cube("/g/data/r87/DRSv3/CMIP6/{mip}/{group}/{model}/{scenario}/{rev}/fx/orog/gn/latest/orog_fx_{model}_{scenario}_{rev}_gn.nc".format(mip=mip,scenario=scenario,rev=rev,stream=stream,var=var,group=group,model=model),Constraints,callback)
            topo_CMIP.coord('longitude').coord_system = template.coord('longitude').coord_system
            topo_CMIP.coord('latitude').coord_system = template.coord('latitude').coord_system
            topo_CMIP = topo_CMIP.regrid(template,regrid_method)
            delta = (template - topo_CMIP)*lapse
            delta.convert_units(data.units)
            data.data = data.data + delta.data
    if var=='pr' and pr_liquid_equiv:
        # convert rainfall to liquid water equivalent
        alpha_w = iris.coords.AuxCoord(1/1000.,units='m**3*kg**-1')
        name = data.name()
        data = data*alpha_w
        data.rename(name)
    return data


def load_barpa_lev1(model,scenario,stream,var,years,Constraints=None,plevs='single',pr_liquid_equiv=False):
    """
    model:           model name. 
    scenario:        evaluation,historical, ssp126, ssp370 etc.
    stream:          CMIP6 time frequency to load. E.g. day, Amon etc.
    var:             variable name
    years:           years to load
    Constraints:     iris loading constraints to apply. e.g. iris.Constraint(longitude=lambda x: 90 <= x <= 200)
    plevs:           pressure levels to load. If 'single', loads a single level. Otherwise, provide list of pressure levels 
    pr_liquid_equiv: Convert units of rainfall from kg/m2/[time] to mm/[time]
    """
    #filepath
    ia39path = "/g/data/ia39/australian-climate-service/test-data/CORDEX-CMIP6/output/AUS-15/BOM/*{model}/{scen}/*/BOM-BARPA-R/v1/{stream}/{var}/*{year}01-{year}12.nc"
    #load a single file
    if plevs == 'single':
        data = iris.load([ia39path.format(model=model,scen=scenario,var=var,year = yr) for yr in years])
    else:
        # load multiple levels from different file streams
        p_years = []
            for year in years:
                for p in plevs:
                    p_years.append((year,p))
            data = iris.load([ia39path.format(model=model,scen=scen,var="%s%03d"%(var,p),year = yr) for (yr,p) in plevs])
            for cube in data:
                # var_name varies for different heights, so this is neccessary for merging
                cube.var_name = None
    iris.util.equalise_attributes(tmp)
    data = data.merge().concatenate_cube()
    if plevs != 'single':
        # transpose so that time is first, pressure second
        tmp.transpose((1,0,2,3))
    if var=='pr' and pr_liquid_equiv:
        # convert rainfall to liquid water equivalent
        alpha_w = iris.coords.AuxCoord(1/1000.,units='m**3*kg**-1')
        name = data.name()
        data = data*alpha_w
        data.rename(name)
    return data
        