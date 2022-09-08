


import iris
import os
import iris.plot as iplt
import cartopy.crs as ccrs
import matplotlib.pyplot as plt
import numpy as np
import progressbar
from scipy.ndimage import label
from iris.coord_categorisation import add_season, add_month, add_day_of_year
from mpi4py import MPI
import sys


model=sys.argv[1]
comm = MPI.COMM_WORLD
rank = comm.Get_rank()


cx = iris.Constraint(longitude=lambda x: 90<=x<=200)
cy = iris.Constraint(latitude =lambda y:-30<=y<=15)
c_hr = iris.Constraint(time=lambda t: t.point.hour==0)
ia39path = "/g/data/ia39/australian-climate-service/test-data/CORDEX-CMIP6/output/AUS-15/BOM/{model}/{scen}/{rev}/BOM-BARPA-R/v1/{time}/{var}/{var}_AUS-15_{model}_{scen}_r1i1p1f1_BOM-BARPA-R_v1_{time}_{year}01-{year}12.nc"
era5path = "/g/data/rt52/era5/pressure-levels/reanalysis/{var}/{year}/{var}_era5_oper_pl_{year}{month:02d}*.nc"
barrapath = "/g/data/cj37/BARRA/BARRA_R/v1/analysis/prs/{var}/{year}/{month:02d}/{var}-an-prs-PT0H-BARRA_R-v1-{year}{month:02d}??T0000Z.sub.nc"
finalpath="/scratch/tp28/eh6215/PBE/Monsoon_westerlies_hr0/"
outpath = os.environ['PBS_JOBFS']

def MonsoonWesterlies(year,month,data,constraints,outpath):
    if os.path.exists(outpath+"/{data}_{year}{month}.nc".format(data=data,year=year,month=month)):
       return
    if data=='barpa':
        ct= iris.Constraint(time=lambda t: t.point.year==year and t.point.month==month)
        u850 = iris.load_cube(ia39path.format(model='ECMWF-ERA5',scen='evaluation',rev='r1i1p1f1',time='6hr',var='ua850',year=year),constraints&ct) 
        u200 = iris.load_cube(ia39path.format(model='ECMWF-ERA5',scen='evaluation',rev='r1i1p1f1',time='6hr',var='ua200',year=year),constraints&ct)
    elif data == 'era5':
        cp = iris.Constraint(pressure_level=lambda p:p in [200,850])
        u = iris.load(era5path.format(var='u',year=year,month=month),cp&constraints)
        iris.util.equalise_attributes(u)
        u = u.concatenate_cube()
        u200 = u[:,0]
        u850 = u[:,1]
    elif data == 'barra':
        cp = iris.Constraint(pressure=lambda p:np.any([x-0.01<p<x+0.01 for x in [200,850]]))
        u = iris.load(barrapath.format(var='wnd_ucmp',year=year,month=month),cp&constraints)
        iris.util.equalise_attributes(u)
        for cube in u:
           try:
              cube.remove_coord('forecast_reference_time')
              cube.coord('time').attributes.pop('MD5')
           except:
              continue
        try:
            u = u.merge_cube()
        except:
            print('cant merge: ',year,month)
            import pdb;pdb.set_trace()
        u200 = u[:,0]
        u850 = u[:,1]
    u850.data.mask += u200.data > 0
    u850.data= u850.data.filled(0)
    MW=u850.collapsed('time',iris.analysis.PROPORTION,function=lambda x:x>0)
    iris.save(MW,outpath+"/{data}_{year}{month}.nc".format(data=data,year=year,month=month),zlib=True,packing='i2')

for year in np.arange(1990,2007):
        if os.path.exists(finalpath+'/{data}_{year}.nc'.format(data=model,year=year)):
            continue
        month = rank +1 
        print(year,month,model)
        MonsoonWesterlies(year,month,model,cx&cy&c_hr,outpath)
        print(year,month,model,'done')
        comm.Barrier()
        if rank == 0:
            data=iris.load(outpath+"/{data}_{year}{month}.nc".format(data=model,year=year,month='*'))
            iris.util.equalise_attributes(data)
            data=data.merge_cube()
            iris.save(data,finalpath+'/{data}_{year}.nc'.format(data=model,year=year),zlib=True,packing='i2')


