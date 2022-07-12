import iris
import iris.cube
from iris.coord_categorisation import add_day_of_year
path1 = "/g/data/tp28/BARPA/trials/{domain}*/era/erai/historical/r0/pp_unified/3hourly/av_prcp_rate/0p05deg/{year}/{var}_{domain}_erai_historical_r0_BARPA*_3hourly_{year:04d}{month:02d}0100-*.nc"
path2 = "/short/tp28/eh6215/ESCI/3hr_BARPAC-T/{var}_{domain}_erai_historical_r0_BARPA*_3hourly_{year:04d}{month:02d}.nc"

#path="/g/data/tp28/BARPA/trials/{domain}/era/erai/historical/r0/pp_unified/3hourly/{var}/{grid}/{year:04d}/{var}_{domain}_erai_historical_r0_BARPA*_3hourly_{year:04d}{month:02d}0100-*.nc" 

def load_barpa_esci(year,month,domain,var,Constraints,std_grid=False):
  if domain == "BARPAC-T_km4p4":
      path=path2
  else:
      path=path1
  if std_grid:
    data = iris.load_cube(path.format(year=year,month=month,domain=domain,var=var,grid='0.05deg'))
  else:
    grid = {"BARPA-EASTAUS_12km":"0p11deg","BARPAC-T_km4p4":"0p04deg","BARPAC-M_km2p2":"0p02deg"}[domain]
    data = iris.load_cube(path.format(year=year,month=month,domain=domain,var=var,grid=grid),Constraints)
    add_day_of_year(data,'time','day')
    data=data.aggregated_by('day',iris.analysis.MEAN)
  return data

def regrid(data,template):
  for cube in [data,template]:
     for coord in ['longitude','latitude']:
        cube.coord(coord).coord_system = None
        try:
          cube.coord(coord).guess_bounds()
        except ValueError:
          1
  return data.regrid(template,iris.analysis.AreaWeighted())

def load_agcd(year,month,Constraints):
    ct = iris.Constraint(time=lambda t: t.point.month==month)
    data = iris.load_cube("/g/data/zv2/agcd/v1/precip/total/r005/01day/agcd_v1_precip_total_r005_daily_%d.nc"%year,Constraints&ct)
    return data

def wetdays(year,domain,agcd=False):
    cx = iris.Constraint(longitude=lambda x: 135<=x<=155)
    cy = iris.Constraint(latitude =lambda y: -10.5>=y>=-44)
    template = iris.load_cube('/home/548/eh6215/orog.nc',cx&cy)
    out = iris.cube.CubeList()
    for month in [12,1,2]:
      if domain=='agcd':
          data = load_agcd(year,month,cx&cy)
      else:
        try:
          data = load_barpa_esci(year,month, domain, "av_prcp_rate",cx&cy)
        except OSError:
          continue
      data = regrid(data,template)
      data.units = "mm/s"
      data.convert_units("mm/day")
      data = data.collapsed('time',iris.analysis.PROPORTION,function=lambda x: x>=1)
      data.units="1" 
      out.append(data)
    iris.util.equalise_attributes(out)
    out = out.merge_cube()
    return out

for year in range(1991,2015)[:]:
  for domain in ['BARPAC-T_km4p4', "BARPA-EASTAUS_12km","BARPAC-T_km4p4","BARPAC-M_km2p2"]:
     print(domain)
     out = wetdays(year,domain)
     out.rename(domain+"_wet_days")
     iris.save(out,"/short/tp28/eh6215/ESCI/daily_pr/wetdays_2_%s_%d.nc"%(domain,year),zlib=True,packing='i8') 

