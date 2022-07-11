import iris
import numpy as np
import os

path1 = "/g/data/tp28/BARPA/trials/{domain}*/era/erai/historical/r0/pp_unified/3hourly/av_prcp_rate/0p05deg/{year}/"
path2 = "/short/tp28/eh6215/ESCI/3hr_BARPAC-T/"


def regrid(year,name):
        data ={}
        if name in ["BARPAC-M","BARPA-E"]:
            data=iris.load([(path1+"/*_{year:04d}{month:02d}*").format(domain=name,year=year1,month=month) for year1,month in [(year,12),(year+1,1),(year+1,2)]])
        else:
            data=iris.load([(path2+"/*_{year:04d}{month:02d}*").format(domain=name,year=year1,month=month) for year1,month in [(year,12),(year+1,1),(year+1,2)]])
        iris.util.equalise_attributes(data)
        data=data.concatenate_cube()
        data.units = "mm/s"
        data.convert_units("mm/day")
        lat=iris.coords.DimCoord({'BARPAC-M':np.arange(-45,-30,0.25),\
                                  'BARPAC-T':np.arange(-30,-10,0.25),\
                                  'BARPA-E' :np.arange(-45,-10,0.25)}[name],standard_name='latitude',units='degrees')
        lon=iris.coords.DimCoord(np.arange(140,155,0.25),standard_name='longitude',units='degrees')
        lat.guess_bounds()
        lon.guess_bounds()
        template = data[0,:lat.shape[0],:lon.shape[0]]
        template.remove_coord('latitude')
        template.remove_coord('longitude')
        template.add_dim_coord(lat,0)
        template.add_dim_coord(lon,1)
        try:
            data.coord('longitude').coord_system=None
            data.coord('latitude').coord_system=None
            data.coord('longitude').guess_bounds()
            data.coord('latitude').guess_bounds()
        except:
            1
        data = data.regrid(template,iris.analysis.AreaWeighted())
        iris.save(data,path2+"regrid_%s_%d.nc"%(name,year),zlib=True, packing='i2')
        del data


for year in range(2010,2016):
    for name in ["BARPAC-M","BARPAC-T","BARPA-E"]:
       if year != 1999:
           if not os.path.exists(path2+"regrid_%s_%d.nc"%(name,year)):
               print(year,name)
               regrid(year,name)
