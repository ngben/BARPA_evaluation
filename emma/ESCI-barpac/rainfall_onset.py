import iris
import iris.cube
import numpy as np
import cf_units 
import progressbar
gdd_real = {"ACCESS1-0":("cmip5","r1i1p1"),"erai":("era",'r0')}


def load_esci_daily(model, var, yearmons, file_template,  scenario='historical',domain="BARPA-EASTAUS_12km",constraints=None,landmask=False):
  assert model in ['ACCESS1-0','erai']
  gdd,realisation = gdd_real[model]
  paths = np.unique([file_template.format( \
             domain=domain, gdd=gdd, model=model, scenario=scenario, realisation=realisation, var=var, \
			 year=year, month=month, year1 = year + int((month+1)>12), month1 = month%12+1) \
             for year,month in yearmons])
  ct = iris.Constraint(time = lambda t: (t.point.year,t.point.month) in yearmons)
  data = iris.load(paths,constraints&ct)
  iris.util.equalise_attributes(data)
  data = data.concatenate().merge()
  if landmask: 
    mask  = iris.load_cube("/g/data/tp28/BARPA/trials/{domain}/static/lnd_mask-{domain}.nc".format(domain=domain),constraints)
    for cube in data:
      if 'latitude' in [x.name() for x in cube.coords()] and 'longitude' in [x.name() for x in cube.coords()]:
        cube.data = np.ma.masked_array(cube.data, mask = (mask.data == 0)[np.newaxis]*np.ones(cube.shape))
  if len(data) and len(data.extract('time_bnds'))==1:
    time_bounds = data.extract_cube('time_bnds')
    cube = data.extract_cube(iris.Constraint(cube_func = lambda x: x.name() != 'time_bnds'))
    cube.coord('time').bounds = time_bounds.data
    return cube
  if len(data)==1:
    return data[0]
  return data


def rainfall_onset(model, years, loader, file_template, startmon = 9, mons = 7, threshold=50, scenario='historical',domain="BARPA-EASTAUS_12km",constraints=None,landmask=True):
  onset_all = iris.cube.CubeList()
  for year in progressbar.progressbar(years):
    yearmons = [(year+int((i+1)>12),i%12+1) for i in range(startmon, startmon+mons)]
    data = loader(model, 'pr', yearmons, file_template, scenario=scenario, domain=domain, constraints=constraints,landmask = landmask)
    t0 = data.coord('time').copy()
    t0.convert_units(cf_units.Unit("days since %04d-01-01"%year,data.coord('time').units.calendar))
    acc = np.cumsum(data.data,axis=0)
    onset = np.argmax(acc>threshold,axis=0) + t0[0].points
    onset = np.ma.masked_values(onset,0)
    onset = data[0].copy(data=onset)
    onset.units = 'days'
    onset.rename("rainy season onset date")
    onset_all.append(onset)
  iris.util.equalise_attributes(onset_all)
  onset_all = onset_all.merge_cube()
  return onset_all

def main():
  cx = iris.Constraint(longitude=lambda x: 130<=x<=155)
  cy = iris.Constraint(latitude =lambda y: -45<=y<=-10)
  datapath = "/g/data/tp28/BARPA/trials/{domain}/{gdd}/{model}/{scenario}/{realisation}/pp_unified/daily/{var}/0p04deg/{year}/"
  filename = "{var}_{domain}_{model}_{scenario}_{realisation}_BARPAC_daily_{year:04d}{month:02d}0100-{year1:04d}{month1:02d}0100.nc"
  outdir = "/scratch/tp28/eh6215/esci/"
  era_onset = rainfall_onset('erai',range(1990,2005),load_esci_daily, datapath+filename,constraints=cx&cy,domain="BARPAC-T_km4p4",startmon=10,mons=6)
  iris.save(era_onset,outdir+"rainfall_onset_erai-C.nc")
#  era_onset = rainfall_onset('erai',range(1990,2005),load_esci_daily, datapath+filename,constraints=cx&cy)
#  iris.save(era_onset,outdir+"rainfall_onset_erai.nc")
#  access_onset = rainfall_onset('ACCESS1-0',range(1990,2005),load_esci_daily,datapath+filename,constraints=cx&cy)
#  iris.save(access_onset,outdir+"rainfall_onset_ACCESS1-0.nc")
#  datapath = "/g/data/tp28/Climate_Hazards/QME/BARPA/BARPA_{model}_bc/{scenario}/pr/"
#  filename = "pr{year}.nc"
#  access_onset = rainfall_onset('ACCESS1-0',range(1990,2005),load_esci_daily,datapath+filename,constraints=cx&cy,scenario='rcp85',landmask=False)
#  iris.save(access_onset,outdir+"rainfall_onset_ACCESS1-0_QME.nc")
#  import pdb;pdb.set_trace()



def plot(): 
  import matplotlib.pyplot as plt
  import iris.plot as iplt
  import cartopy.crs as ccrs
  import matplotlib.colors as mcolors
  from scipy.ndimage import convolve, gaussian_filter
  import datetime as dt
#
  erai = iris.load("rainfall_onset_erai.nc")
  ACCESS = iris.load("rainfall_onset_ACCESS1-0.nc")
  QME = iris.load("rainfall_onset_ACCESS1-0_QME.nc")
#
  ticks = [[(dt.datetime(2012+int(month<6),month,day)-dt.datetime(2012,1,1)).days for day in [1,11,21]] for month in [9,10,11,12,1,2,3]]
  ticks = [item for sublist in ticks for item in sublist][:-2]
  colours =map(lambda x: plt.cm.Spectral_r(x-int(x<1/2)*1/16) if x>1/3 else plt.cm.RdBu_r(x),np.linspace(0,1,100))
  cmap = mcolors.LinearSegmentedColormap.from_list('onset',list(colours))
  axs = []
#  
  cy =  iris.Constraint(latitude=lambda y: y>-29)
  for i,data in enumerate([erai,ACCESS,QME]):
    ax=plt.subplot(1,3,i+1,projection=ccrs.PlateCarree())
    x = data[0].extract(cy).collapsed('time',iris.analysis.PERCENTILE,percent=50)
    x.data = np.ma.masked_array(x.data,x.data<275)
    mask = x.data.mask
    mask = convolve(mask,np.ones((2,2)))==1
    x.data = gaussian_filter(x.data,2)
    x.data = np.ma.masked_array(x.data, mask)
    a=iplt.contourf(x,ticks,cmap=cmap,extend='max')
    iplt.contour(x,ticks,colors='0.5',linewidths=0.5)
    ax.coastlines()
    axs.append(ax)
#
  cax = plt.colorbar(a,ax=axs,ticks = ticks[::3],orientation='horizontal')
  cax.ax.set_xticklabels(["1 %s"%mon for mon in ['Sep','Oct','Nov',"Dec","Jan","Feb","Mar"]])
  plt.show()


if __name__ == "__main__":
    main()
