BARPA evaluation scripts for sharing with ACS 


Shared Datasets:

/g/data/tp28/dev/evaluation_datasets/dmi.nc: Dipole Mode Index timeseries

/g/data/tp28/dev/evaluation_datasets/NRM_*clusters/*: Original NRM cluster shapefiles

/g/data/tp28/dev/evaluation_datasets/NRM_clusters.nc: NRM Clusters on BARPA-R grid

/g/data/tp28/dev/evaluation_datasets/NRM_subclusters.nc: NRM Subclusters on BARPA-R grid

/g/data/tp28/dev/evaluation_datasets/BARPA-R_orography.nc

/g/data/tp28/dev/evaluation_datasets/BARPA-R_landseamask.nc


Shared Code:

lib/apply_xclim.py: Reads BARPA-R or AGCD and applies xclim indicators

lib/load_iris.py: Loads BARPA-R and CMIP6 data with iris

lib/plotting_functions.py: creates plots from BRR-069 (AGCD comparisons)

lib/spatial_selection.py: Damien Irving's code to generate xarray masks from shapefiles
