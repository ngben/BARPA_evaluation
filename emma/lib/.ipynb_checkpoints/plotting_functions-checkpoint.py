import iris
import matplotlib.pyplot as plt
import iris.plot as iplt
import cartopy.crs as ccrs
import numpy as np
from iris.coord_categorisation import add_month, add_season

def bias_plots(data,var,mask,keys,vmin,vmax,vdiff,cmap1,cmap2,units,offset=0,Constraints=None):
  n = len(keys)
  means = {}
  for trial in keys:
    means[trial] = data[trial][var].extract(Constraints).collapsed('time',iris.analysis.MEAN)
  for i,trial1 in enumerate(keys):
    for j,trial2 in enumerate(keys):
      if i==j:
          cube = means[trial1]
          cube.convert_units(units)
          cube.data = np.ma.masked_array(cube.data,mask)
          ax=plt.subplot(n,n,n*i+j+1,projection=ccrs.PlateCarree(offset))
          iplt.pcolormesh(cube,vmin=vmin,vmax=vmax,cmap=cmap1)
          plt.colorbar()
          ax.coastlines(zorder=6)
          plt.title(trial1)
      elif i<j:
          cube1 = means[trial1]
          cube1.convert_units(units)
          cube1.data = np.ma.masked_array(cube1.data,mask)
          cube2 = means[trial2]
          cube2.convert_units(units)
          cube2.data = np.ma.masked_array(cube2.data,mask)
          rmse = np.sqrt(((cube1 - cube2)**2).collapsed(['latitude','longitude'],iris.analysis.MEAN).data)
          ax=plt.subplot(n,n,n*i+j+1,projection=ccrs.PlateCarree())
          iplt.pcolormesh(cube1-cube2,vmin=-vdiff,vmax=vdiff,cmap=cmap2)
          plt.title("%s - %s (%.2f)"%(trial1,trial2,rmse))
          ax.coastlines(zorder=6)
          plt.colorbar()
  plt.suptitle(var)

def ts_bias_rmse_plots(data,plottype,var,mask,keys,ref_key,units,Constraint=None):
  assert plottype in ['bias','rmse']
  n = len(keys)
  if Constraint is None:
      Constraint = iris.Constraint(cube_func = lambda cube:1)
  ref = data[ref_key][var]
  ref.convert_units(units)
#  ref.data = np.ma.masked_array(ref.data,mask[np.newaxis]*np.zeros(ref.shape))
  if not 'month' in [c.name() for c in ref.coords()]:
    add_month(ref,'time','month')
  ref = ref.aggregated_by('month',iris.analysis.MEAN)
  ref.remove_coord('time')
  ref = (ref*mask).extract(Constraint)
  for i,trial in enumerate(keys):
    cube = data[trial][var] 
    cube.convert_units(units)
    cube = (cube*mask).extract(Constraint)
    if not "month" in [c.name() for c in cube.coords()]:
      add_month(cube,'time','month')
    cube = cube.aggregated_by('month',iris.analysis.MEAN)
    cube.remove_coord('time')
    if plottype=='bias':
      bias = ((cube-ref)).collapsed(['longitude','latitude'],iris.analysis.MEAN)
      iplt.plot(bias,label=trial)
    elif plottype=='rmse':
      rmse = ((cube-ref)**2).collapsed(['longitude','latitude'],iris.analysis.MEAN)**0.5
      iplt.plot(rmse,label=trial)
    plt.xticks(range(12),["J","F","M","A","M","J","J","A","S","O","N","D"])
  plt.legend()

def season_bias(refdata,data,template,vdiff,cmap,labels):
    ref = refdata.aggregated_by('seas',iris.analysis.MEAN)
    ref = ref.regrid(template,iris.analysis.AreaWeighted())
    c = {}
    n = len(data)
    for j,cube in enumerate(data):
        cube = cube.aggregated_by('seas',iris.analysis.MEAN)
        cube = cube.regrid(ref,iris.analysis.AreaWeighted())
        for i in range(4):
            ax=plt.subplot(4,n,j+1+n*i,projection=ccrs.PlateCarree(180))
            a=iplt.pcolormesh(cube[i]-ref[i],vmin=-vdiff,vmax=vdiff,cmap=cmap)
            if j==0:
              c[i]=iplt.contour(cube[i],5,colors='k')
            else:
              iplt.contour(cube[i],c[i].levels,colors='k')
            rmse = (((cube[i]-ref[i])**2).collapsed(['longitude','latitude'],iris.analysis.MEAN)**0.5/ref[i].collapsed(['longitude','latitude'],iris.analysis.STD_DEV)).data
            plt.title("%s (%0.2f)"%(labels[j],rmse))
            plt.colorbar(a)
            ax.coastlines()


