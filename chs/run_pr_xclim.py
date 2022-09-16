from __future__ import annotations
import os, sys
sys.path.append("../lib")
from datetime import datetime as dt
import xclim 
import apply_xclim
import importlib
importlib.reload(apply_xclim)
import argparse

parser = argparse.ArgumentParser(description='Compute monthly xclim indices from daily BARPA, AGCD, CMIP6 and GPCC data, and hourly ERA5 data')
parser.add_argument('--metric', nargs='?', help='xclim indicators for precipitation')
parser.add_argument('--data_source', nargs='?', choices=["AGCD", "ERA5", "GPCC", "BARPA", "CMIP6"], help='Name of the data source')
parser.add_argument("--workdir", nargs='?', help="Directory path to save the data files")
parser.add_argument("--years", nargs='+', help="Comma separated list of years to process")
parser.add_argument("--barpa_gcm", nargs='?', help="Driving GCM name for BARPA if --data_source BARPA")
parser.add_argument("--scenario", nargs='?', help="Scenario for BARPA if --data_source BARPA or CMIP6")
parser.add_argument("--gcm", nargs='?', help="CMIP6 model name if --data_source CMIP6")

args = parser.parse_args()

metric = args.metric
data_source = args.data_source
workdir = args.workdir
years = [int(y) for y in args.years]

if not os.path.exists(workdir):
    os.makedirs(workdir)
    
metric_maps = {'RR1': xclim.indicators.icclim.RR1,
               'dry_days': xclim.indicators.atmos.dry_days,
               'R20mm': xclim.indicators.icclim.R20mm,
               'R10mm': xclim.indicators.icclim.R10mm,
               'RX1day': xclim.indicators.icclim.RX1day,
               'RX5day': xclim.indicators.icclim.RX5day,
               'prcptot': xclim.indices.prcptot
              }

assert metric in metric_maps.keys(), "Undefined metric {:}, update metric_maps".format(metric)
indicator = metric_maps[metric]

if data_source == 'AGCD':
    print("Doing {:}".format(data_source))
    out = apply_xclim.xclim_for_agcd(indicator, 'precip', 'calib', years, outpath=workdir)
    
elif data_source == 'ERA5':
    print("Doing {:}".format(data_source))
    operation = 'resample(time="1D").mean()'
    out = apply_xclim.xclim_for_era5(indicator, 'single-levels', 'mtpr', operation, years, outpath=workdir)
    
elif data_source == 'GPCC':
    print("Doing {:}".format(data_source))
    out = apply_xclim.xclim_for_gpcc(indicator, years, res="g10", outpath=workdir)
    
elif data_source == 'BARPA':
    print("Doing {:}".format(data_source))
    assert args.scenario is not None, "--scenario is needed"
    assert args.barpa_gcm is not None, "--barpa_gcm is needed"
    scenario = 'evaluation' if args.barpa_gcm == 'ERA5' else args.scenario
    out = apply_xclim.xclim_for_barpa(args.barpa_gcm, indicator, "pr", scenario, years, outpath=workdir)
    
elif data_source == "CMIP6":
    print("Doing {:}".format(data_source))
    assert args.scenario is not None, "--scenario is needed"
    assert args.gcm is not None, "--gcm is needed"
    out = apply_xclim.xclim_for_cmip6(args.gcm, indicator, 'pr', args.scenario, years, outpath=workdir)
