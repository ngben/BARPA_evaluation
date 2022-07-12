import iris
import warnings
import iris.plot as iplt
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
from scipy.stats import ks_2samp
import numpy as np
import cmocean
from scipy.stats import ttest_rel
def fxn():
    warnings.warn("user", UserWarning)

warnings.simplefilter("ignore")
fxn()

def ks(data1,data2):
    nt,ny,nx = data1.shape
    return [[ np.nan if data1.mask[0,i,j] else ks_2samp(data1[:,i,j],data2[:,i,j]).statistic  for j in range(nx)] for i in range(ny)]

trials = {'r2':'cg282_ACCESS-CM2_historical_1979_r4p','r6':'cg282_ACCESS-CM2_historical_1979_r6p','agcd':'agcd_tot','ACCESS-CM2':'CM2'}
path = '/scratch/tp28/eh6215/daily/{trial}/{year:04d}*.nc'
years  = np.arange(1980,1990)
cx = iris.Constraint(longitude=lambda x: 110<=x<=155)
cy = iris.Constraint(latitude =lambda y: -45<=y<=-10)

data = {}
for trial in ['r2','agcd']:
    print(trial) 
    data[trial]=iris.load([path.format(trial=trials[trial],year=year) for (year) in years])
    iris.util.equalise_attributes(data[trial])
    data[trial]=data[trial].concatenate()

data['agcd'][0].units='mm/day'

path_drs = "/g/data/tp28/ACS_DRS_v0.3/CORDEX-CMIP6/output/AUS-17i/BOM/CSIRO-BOM-ACCESS-CM2/historical/r4i1p1f1/BOM-BARPA-R/v1/day/pr/"
data['r6'] =  iris.load([path_drs+'pr_AUS-17i_CSIRO-BOM-ACCESS-CM2_historical_r4i1p1f1_BOM-BARPA-R_v1_day_%04d0101-%04d1231.nc'%(year,year) for year in years],cx&cy)
iris.util.equalise_attributes(data['r6'])
data['r6'] = data['r6'].concatenate()
data['r6'][0].units = "mm/s"
data['r6'][0].convert_units("mm/day")

cmip_path = "/g/data/fs38/publications/CMIP6/CMIP/CSIRO-ARCCSS/ACCESS-CM2/historical/r4i1p1f1/day/pr/gn/latest/"
ct = iris.Constraint(time=lambda t: t.point.year in years)
data['ACCESS-CM2'] = iris.load(cmip_path+"pr_day_ACCESS-CM2_historical_r4i1p1f1_gn_19500101-19991231.nc",ct&cy&cx)
data['ACCESS-CM2'][0].units = "mm/s"
data['ACCESS-CM2'][0].convert_units("mm/day")
data['ACCESS-CM2'][0] = data['ACCESS-CM2'][0].regrid(data['r2'][0],iris.analysis.Linear())
print(data)

# Precip
proc = {}
agcd_75 = data['agcd'].extract('agcd_precip')[0].extract(cx&cy).data[:,:,1:]
agcd_75.sort(axis=0)
for i,trial in enumerate(trials):
    print(trial)
    proc[trial] = {}
    p = data[trial].extract(['prcp','agcd_precip','precipitation_flux'])[0]
    p = p.extract(cx&cy)
    proc[trial]['mean_rain'] = p.collapsed('time',iris.analysis.MEAN)
    proc[trial]['rain_days'] = p.collapsed('time',iris.analysis.PROPORTION,function=lambda x: x>=1)
    if trial !='agcd':
        p_75 = p.data
        p_75.sort(axis=0)
        proc[trial]['kstest'] = p[0].copy(data=ks(agcd_75[-100:],p_75[-100:]))
# Precip
sig = {}
from iris.coord_categorisation import add_year
add_year(data['r2'][0],'time','year')
add_year(data['r6'][0],'time','year')
tmp1 = data['r2'][0].extract(cx&cy).aggregated_by('year',iris.analysis.MEAN)
tmp2 = data['r6'][0].extract(cx&cy).aggregated_by('year',iris.analysis.MEAN)
tmp3 = data['r2'][0].extract(cx&cy).aggregated_by('year',iris.analysis.PROPORTION,function=lambda x: x>=1)
tmp4 = data['r6'][0].extract(cx&cy).aggregated_by('year',iris.analysis.PROPORTION,function=lambda x: x>=1)

sig['mean_rain'] = tmp1[0].copy(data=np.ma.masked_array(ttest_rel(tmp1.data,tmp2.data,axis=0).pvalue,mask = data['agcd'][0].extract(cx&cy)[0,:,:-1].data.mask))
sig['rain_days'] = tmp3[0].copy(data=np.ma.masked_array(ttest_rel(tmp3.data,tmp4.data,axis=0).pvalue,mask = data['agcd'][0].extract(cx&cy)[0,:,:-1].data.mask))

# mean rain
# rain days
# ks
proc['agcd']['kstest']=0
proc['agcd']['mean_rain'].units = 'mm/day'
plot = {'mean_rain':(0,5,-2,2,cmocean.cm.rain),'rain_days':(0,.5,-0.2,0.2,cmocean.cm.rain),'kstest':(0,0,0,1,cmocean.cm.dense)}
fig = plt.figure(figsize=(8,6))
for i,var in enumerate(['mean_rain','rain_days']):
    for j,trial in enumerate(['agcd','r2','r6']):
        vmin,vmax,vd1,vd2,cmap=plot[var]
        if trial == 'agcd':
            ax=plt.subplot(3,3,i*3+j+1,projection=ccrs.PlateCarree())
            iplt.pcolormesh(proc[trial][var],vmin=vmin,vmax=vmax,cmap=cmap)
            plt.colorbar()
            plt.title("AGCD")
            ax.coastlines()
            ax.text(-0.07, 0.55, ["Mean rainfall \n (mm/day)","Rain day fraction \n (>1mm/day)"][i], va='bottom', ha='center',
                rotation='vertical', rotation_mode='anchor',
                transform=ax.transAxes)
        else:
            ax=plt.subplot(3,3,i*3+j+1,projection=ccrs.PlateCarree())
            tmp = proc[trial][var].copy(data= proc[trial][var].data-proc['agcd'][var].data[:,:-1])
            iplt.pcolormesh(tmp,vmin=vd1,vmax=vd2,cmap='bwr_r')      
            plt.colorbar()
            plt.title("%s: %0.3f"%(trial,np.sqrt(tmp.data**2).mean()) )
            if trial in ['r2','r6']:
                iplt.contourf(sig[var],(0,0.05),hatches=['//'],colors='None')
            ax.coastlines()


for j,trial in enumerate(['r2','r6']):    
    ax=plt.subplot(3,3,j+8,projection=ccrs.PlateCarree())
    iplt.pcolormesh(proc[trial]['kstest'],vmin=0,vmax=0.5,cmap=cmocean.cm.dense_r)  
    plt.title("%s: %0.2f"%(trial,np.nanmean(proc[trial]['kstest'].data)))
    plt.colorbar()
    ax.coastlines()
    if j==0:
        ax.text(-0.07, 0.55, 'KS Stat \n (top 100 days)', va='bottom', ha='center',
        rotation='vertical', rotation_mode='anchor',
        transform=ax.transAxes)

plt.show()

