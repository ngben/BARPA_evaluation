  

variables = { "hus"  :("Specific Humidity",  ["700","600"]),
         "omega":("Vertical wind",      ["500"]), 
         "psl"  :("Pressure",           ["Sea Level"]), 
         "ta"   :("Air Temperature",    ["850","700","600","500","300"]), 
         "ua"   :("Eastward Wind",      ["850","300","200"]),
         "va"   :("Northward Wind",     ["850","300","200"])}
#         "zg"   :("Geopotential Height",["500","300"])}
    
colour= ['FF9AA2','FFB7B2','FFDAC1','E2F0CB','B5EAD7','C8CECA']
for i,var in enumerate(variables):
    name, heights = variables[var]
    print("[h1: %s]"%name)
    print("bgcolor = %s\n"%colour[i])
    for h in heights:
        if h[-1]=='0':
            print("[h2: %s hPa %s]"%(h,name))
            print("variable=%s%s\n"%(var,h))
            print("[era5]")
            print("source = DATA/{var}{height}/era5/era5_{var}{height}.nc\n".format(var=var,height=h))
        else:
            var2=var
            if h=='Surface':
               var2 = {'hus':'huss','ta':'tasmean'}[var]
            print("[h2: %s %s]"%(h,name))
            print("variable=%s\n"%var2)
            print("[era5]")
            print("source = DATA/{var}/era5/era5_{var}.nc\n".format(var=var2))    
