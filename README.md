# BARPA evaluation scripts for sharing with ACS 


## Shared Datasets on gadi/NCI:
`/g/data/tp28/dev/evaluation_datasets/`:
  - `dmi.nc`: Dipole Mode Index timeseries
  - `NRM_*clusters/*`: Original NRM cluster shapefiles
  - `NRM_clusters.nc`: NRM Clusters on BARPA-R grid
  - `NRM_subclusters.nc`: NRM Subclusters on BARPA-R grid
  - `BARPA-R_orography.nc`
  - `BARPA-R_landseamask.nc`
  - `awap_masks.nc`: Land sea mask and data quality mask (based on regions with zero rainfall for long period) on the AWAP grid.
  - `gpcc_mask.nc`: Data-presence mask for GPCC g10 daily data
  - `clim_indices/*.nc`: Generated xclim indices for BARPA, GPCC, AGCD, and ERA5

## Shared Code:
`./lib/`:
  - `apply_xclim.py`: Reads BARPA-R, AGCD, GPCC or ERA5, and applies xclim indicators
  - `load_iris.py`: Loads BARPA-R and CMIP6 data with iris
  - `plotting_functions.py`: creates plots from BRR-069 (AGCD comparisons)
  - `spatial_selection.py`: Damien Irving's code to generate xarray masks from shapefiles
  - `barpa_drs_interface.py`: Reads BARPA-R data using either iris or xarray. Currently interfaces with the test-data on ia39, but can be easily updated to read off the prerelease/release data
  - `cmip6_interface.py`: Reads CMIP6 data using either iris or xarray. Currently limits to the GCM used in BARPA experiments, but can be easily extended to read off other ones.
  - `era5_interface.py`: Reads the ERA5 data on rt52 using either iris or xarray.
  - `agcd_interface.py`: Reads the AGCD data on the zv2 using either iris or xarray.
  - `gpcc_interface.py`: Reads the GPCC data on ia39 using xarray.

## Notebooks:
  - `chs/xclim_prcp_spatial_compare.ipynb` : Spatial comparisons of monthly xclim indicators between ACGD, GPCC, ERA5 and BARPA
