#!/g/data3/hh5/public/apps/miniconda3/envs/analysis3-22.01/bin/python

#PBS -N job_4
#PBS -l walltime=04:00:00
#PBS -q normal
#PBS -P tp28
# PBS -W umask=0007
#PBS -l storage=scratch/tp28+gdata/tp28+gdata/hh5+gdata/access+gdata/dp9+gdata/rt52
#PBS -l mem=16G
#PBS -l jobfs=2G
#PBS -l ncpus=4


import iris
import os
from iris.coord_categorisation import add_day_of_year
import iris.analysis

tmppath = os.environ['PBS_JOBFS']+'/{yearmon}'
outpath = '/g/data/tp28/dev/eh6215/comp/'

def load_aggregate(var,stream,path,yearmon,constraints,aggregators,name=None):
    data= iris.load(os.path.join(path,yearmon,"nc",stream,var+"-*.nc"),constraints)
    iris.util.equalise_attributes(data)
    data = data.concatenate_cube()
    for a in aggregators:
        if a[0]=='collapse':
            data = data.collapsed(a[1],a[2])
        elif a[0] == 'aggregate':
            if a[1] == 'day':
                add_day_of_year(data,'time',a[1])
                data = data.aggregated_by(a[1],a[2])
            else:
                exit(1,'implement')
        else:
            exit(1,'implement')
    if not name is None:
       data.rename(data.name()+name)
    iris.save(data,os.path.join(tmppath.format(yearmon=yearmon),data.name()).replace(" ","_")+".nc")
    return os.path.join(tmppath.format(yearmon=yearmon),data.name()).replace(" ","_")+".nc"
    
def main(exp,year):
  files = []
  path="/g/data/tp28/dev/barpa/prod/"+runs[exp][0]+"/"+exp
  for mon in range(1,13):
    print(exp,year,mon)
    yearmon='%04d%02d01T0000Z'%(year,mon)
    try:
      os.mkdir(tmppath.format(yearmon=yearmon))
    except OSError:
        1
    c_ntb=  iris.Constraint(cube_func = lambda cube:cube.name() !="time_bounds")
    c_p2 = iris.Constraint(pressure=lambda p: p in [200,850])
    c_aus = iris.Constraint(longitude=lambda x: 110<=x<=155)
    c_t6 = iris.Constraint(time=lambda t:t.point.hour in [0,6,12,18])
#    for var,stream in [("av_prcp_rate","SLV1H"),("ttl_col_q","SLV1H"),("av_olr","SLV1H"),("mslp","SLV15M"),('temp_scrn','SLV15M')]:
#        files.append(load_aggregate(var,stream,path,yearmon,c_ntb,[('collapse','time',iris.analysis.MEAN)]))
#    for (name,agg) in [('_min',iris.analysis.MIN), ('_max',iris.analysis.MAX)]:
#        files.append(load_aggregate('temp_scrn','SLV15M',path,yearmon,c_ntb,[('aggregate','day',agg),('collapse','time',iris.analysis.MEAN)],name=name))
#    for var in ['wnd_ucmp','wnd_vcmp']:
#        files.append(load_aggregate(var,'PRS3H',path,yearmon,c_ntb&c_p2,[('collapse','time',iris.analysis.MEAN)]))
    for var in ['wnd_ucmp','wnd_vcmp','omega_uv','air_temp_uv','spec_hum_uv']:
        files.append(load_aggregate(var,'PRS3H',path,yearmon,c_ntb,[('collapse',['time','longitude'],iris.analysis.MEAN)],name='_zm'))
    for var in ['wnd_ucmp','wnd_vcmp','omega_uv','air_temp_uv','spec_hum_uv']:
        files.append(load_aggregate(var,'PRS3H',path,yearmon,c_ntb&c_aus,[('collapse',['time','longitude'],iris.analysis.MEAN)],name='_au'))
  data = iris.load(files)
  iris.util.equalise_attributes(data)
  data=data.merge()
  iris.save(data,outpath+exp+"_ml_%04d.nc"%year,zlib=True)
  for f in files:
    os.remove(f)

runs = {"cg282_ACCESS-CM2_historical_1960_sciB":('eh6215',1961,1969),
        "cg282_ACCESS-CM2_ssp126_2014_sciB":('eh6215',2015,2022),
        "cg282_ACCESS-CM2_ssp370_2014_sciB":('eh6215',2015,2024),
        "cg282_ACCESS-ESM1-5_ssp370_2014_sciB":('cst565',2015,2019),
        "cg282_ERA5_historical_1979_sciB":('chs548',1980,1983)}



for i,exp in enumerate(runs):
  if i==4:
    for year in range(runs[exp][1],runs[exp][2]):
        if not os.path.exists(outpath+exp+"_ml_%04d.nc"%year):
            main(exp,year)

