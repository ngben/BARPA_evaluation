import iris
import numpy as np
import datetime as dt
import os
alpha_w = iris.coords.AuxCoord(1/1000.,units='m**3*kg**-1')
cmip_info = {"ACCESS-CM2":("CSIRO-ARCCSS","r4i1p1f1")}
def load_cmip(scenario,model,stream,var,t_s,t_e,Constraints,template=None,lapse=None,regrid_method=iris.analysis.Linear()):
    group,rev  = cmip_info[model]
    if scenario == 'historical':
        mip = "CMIP"
    else:
        mip = "ScenarioMIP"
    path = "/g/data/r87/DRSv3/CMIP6/{mip}/{group}/{model}/{scenario}/{rev}/{stream}/{var}/gn/latest/".format(mip=mip,scenario=scenario,rev=rev,stream=stream,var=var,group=group,model=model)
    filepart = "{var}_{stream}_{model}_{scenario}_{rev}_gn".format(mip=mip,scenario=scenario,rev=rev,stream=stream,var=var,group=group,model=model)
    files = [f for f in os.listdir(path) if filepart in f]
    starts = [f.split("_")[-1].split("-")[0] for f in files]
    ends = [f.split("_")[-1].split("-")[1] for f in files]
    starts = [dt.datetime(int(x[:4]),int(x[4:6]),1) for x in starts]
    ends = [dt.datetime(int(x[:4]),int(x[4:6]),1) for x in ends]
    files = [ os.path.join(path,f) for (i,f) in enumerate(files) if ((t_e  - starts[i]).days >0  and (ends[i] - t_s).days >= 0) ]
    ct = iris.Constraint(time = lambda t: ((dt.datetime(t.point.year,t.point.month,1) - t_s).days >= 0) and ((dt.datetime(t.point.year,t.point.month,1) - t_e).days < 0))
    data = iris.load_cube(files,Constraints&ct)
    if not template is None:
        data.coord('longitude').coord_system = template.coord('longitude').coord_system
        data.coord('latitude').coord_system = template.coord('latitude').coord_system
        data = data.regrid(template,regrid_method)
        if lapse is not None:
            topo_CMIP = iris.load_cube("/g/data/r87/DRSv3/CMIP6/{mip}/{group}/{model}/{scenario}/{rev}/fx/orog/gn/latest/orog_fx_{model}_{scenario}_{rev}_gn.nc".format(mip=mip,scenario=scenario,rev=rev,stream=stream,var=var,group=group,model=model),Constraints)
            topo_CMIP.coord('longitude').coord_system = template.coord('longitude').coord_system
            topo_CMIP.coord('latitude').coord_system = template.coord('latitude').coord_system
            topo_CMIP = topo_CMIP.regrid(template,regrid_method)
            delta = (template - topo_CMIP)*lapse
            delta.convert_units(data.units)
            data.data = data.data + delta.data
    if var=='pr':
        name = data.name()
        data = data*alpha_w
        data.rename(name)
    return data

