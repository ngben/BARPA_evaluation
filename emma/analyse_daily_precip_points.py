
import iris
import matplotlib.pyplot as plt
import os

path  ="/scratch/tp28/eh6215/rain_ts/"
os.chdir(path)
r6 = iris.load([path+"rain_cg282_ACCESS-CM2_historical_1979_r6p_%d.nc"%i for i in range(1980,1990)])
r4 = iris.load([path+"rain_cg282_ACCESS-CM2_historical_1979_r4p_%d.nc"%i for i in range(1980,1990)])
awap = iris.load([path+"rain_agcd_v1_total_%d.nc"%i for i in range(1980,1990)])

towns  = {'Darwin':(-13,131,2),
          'Katherine':(-15,132,2),
          'Cloncurry':(-20,140,2),
          'Cairns':(-17,145,2),
          'Rockhampton':(-23,150,2),
          'Brisbane':(-27,153,1),
          'Roma':(-26,149,1),
          'Coffs':(-30,153,1),
          'Sydney':(-33,151,1),
          'Canberra':(-35,149,1),
          'Dubbo':(-32,148,1),
          'Shepparton':(-36,145,1),
          'Melbourne':(-37,145,1),
          'Tasmania':(-42,146.5,2),
          'Mildura':(-34,142,2),
          'Warrnambul':(-38,142,1),
          'Adelaide':(-35,138,1), 
          'Cooper Pedy':(-29,135,1),
          'Whyalla':(-33, 137,2), 
          'Esperance':(-34,122,2),
          'Perth':(-32,116,1),
          'Kalgoorlie':(-30,121,2),
          'Karratha':(-20,116,2),
          "Launceston":(-41.5,147,1),
          "Hobart":(-42.5,147,1)}



def daily_precip_barpa(years,points):
    out = iris.cube.CubeList()
    for year in years:
      data = iris.load_cube("/g/data/zv2/agcd/v1/precip/total/r005/01day/agcd_v1_precip_total_r005_daily_%s.nc"%year)
      for name in points:
          y,x,delta = points[name]
          out.append(data.interpolate([('latitude',y),('longitude',x)],iris.analysis.Nearest()))
          out[-1].rename(name)
    iris.util.equalise_attributes(out)
    out = out.concatenate()
    #iris.save(out,outfile.format(trial='agcd_v1_total',year=year),zlib=True)
    return out 

#agcd = daily_precip(range(1980,1990),towns)

def daily_precip_cmip(years,points):
    path = "/g/data/r87/DRSv3/CMIP6/CMIP/CSIRO-ARCCSS/ACCESS-CM2/historical/r4i1p1f1/day/pr/gn/latest/pr_day_ACCESS-CM2_historical_r4i1p1f1_gn_19500101-19991231.nc"
    ct = iris.Constraint(time=lambda t: t.point.year in years)
    data = iris.load_cube(path,ct)
    out = iris.cube.CubeList()
    for name in points:
        y,x,delta = points[name]
        out.append(data.interpolate([('latitude',y),('longitude',x)],iris.analysis.Nearest()))
        out[-1].rename(name)
    return out

cmip = daily_precip_cmip(range(1980,1990),towns)

iris.util.equalise_attributes(r4)
iris.util.equalise_attributes(r6)
iris.util.equalise_attributes(awap)

r6 = r6.concatenate()
r4 = r4.concatenate()
awap = awap.concatenate()

for i in range(25):
  ax=plt.subplot(5,5,i+1,aspect=1)
  x = r4[i].data
  y = r6[i].data
  z = awap[i].data
  c = cmip[i].data
  x.sort()
  y.sort()
  z.sort()
  c.sort()
  m1 = 0.01#
  x[int((x>0).sum()*-.1)]
  m2 = max(x[-1],y[-1])
  plt.plot(z,x,'.',ms=2)
  plt.plot(z,y,'.',ms=2)
  plt.plot(z,c,'.',ms=2)
  plt.plot([m1,m2],[m1,m2],'k-',lw=1)
  plt.semilogy()
  plt.semilogx()
  plt.title(r4[i].name(),fontsize='small')
#  plt.ylim(0.01,1000)
#  plt.xlim(0.01,1000)
  plt.xlim([m1,m2*1.05])
  plt.ylim([m1,m2*1.05])
  plt.xticks(fontsize='x-small')
  plt.yticks(fontsize='x-small')
  plt.grid()


plt.show()
