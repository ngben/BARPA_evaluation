import spatial_selection
import numpy as np
import geopandas as gp
import xarray as xr
import os

def region_aggregation(data,gridname,shapefile = 'NRM_clusters',aggregator='mean',landmask=None):
    """
    Aggregate a data-array over the NRM regions
    default is to take a spatial mean, but other aggregators are available
    Parameters
    ----------
    data: x-array 
        input x-array, must have coordinates lon, lat
    gridname: string
        codename for grid to enable caching of region masks 
    shapefile: string
        indicates shapefile containing regions to aggregate over.
        Should be either a full filepath or one of 'NRM_clusters', 'NRM_sub_clusters', 'NRM_super_clusters'
    aggregator: string
         name of x-array reduction method to apply. Valid entries:
         ['all','any','count','cumprod','cumsum','max','mean','median','min','prod','std','sum','ar']
    landmask: xarray or None
         if not None, binary land-sea mask to apply in addition to regions
    Returns
    -------
      result: x-array
          Aggregated data array
      labels: pandas.Series
          Region labels from shapefile
    """
    assert(aggregator in ['all','any','count','cumprod','cumsum','max','mean','median','min','prod','std','sum','ar'])
    #load shapefile
    if shapefile in ['NRM_clusters', 'NRM_sub_clusters', 'NRM_super_clusters']:
        shapefilepath = '/g/data/tp28/dev/evaluation_datasets/{cluster}/{cluster}.shp'.format(cluster=shapefile)
    else:
        shapefilepath = shapefile
    print('reading shapefile')
    mask = gp.read_file(shapefilepath)
    # extract region names from shapefile
    labels = mask.label
    # define cache path
    ncpath = shapefilepath.strip('.shp')+"_{grid}.nc".format(grid=gridname)
    if os.path.exists(ncpath):
        # if cached version exists, load it
        print('loading cached mask')
        mask_xarray = xr.load_dataset(ncpath).__xarray_dataarray_variable__
        assert (mask_xarray.lon == data.lon).all()
        assert (mask_xarray.lat == data.lat).all()
    else:
        print('creating new mask - may be memory intensive')
        # else, compute it. This is be memory-intensive
        mask_xarray = spatial_selection.centre_mask(mask, data.lon.values, data.lat.values, output="2D")
        mask_xarray.to_netcdf(ncpath)
    if landmask is not None:
        print('applying land-sea mask')
        mask_xarray = mask_xarray * landmask
    # Concatenate regions into 3D xarray
    #regions = xr.concat(
    #                    [(nrm_regrid == region_id).expand_dims(region=[i])
    #                     for i, region_id in enumerate(labels)], 
    #                      dim='region'
    #                   )
    # aggregate data array by region
    print('aggregating')
    result = getattr(data.where(mask_xarray),aggregator)(['lat', 'lon'])   # if aggregator=mean, this is equivanlent to data[var].where(regions).mean(['lat','lon'])
    # now the data is small (8 timeseries), commit to memory
    print('loading data into memory')
    result = result.load()  
    return result,labels

