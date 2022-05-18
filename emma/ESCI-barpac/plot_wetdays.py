import iris
import numpy as np
import matplotlib.pyplot as plt
from plotting_functions import bias_plots
import cmocean

cx = iris.Constraint(longitude=lambda x: 140<=x<=155)
cy = iris.Constraint(latitude =lambda y: -10.5>=y>=-44)
   
lsm = iris.load_cube("/home/548/eh6215/lsm.nc","land_binary_mask").extract(cx&cy)[:-1]
#lsm.data  = np.m.masked_array(np.ones(lsm.shape),mask=1-lsm.data)
data = {}
ct = iris.Constraint(time=lambda t:t.point.month in [1] and t.point.year >= 1991 and t.point.year <2015)
for domain in ['agcd',"BARPA-EASTAUS_12km","BARPAC-T_km4p4","BARPAC-M_km2p2"]:
    data[domain] = {}
    data[domain]['wet days']= iris.load_cube("/scratch/tp28/eh6215/ESCI/daily_pr/wetdays_%s.nc"%domain).extract(cx&cy&ct)
    data[domain]['wet days'].rename('wet days')

cy2 = iris.Constraint(latitude=lambda y: y>-30)
cy3 = iris.Constraint(latitude=lambda y: y<=-30)

tmp = iris.cube.CubeList([data["BARPAC-T_km4p4"]['wet days'].extract(cy2),1*data['BARPAC-M_km2p2']['wet days'].extract(cy3)])
iris.util.equalise_attributes(tmp)
tmp=tmp.concatenate_cube()
data['BARPAC']={}
data['BARPAC']['wet days']=tmp
cy2 = iris.Constraint(latitude =lambda y: -10.5>=y>=-44)
plt.figure()
bias_plots(data,'wet days',1-lsm.extract(cy2).data,["BARPA-EASTAUS_12km","BARPAC","agcd"],0,1,0.5,cmocean.cm.rain,'bwr_r',"1",Constraints=cy2&ct)

plt.figure()
bias_plots(data,'wet days',1-lsm.extract(cy2).data,["BARPA-EASTAUS_12km","BARPAC-M_km2p2","agcd"],0,1,0.2,cmocean.cm.rain,'bwr_r',"1",Constraints=cy2&ct)

plt.show()
