import iris
import iris.cube
from iris.coord_categorisation import add_day_of_year
import numpy as np

cx = iris.Constraint(longitude=lambda x: 110<=x<=155)
cy = iris.Constraint(latitude=lambda x: -45<=x<=10)

towns  = {'Darwin':(-13,131,2),
          'Brisbane':(-27,153,1),
          'Sydney':(-33,151,1),
          'Canberra':(-35,149,1),
          'Melbourne':(-37,145,1),
          'Adelaide':(-35,138,1), 
          'Perth':(-32,116,1),
          "Hobart":(-42.5,147,1)}



file_p = "{var}-{sim}-barpa_r-v1-{yearmon}*.nc"
path = "/g/data/tp28/dev/barpa/prod/{owner}/{trial}/{yearmon}01T0000Z/nc/{time}/"
def daily_precip(year,trial,points,sim,owner,var,outfile,box=False,delta=1):
    out = iris.cube.CubeList([])
    for mon in range(1,13):
        yearmon = "%04d%02d"%(year,mon)
        data=iris.load((path+file_p).format(trial=trial,yearmon=yearmon,sim=sim,var=var,time='SLV1H',owner=owner),cx&cy)
        iris.util.equalise_attributes(data)
        data=data.concatenate_cube()
        add_day_of_year(data,'time','doyr')
        data = data.aggregated_by('doyr',iris.analysis.MEAN)
        data.units='mm/s'
        data.convert_units('mm/day')
        for name in points:
          y,x,delta = points[name]
          if box:
            cx2 = iris.Constraint(longitude=lambda xx: x-delta<=xx<=x+delta)
            cy2 = iris.Constraint(latitude=lambda yy: y-delta<=yy<=y+delta)
            out.append(data.extract(cx2&cy2).collapsed(['latitude','longitude'],iris.analysis.MEAN))
          else:
            out.append(data.interpolate([('latitude',y),('longitude',x)],iris.analysis.Nearest()))
          out[-1].rename(name)
    iris.util.equalise_attributes(out)
    out = out.concatenate()
    iris.save(out,outfile.format(trial=trial,year=year),zlib=True)

def daily_precip_agcd(years,points,outfile,box=False,delta=1):
    out = iris.cube.CubeList()
    for year in years:
      data = iris.load_cube("/g/data/zv2/agcd/v1/precip/total/r005/01day/agcd_v1_precip_total_r005_daily_%s.nc"%year)
      for name in points:
          y,x,delta = points[name]
          if box:
            cx2 = iris.Constraint(longitude=lambda xx: x-delta<=xx<=x+delta)
            cy2 = iris.Constraint(latitude=lambda yy: y-delta<=yy<=y+delta)
            out.append(data.extract(cx2&cy2).collapsed(['latitude','longitude'],iris.analysis.MEAN))
          else:
            out.append(data.interpolate([('latitude',y),('longitude',x)],iris.analysis.Nearest()))
          out[-1].rename(name)
    iris.util.equalise_attributes(out)
    out = out.concatenate()
    iris.save(out,outfile.format(trial='agcd_v1_total',year=year),zlib=True)
    #return out 

outfile_point = "/scratch/tp28/eh6215/rain_ts/rain_{trial}_{year}.nc"
outfile_box = "/scratch/tp28/eh6215/rain_ts/rain_{trial}_{year}_box.nc"
                    
hist = "CMIP6-ACCESS-CM2-historical-r4i1p1f1"
future = "CMIP6-ACCESS-CM2-ssp370-r4i1p1f1"
for year in range(1967,1972):
  print(year)
  daily_precip(year,'cg282_ACCESS-CM2_historical_1960_sciB',towns,hist,'eh6215',"av_prcp_rate",outfile_box,box=True)

for year in range(2015,2026):
  print(year)
  daily_precip(year,'cg282_ACCESS-CM2_historical_2014_sciB',towns,future,'eh6215',"av_prcp_rate",outfile_box,box=True)


