import iris
import os
from mpi4py import MPI
comm = MPI.COMM_WORLD
i = int(comm.Get_rank())
print(i)


convert = {'ua':'u','va':'v','omega':'w','ta':'t','zg':'z','hus':'q','psl':'msl','tasmean':'2t'}
cx = iris.Constraint(longitude=lambda x:90<=x<=210)
cy = iris.Constraint(latitude=lambda x:-60<=x<=15)

def callback(cube,field,filename):
    cube1 = cube.extract(iris.Constraint(longitude=lambda x: x>=0))
    cube2 = cube.extract(iris.Constraint(longitude=lambda x: x<0))
    cube2.coord('longitude').points = cube2.coord('longitude').points + 360
    if cube2.coord('longitude').has_bounds():
        cube2.coord('longitude').bounds = cube2.coord('longitude').bounds + 360
    return iris.cube.CubeList([cube1,cube2]).concatenate_cube()

def prep_era5_for_ilamb(var):
    try:  # pressure level
        height = int(var[-3:])
        var1 = var[:-3]
    except ValueError:  #not pressure level
        height = None
        var1=var
    if height is None:
        path = "/g/data/rt52/era5/single-levels/monthly-averaged/"+convert[var1]+"/*/*nc"
        data = iris.load(path,cx&cy,callback)
    else:
        cp = iris.Constraint(pressure_level=height)
        path = "/g/data/rt52/era5/pressure-levels/monthly-averaged/"+convert[var1]+"/*/*nc"
        data = iris.load(path,cx&cy&cp,callback)
    iris.util.equalise_attributes(data)
    data=data.concatenate_cube()
    if var1 == 'zg':
        g = iris.coords.AuxCoord(1/9.8,units='s/m2')
        data = data*g
        data.rename("geopotential_height")
    data.coord('longitude').guess_bounds()
    data.coord('latitude').guess_bounds()
    data.coord('time').guess_bounds()
    data.rename(var)
    try:
        os.mkdir("/scratch/tp28/eh6215/ilamb/ILAMB_sample/DATA/"+var)
        os.mkdir("/scratch/tp28/eh6215/ilamb/ILAMB_sample/DATA/"+var+"/era5")
    except:
        1
    iris.save(data,"/scratch/tp28/eh6215/ilamb/ILAMB_sample/DATA/{var}/era5/era5_{var}.nc".format(var=var),zlib=True,packing='i2')
    
    
        
#['hurs','hus600','hus700','huss','omega500','psl','ta300','ta500','ta600','ta700','ta850','tasmean','ua200','ua300','ua500','ua850','va200','va300','va500','va850','zg300','zg500']
variables = ['hus600','hus700','hus850','omega500','ta300','ta500','ta600','ta700','ta850','tasmean','ua200','ua300','ua500','ua850','va200','va300','va500','va850','zg200','zg500','zg850']
print(len(variables))
prep_era5_for_ilamb(variables[i])
prep_era5_for_ilamb(variables[i+11])
