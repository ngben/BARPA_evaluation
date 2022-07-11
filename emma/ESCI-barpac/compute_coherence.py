import iris
import numpy as np
from iris.coord_categorisation import add_day_of_year
import iris
import numpy as np
import pickle

from iris.coord_categorisation import add_hour

import os
os.chdir("/home/548/eh6215/Desktop/python/ASoP/ASoP-Coherence")
import asop_coherence

path1 = "/g/data/tp28/BARPA/trials/{domain}*/era/erai/historical/r0/pp_unified/3hourly/av_prcp_rate/0p05deg/{year}/"
path2 = "/short/tp28/eh6215/ESCI/3hr_BARPAC-T/"

params = {"BARPAC-M": {'dt':3600*3, 'dx':5, 'dy':5, 'legend_name':'BARPAC-M', 'name':'BARPAC-M', 'region':[-45,-30,140,155], 'box_size':200, 'color':'tab:red',   'region_size':21, 'lag_length':10, 'autocorr_length':60*60*24*5},
          "BARPAC-T": {'dt':3600*3, 'dx':4, 'dy':4, 'legend_name':'BARPAC-T', 'name':'BARPAC-T', 'region':[-45,-30,140,155], 'box_size':200, 'color':'tab:blue', 'region_size':21, 'lag_length':10, 'autocorr_length':60*60*24*5},
          "BARPAR-M": {'dt':3600*3, 'dx':5, 'dy':5, 'legend_name':'BARPAR-M', 'name':'BARPAR-M', 'region':[-30,-10,140,155], 'box_size':200, 'color':'tab:green',  'region_size':21, 'lag_length':10, 'autocorr_length':60*60*24*5},
          "BARPAR-T": {'dt':3600*3, 'dx':4, 'dy':4, 'legend_name':'BARPAR-T', 'name':'BARPAR-T', 'region':[-30,-10,140,155], 'box_size':200, 'color':'tab:orange', 'region_size':21, 'lag_length':10, 'autocorr_length':60*60*24*5}}
          

def calc_coherence(year):
    data ={}
    for name in ["BARPAC-M","BARPAC-T","BARPA-E"]:
        if name in ["BARPAC-M","BARPA-E"]:
            data[name]=iris.load([(path1+"/*_{year:04d}{month:02d}*").format(domain=name,year=year1,month=month) for year1,month in [(year,12),(year+1,1),(year+1,2)]])
        else:
            data[name]=iris.load([(path2+"/*_{year:04d}{month:02d}*").format(domain=name,year=year1,month=month) for year1,month in [(year,12),(year+1,1),(year+1,2)]])
        iris.util.equalise_attributes(data[name])
        data[name]=data[name].concatenate_cube()
        data[name].units = "mm/s"
        data[name].convert_units("mm/day")
    #add_day_of_year(data[name],'time','day')
    #data[name]=data[name].aggregated_by('day',iris.analysis.MEAN)
    bins=[0,0.5,1,2,4,6,9,12,16,20,25,30,40,60,90,130,180,2e20]
    oned_hist,twod_hist,grid_corr={},{},{}
    for region in ['M','T']:
        cy = {'M':iris.Constraint(latitude=lambda x:-45<=x<=-30),"T":iris.Constraint(latitude=lambda x:-30<=x<=-10)}[region]
        cx = iris.Constraint(longitude=lambda x: 140<=x<=155)
        oned_hist['BARPAR_'+region],twod_hist['BARPAR_'+region] = asop_coherence.compute_histogram(data['BARPA-E'].extract(cx&cy),bins)
        oned_hist['BARPAC_'+region],twod_hist['BARPAC_'+region] = asop_coherence.compute_histogram(data['BARPAC-'+region].extract(cx&cy),bins)
        grid_corr['BARPAR_'+region] = asop_coherence.compute_equalgrid_corr(data['BARPA-E'].extract(cx&cy),params['BARPAR-'+region])
        grid_corr['BARPAC_'+region] = asop_coherence.compute_equalgrid_corr(data['BARPAC-M'].extract(cx&cy),params['BARPAC-'+region])
    pickle.dump((oned_hist,twod_hist,grid_corr),open('/scratch/tp28/eh6215/ESCI/ASoP/coherence_%d.pickle'%year,'wb'))
    
for year in range(1995,2016):
    print(year)
    calc_coherence(year)
