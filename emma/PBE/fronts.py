import iris
import os
import numpy as np
from skimage.feature import canny
from scipy.ndimage import convolve 
from mpi4py import MPI
import iris.cube
comm = MPI.COMM_WORLD
rank = comm.Get_rank()
size = comm.Get_size()
path = "/g/data/ia39/australian-climate-service/test-data/CORDEX-CMIP6/output/AUS-15/BOM/*{model}/{scen}/*/BOM-BARPA-R/v1/{time}/{var}/*{year}01-{year}12.nc"
outpath = "/scratch/tp28/eh6215/ilamb/ILAMB_sample/MODELS3/BARPA_{model}/fronts/fronts_{year:04d}.nc"

def fronts(year,model,scen,k):
  if os.path.exists(outpath.format(model=model,year=year)):
    return
  out = iris.cube.CubeList()
  for month in range(1,13):
    ct = iris.Constraint(time=lambda t: t.point.month==month and t.point.hour==12)
    t = iris.load_cube(path.format(model=model,scen=scen, time='6hr',var='ta850',year=year),ct)
    nt = t.shape[0]
    C=[canny(t[i].data,3,2,6,(1-t[i].data.mask).astype(bool)) for i in range(nt)]
    C=np.array(C)
    C=t.copy(data=C)
    CC = convolve(C.data,np.ones((1,k,k)),mode='constant', cval=0)[:,::k,::k] > 0
    cube = C[0,::k,::k].copy(data = CC.sum(axis=0))
    out.append(cube)
  iris.util.equalise_attributes(out) 
  out = out.merge_cube()
  iris.save(out,outpath.format(model=model,year=year))

def split(a, n):
    k, m = divmod(len(a), n)
    return list(a[i*k+min(i, m):(i+1)*k+min(i+1, m)] for i in range(n))


models = {"ERA5":         ('evaluation',1979,1990),
          "ACCESS-CM2":   ('historical',1979,1991),
          "ACCESS-ESM1-5":('historical',1960,1971)}
          
runlist = []
for model in models:
    scen, year0, year1 = models[model]
    for year in range(year0,year1):
        runlist.append((model,year,scen))
        
runlist = split(runlist,size)[rank]

for (model,year,scen) in runlist:
    print(model,year)
    fronts(year,model,scen,10)
