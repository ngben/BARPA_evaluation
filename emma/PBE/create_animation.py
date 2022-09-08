import iris
import datetime as dt
import os
import iris.plot as iplt
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cmocean
from matplotlib import animation
import numpy as np
from matplotlib.colors import LogNorm
import warnings
from scipy.ndimage import gaussian_filter
#Apr1997, Mar2001, Feb1999

cx = iris.Constraint(longitude=lambda x: 100<=x<=170)
cy = iris.Constraint(latitude=lambda x: -50<=x<=0)

# set the plot elements in the dictionaries below (1 dict per subplot/dataset)
# var: name of variable in drs
# freq: update frequency in hours
# type: matplotlib plot class
# operation: supports basic arithmetic
# mask: mask values below this threshold
# k: for quiver plots, arrow thinning parameter (required, 1=none)
# sigma: gaussian smoothing length (not applied if not present)
# remaining keywords are plot class parameters

access = [{'var':'tas',      'freq':3,'type':'pcolormesh','operation':'sub273.15','vmin':0,'vmax':45,'cmap':'hot_r'},
          {'var':('ua','va'),'freq':6,'type':'quiver','k':1, 'plev':0},
          {'var':'pr',       'freq':3,'type':'pcolormesh','mask':1,'operation':'mul3600','vmin':1,'vmax':10,'cmap':cmocean.cm.rain},
          {'var':'psl',      'freq':24,'type':'contour','operation':'div100','levels':np.arange(950,1051,5),'colors':'k'}] 


barpa = [{'var':'tasmean',        'freq':1,'type':'pcolormesh','operation':'sub273.15','vmin':0,'vmax':45,'cmap':'hot_r'},
         {'var':('ua850','va850'),'freq':6,'type':'quiver','k':10,'sigma':5},
         {'var':'pr',             'freq':1,'type':'pcolormesh','mask':1,'operation':'mul3600','vmin':1,'vmax':10,'cmap':cmocean.cm.rain},
         {'var':'psl',            'freq':1,'type':'contour','operation':'div100','levels':np.arange(950,1051,5),'colors':'k','sigma':5}] 

# path to data 
ia39path = "/g/data/ia39/australian-climate-service/test-data/CORDEX-CMIP6/output/AUS-15/BOM/*ACCESS-CM2/historical/r4i1p1f1/BOM-BARPA-R/v1/{time}/{var}/*{year}01-{year}12.nc"
fs38path = "/g/data/fs38/publications/CMIP6/CMIP/CSIRO-ARCCSS/ACCESS-CM2/historical/r4i1p1f1/{time}/{var}/gn/latest/{var}_{time}_ACCESS-CM2_historical_r4i1p1f1_gn_{year}*.nc"

# data for plots will be saved here unpacked to speed up reading
tmppath = "/scratch/tp28/eh6215/anim_temp/"

# animation will be for the start of this month
year,month=1999,2

# read data from storage (true) or use cached data (false)
GenData=False
         
def prep_casestudy(year,month,path,dictlist,tmppath,Constraints,n=9):
    # reads required data and saves it to tmppath
    freqs = {1:'1hr',3:'3hr',6:'6hr',24:'day'}
    ct = iris.Constraint(time=lambda t:t.point.year==year and t.point.month==month and t.point.day <= n)
    data = iris.cube.CubeList()
    for D in dictlist:
        year1=year
        time = freqs[D['freq']]
        if 'fs38' in path:
            year1 = ("%4d"%(year))[:{'day':2,'3hr':3,'6hr':4,'1hr':4}[time]]  # fudge to deal with multiple years per file in ACCESS-CM2 data
        if 'plev' in D:
            time = time+"PlevPt"
        if type(D['var']) is tuple:
            data.append(iris.load_cube(path.format(var=D['var'][0],time=time,year=year1),Constraints&ct))
            data[-1].rename(D['var'][0])
            data.append(iris.load_cube(path.format(var=D['var'][1],time=time,year=year1),Constraints&ct))
            data[-1].rename(D['var'][1])
            if 'plev' in D:
                data[-2] = data[-2][:,D['plev']]
                data[-1] = data[-1][:,D['plev']]
        else:
            data.append(iris.load_cube(path.format(var=D['var'],time=time,year=year1),Constraints&ct))
            data[-1].rename(D['var'])
            if 'plev' in D:
                data[-1] = data[-1][:,D['plev']]
    iris.save(data,tmppath)
    return data
         

def apply_operation(X,op):
    # helper function to apply offsets and scalings for unit transformations
    if op[:3]=='add':
        return X+float(op[3:])
    elif op[:3]=='sub':
        return X-float(op[3:])
    elif op[:3]=='mul':
        return X*float(op[3:])
    elif op[:3]=='div':
        return X/float(op[3:])
    else:
        exit('could not parse operation')
        
def prep_data(data,D,i):
    #extracts data from cubelists and applies scalings, offsets, masks and smoothing
    if type(D['var']) is tuple:
        X = data.extract_cube(D['var'][0])[i].copy()
        Y = data.extract_cube(D['var'][1])[i].copy()
    else:
        X = data.extract_cube(D['var'])[i].copy()
    if 'operation' in D:
        X = apply_operation(X,D['operation'])
    if 'mask' in D:
        X.data.mask += X.data < D['mask']
    if 'sigma' in D:
        X.data = gaussian_filter(X.data.filled(0),sigma=D['sigma'])
    if type(D['var']) is tuple:
        if 'operation' in D:
            Y = apply_operation(Y,D['operation'])
        if 'mask' in D:
            Y.data.mask += Y.data < D['mask']
        if 'sigma' in D:
            Y.data = gaussian_filter(Y.data.filled(0),sigma=D['sigma'])
        return X,Y
    return X
        
        
def init(ax,dictlist,data):
    # initialise a subplot with data from timestep 0
    plot = []
    for D in dictlist:
        X = prep_data(data,D,0)
        if type(X) is tuple:
           X,Y = X
        lon = X.coord('longitude').points
        lat = X.coord('latitude').points
        if D['type'] == 'pcolormesh':
            dx = lon[1]-lon[0]
            dy = lat[1]-lat[0]
            lon = np.array(list(lon - dx/2)+[lon[-1]+dx/2])
            lat = np.array(list(lat - dy/2)+[lat[-1]+dy/2])
            plot.append(ax.pcolormesh(lon,lat,X.data,vmin=D['vmin'],vmax=D['vmax'],cmap=D['cmap']))
        elif D['type'] == 'contour':
            plot.append(ax.contour(lon,lat,X.data,D['levels'],colors=D['colors']))
        elif D['type'] == 'quiver':
            k=D['k']
            plot.append(ax.quiver(lon[::k],lat[::k],X.data[::k,::k],Y.data[::k,::k]))
    return plot
            
def update_subplot(i,plot,dictlist,ax,data):
    # updates a subplot for timestep i
    for j,D in enumerate(dictlist):
        X = prep_data(data,D,i//D['freq'])
        if D['type'] == 'pcolormesh':
            plot[j].set_array(X.data.flatten())
        elif D['type'] == 'contour':
            lon = X.coord('longitude').points
            lat = X.coord('latitude').points
            for coll in plot[j].collections:
               coll.remove()
            plot[j] = ax.contour(lon,lat,X.data,D['levels'],colors=D['colors'])
        elif D['type'] == 'quiver':
            k=D['k']
            plot[j].set_UVC(X[0][::k,::k].data.flatten(),X[1][::k,::k].data.flatten())
    return plot

def update(i):
    # update figure. Change this function when changing subplot layout 
    global plot_barpa,plot_access
    plot_barpa=update_subplot(i,plot_barpa,barpa,ax1,data_barpa)
    plot_access=update_subplot(i,plot_access,access,ax2,data_access)
    ax1.set_title("%d%02d%02d %02d:00"%(year,month,i//24 + 1, i%24))
    ax2.set_title("%d%02d%02d %02d:00"%(year,month,i//24 + 1, ((i//3)*3)%24))
    return plot_barpa,plot_access

if __name__ == "__main__":
  if GenData:
    # save data to tmppath
    print('preparing barpa')
    prep_casestudy(year,month,ia39path,barpa,tmppath+'barpa.nc',cx&cy)
    print('preparing access')
    prep_casestudy(year,month,fs38path,access,tmppath+'access.nc',cx&cy)
    print('data prepared')

  # load data from tmppath
  data_barpa = iris.load(tmppath+'barpa.nc')
  data_access = iris.load(tmppath+'access.nc')
  print('data loaded')

  # read data into memory
  for cube in data_barpa+data_access:
    cube.data
  print('data realised')

  # initialise data
  fig = plt.figure(figsize=(9,5))
  ax1=plt.subplot(121,projection=ccrs.PlateCarree())
  plot_barpa = init(ax1,barpa,data_barpa)
  ax1.coastlines()
  ax1.set_title("%d%02d%02d"%(year,month,1))
  c=plt.colorbar(plot_barpa[2],orientation='horizontal')
  c.set_label("precip (mm/hr)")

  ax2=plt.subplot(122,projection=ccrs.PlateCarree())
  plot_access = init(ax2,access,data_access)
  ax2.coastlines()
  ax2.set_title("%d%02d%02d"%(year,month,1))
  c=plt.colorbar(plot_access[0],orientation='horizontal')
  c.set_label('Surface Air Temperature (C)')
  print('figure initialised')
  # when setting up a new animation, check the initial frame looks correct 
  #before proceeding with the animation
  #plt.show()   

  # do animation
  anim=animation.FuncAnimation(fig,update,frames=7*24)
  anim.save('barpa.gif',writer='imagemagick',fps=4)
  print('done')

