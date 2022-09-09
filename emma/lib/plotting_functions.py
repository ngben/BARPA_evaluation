import iris
import matplotlib.pyplot as plt
import iris.plot as iplt
import cartopy.crs as ccrs
import numpy as np
from iris.coord_categorisation import add_month, add_season

"""
plotting functions for figures in BRR069


These are pretty specific and clunky, especially the second two. Could be easier to start again
"""


def bias_plots(data,var,mask,keys,vmin,vmax,vdiff,cmap1,cmap2,units,offset=0,Constraints=None,lognorm=False):
    """
    makes a upper-diagonal matrix plot showing the difference between obs and models
      data: dictionary of model data to compare. Can be double nested with data[model][var] = cubes, or single with data[model] = cubes
      var: name of variable to compare. If data is a 2-nested dictionary, var should be in the second-level keys
      mask: 2d numpy array for masking the data. set to np.zeros(ny,nx) if no mask is to be used
      keys: model names for plot. Should be subset of data.keys(). Can be used to control order of subplots
      vmin: min colormap value for diagonal plots
      vmax: max colormap value for diagonal plots
      vdiff: colormap amplitude for off-diagonal difference plots (these have a symmetric colorbar)
      cmap1: colormap for full diagonal plots
      cmap2: colormap for off-diagonal plots
      units: units to convert all cubes to
      offset: central_longitude for platecarree projection. Set to 180 if dateline is to be included in plot
      Constraints: spatial subset via iris constraints
      Lognorm: if true, apply log scaling to color axis
      ...
    """ 
    if lognorm:
        from matplotlib.colors import LogNorm
    n = len(keys)
    means = {}
    if Constraint is None:
        Constraint = iris.Constraint(cube_func = lambda cube:1)
    for trial in keys:
        # calculate time means for each variable if neccessary, and flatten dictionary
        if type(data[trial]) is dict:
            tmp = data[trial][var].extract(Constraints)
        else:
            tmp = data[trial].extract(Constraints)
        if tmp.ndim == 3:
            tmp=tmp.collapsed('time',iris.analysis.MEAN)
        means[trial] = tmp
    for i,trial1 in enumerate(keys):
        for j,trial2 in enumerate(keys):
            if i==j:
                # diagonal plots show full field values
                cube = means[trial1]
                cube.convert_units(units)
                cube.data = np.ma.masked_array(cube.data,mask)
                ax=plt.subplot(n,n,n*i+j+1,projection=ccrs.PlateCarree(offset))
                if lognorm:
                    iplt.pcolormesh(cube,vmin=vmin,vmax=vmax,cmap=cmap1,norm=LogNorm())
                else:
                    iplt.pcolormesh(cube,vmin=vmin,vmax=vmax,cmap=cmap1)
                plt.colorbar()
                ax.coastlines(zorder=6)
                plt.title(trial1)
            elif i<j:
                # off-diagonal plots show differences
                cube1 = means[trial1]
                cube1.convert_units(units)
                cube1.data = np.ma.masked_array(cube1.data,mask)
                cube2 = means[trial2]
                cube2.convert_units(units)
                cube2.data = np.ma.masked_array(cube2.data,mask)
                rmse = np.sqrt(((cube1 - cube2)**2).collapsed(['latitude','longitude'],iris.analysis.MEAN).data)
                ax=plt.subplot(n,n,n*i+j+1,projection=ccrs.PlateCarree())
                iplt.pcolormesh(cube1-cube2,vmin=-vdiff,vmax=vdiff,cmap=cmap2)
                # title label contains spatial RMSE difference
                plt.title("%s - %s (%.2f)"%(trial1,trial2,rmse))
                ax.coastlines(zorder=6)
                plt.colorbar()
    plt.suptitle(var)

def ts_bias_rmse_plots(data,plottype,var,mask,keys,ref_key,units,Constraint=None):
    """
    plot seasonal timeseries of RMSE error
      data: dictionary of containing data cubes to plot. Can be double nested with data[model][var] = cubes, or single with data[model] = cubes
      plottype: either 'bias' or 'rmse'
      var: variable name for double-nested dictionary
      mask: mask to apply. I think it should be 1 for no mask, or else a masked cube of 1s outside of the masked area
      keys: the data dictionary keys for the models to include in the plot
      ref_key: the data dictionary key for the reference dataset
      units: units to convert all cubes to
      Constraints: spatial subset via iris constraints
    """
    assert plottype in ['bias','rmse']
    n = len(keys)
    if Constraint is None:
        Constraint = iris.Constraint(cube_func = lambda cube:1)
    if type(data[refkey])==dict:
        ref = data[ref_key][var]
    else:
        ref = data[ref_key]
    ref.convert_units(units)
#    ref.data = np.ma.masked_array(ref.data,mask[np.newaxis]*np.zeros(ref.shape))
    if not 'month' in [c.name() for c in ref.coords()]:
        add_month(ref,'time','month')
    ref = ref.aggregated_by('month',iris.analysis.MEAN)
    ref.remove_coord('time')
    ref = (ref*mask).extract(Constraint)
    for i,trial in enumerate(keys):
        if type(data[trial])==dict:
            cube = data[trial][var] 
        else:
            cube = data[trial]
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
    """
    plot seasonal bias maps
    refdata: 3D gridded observational dataset 
    data: cubelist of model data to compare with refdata
    template: 2D cube to regrid data onto 
    vdiff: color bar amplitude
    cmap: colormap
    labels: plot titles
    """
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


