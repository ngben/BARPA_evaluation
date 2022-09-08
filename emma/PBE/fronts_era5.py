import iris
import numpy as np
from skimage.feature import canny
from scipy.ndimage import convolve 
from mpi4py import MPI
import iris.cube
comm = MPI.COMM_WORLD
rank = comm.Get_rank()
size = comm.Get_size()
path = "/g/data/rt52/era5/pressure-levels/reanalysis/t/{year}/t_era5_oper_pl_{year}{month:02d}01-{year}{month:02d}??.nc"

outpath = "/scratch/tp28/eh6215/ilamb/ILAMB_sample/DATA/fronts/era5/fronts_{year:04d}.nc"
cp = iris.Constraint(pressure_level=850)

def fronts(year,k):
  out = iris.cube.CubeList()
  template = iris.load_cube("/home/548/eh6215/orog.nc")
  for month in range(1,13):
    ct = iris.Constraint(time=lambda t: t.point.hour==12)
    t = iris.load_cube(path.format(month=month,year=year),ct&cp)
    t.coord('longitude').coord_system = template.coord('longitude').coord_system
    t.coord('latitude').coord_system = template.coord('latitude').coord_system
    t=t.regrid(template,iris.analysis.Nearest())
    nt = t.shape[0]
    C=[canny(t[i].data,3,2,6) for i in range(nt)]
    C=np.array(C)
    C=t.copy(data=C)
    CC = convolve(C.data,np.ones((1,k,k)),mode='constant', cval=0)[:,::k,::k] > 0
    cube = C[0,::k,::k].copy(data = CC.sum(axis=0))
    out.append(cube)
  iris.util.equalise_attributes(out)
  out = out.merge_cube()
  iris.save(out,outpath.format(year=year))

fronts(rank+1979,10)
