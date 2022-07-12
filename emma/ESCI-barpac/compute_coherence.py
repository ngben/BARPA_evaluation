#!/g/data3/hh5/public/apps/miniconda3/envs/analysis3-21.10/bin/python

import iris
import numpy as np
import pickle
import os
import asop_coherence

from mpi4py import MPI
comm = MPI.COMM_WORLD
rank = comm.Get_rank()
print(rank)
size = comm.Get_size()
year = rank + 1990

path1 = "/g/data/tp28/BARPA/trials/{domain}*/era/erai/historical/r0/pp_unified/3hourly/av_prcp_rate/0p05deg/{year}/"
path2 = "/scratch/tp28/eh6215/ESCI/3hr_BARPAC-T/"

params = {"BARPAC-M": {'dt':3600*3, 'dx':25, 'dy':25, 'legend_name':'BARPAC-M', 'name':'BARPAC-M', 'region':[-45,-30,140,155], 'box_size':200, 'color':'tab:red',   'region_size':9, 'lag_length':10, 'autocorr_length':60*60*24*5},
          "BARPAC-T": {'dt':3600*3, 'dx':25, 'dy':25, 'legend_name':'BARPAC-T', 'name':'BARPAC-T', 'region':[-45,-30,140,155], 'box_size':200, 'color':'tab:blue', 'region_size':9, 'lag_length':10, 'autocorr_length':60*60*24*5},
          "BARPAR-M": {'dt':3600*3, 'dx':25, 'dy':25, 'legend_name':'BARPAR-M', 'name':'BARPAR-M', 'region':[-30,-10,140,155], 'box_size':200, 'color':'tab:green',  'region_size':9, 'lag_length':10, 'autocorr_length':60*60*24*5},
          "BARPAR-T": {'dt':3600*3, 'dx':25, 'dy':25, 'legend_name':'BARPAR-T', 'name':'BARPAR-T', 'region':[-30,-10,140,155], 'box_size':200, 'color':'tab:orange', 'region_size':9, 'lag_length':10, 'autocorr_length':60*60*24*5}}
          

def calc_coherence(year):
    data ={}
    """
    for name in ["BARPAC-M","BARPAC-T","BARPA-E"]:
        if name in ["BARPAC-M","BARPA-E"]:
            data[name]=iris.load([(path1+"/*_{year:04d}{month:02d}*").format(domain=name,year=year1,month=month) for year1,month in [(year,12),(year+1,1),(year+1,2)]])
        else:
            data[name]=iris.load([(path2+"/*_{year:04d}{month:02d}*").format(domain=name,year=year1,month=month) for year1,month in [(year,12),(year+1,1),(year+1,2)]])
        iris.util.equalise_attributes(data[name])
        data[name]=data[name].concatenate_cube()
        data[name].units = "mm/s"
        data[name].convert_units("mm/day")
        lat=iris.coords.DimCoord({'BARPAC-M':np.arange(-45,-30,0.25),\
                                  'BARPAC-T':np.arange(-30,-10,0.25),\
                                  'BARPA-E' :np.arange(-45,-10,0.25)}[name],standard_name='latitude',units='degrees')
        lon=iris.coords.DimCoord(np.arange(140,155,0.25),standard_name='longitude',units='degrees')
        lat.guess_bounds()
        lon.guess_bounds()
        template = data[name][0,:lat.shape[0],:lon.shape[0]]
        template.remove_coord('latitude')
        template.remove_coord('longitude')
        template.add_dim_coord(lat,0)
        template.add_dim_coord(lon,1)
        try:
            data[name].coord('longitude').coord_system=None
            data[name].coord('latitude').coord_system=None
            data[name].coord('longitude').guess_bounds()
            data[name].coord('latitude').guess_bounds()
        except:
            1
        data[name] = data[name].regrid(template,iris.analysis.AreaWeighted())
    """
    #add_day_of_year(data[name],'time','day')
    #data[name]=data[name].aggregated_by('day',iris.analysis.MEAN)
    bins=[0,0.5,1,2,4,6,9,12,16,20,25,30,40,60,90,130,180,2e20]
    oned_hist,twod_hist,grid_corr={},{},{}
    for region in ['M','T']:
        cy = {'M':iris.Constraint(latitude=lambda x:-45<=x<=-30),"T":iris.Constraint(latitude=lambda x:-30<=x<=-10)}[region]
        cx = iris.Constraint(longitude=lambda x: 140<=x<=155)
        oned_hist['BARPAR_'+region],twod_hist['BARPAR_'+region] = asop_coherence.compute_histogram(data['BARPA-E'].extract(cx&cy),bins)
        oned_hist['BARPAC_'+region],twod_hist['BARPAC_'+region] = asop_coherence.compute_histogram(data['BARPAC-'+region].extract(cx&cy),bins)
    pickle.dump((oned_hist,twod_hist),open('/scratch/tp28/eh6215/ESCI/ASoP/coherence_%d_hist.pickle'%year,'wb'))
    for region in ['M','T']:
        grid_corr['BARPAR_'+region] = asop_coherence.compute_equalgrid_corr(data['BARPA-E'].extract(cx&cy),params['BARPAR-'+region])
        grid_corr['BARPAC_'+region] = asop_coherence.compute_equalgrid_corr(data['BARPAC-M'].extract(cx&cy),params['BARPAC-'+region])
    pickle.dump((grid_corr),open('/scratch/tp28/eh6215/ESCI/ASoP/coherence_%d_corr.pickle'%year,'wb'))
    
print(year)
calc_coherence(year)
