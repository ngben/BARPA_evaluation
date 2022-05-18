import asop_coherence as asop
import numpy as np
import pickle

"""
    Example use of ASoP Coherence package to compute
    and plot diagnostics of the spatial and temporal
    coherence of precipitation in a dataset.
    
    This example uses TRMM 3B42v7A and CMORPH v1.0 data 
    for October 2009 - January 2010, as shown in 
    Klingaman et al. (2017, GMD, doi:10.5194/gmd-10-57-2017)
    
    Written by Nicholas Klingaman
    nicholas.klingaman@ncas.ac.uk
    
    (C) The author 2017
    
"""

def get_dictionary(key):
    
    """
    The Coherence package relies on a dataset dictionary,
    for which currently the user must specify most values.
        
    This function shows how to build a dictionary.  The dictionary to
    be returned to the main program is selected through the use of
    a "key", here either "TRMM" or "CMORPH"
        
    Arguments:
        * key:
            A string used to select the correct dataset
            
    Returns:
        * asop_dict:
            A dictionary containing required and optional
            parameters for the ASoP Coherence package.
    
        Required dictionary keys:
        
        infile       - Path to input file (must be readable by Iris)
        name         - Name for model in plot files (no spaces)
        legend_name  - Name for model in legends and titles on plots (spaces allowed)
        dt           - Timestep of input data (in seconds)
        dx           - Longitudinal grid spacing at equator (in km)
        dy           - Latitudinal grid spacing (in km)
        constraint   - standard_name of data to read from netCDF file (e.g., precipitation flux)
        scale_factor - Multiplier necessary to convert precipitation to units of mm/day
        region       - Region of data to read [minlat, maxlat, minlon, maxlon]
        box_size     - Length of sub-regions (square boxes) to consider for correlation analysis
                        as a function of physical distance
                        (in km, recommended value is > 6.5*dx).
        color        - Name of color to use on line graphs (must be recognised by matplotlib).
        region_size  - Length of sub-regions (square boxes) to consider for correlation analysis
                        as a function of model gridpoints (including lag correlations, see below)
                        (in units of native gridpoints, odd integers strongly recommended).
        lag_length   - Maximum lag to consider for correlation analysis as a function of model
                        gridpoints, for constructing distance vs. lag correlation diagrams.
                        Correlations for lags from 0 (coincidence) until lag_length will be computed.
        autocorr_length - The maximum autocorrelation to analyse (in seconds).
        
        Optional dictionary keys, which are useful mainly if analysing the same
        dataset on more than one grid / temporal sampling interval:
        
        grid_type    - A string describing the grid, used in output filenames
                        (recommend no spaces).
        time_type    - A string describing the temporal sampling, used in output filenames
                        (recommend no spaces).
        grid_desc    - A string describing the grid, used in plot titles (can contain spaces).
        time_desc    - A string describing the temporal sampling, used in plot titles
                        (can contain spaces).
    """
    
    asop_dict = {}
    if key == 'BARPAR':
        asop_dict['infile']       = '/g/data/tp28/BARPA/trials/BARPA-EASTAUS_12km/era/erai/historical/r0/pp_unified/daily/pr/0p11deg/2006/pr_BARPA-EASTAUS_12km_erai_historical_r0_BARPA_daily_2006010100-2006020100.nc'
        asop_dict['name']         = 'BARPAR'
        asop_dict['dt']           = 86400
        asop_dict['dx']           = 4
        asop_dict['dy']           = 4
        asop_dict['constraint']   = 'DAILY INTEGRATED PRECIPITATION IN MM DAY-1'
        asop_dict['scale_factor'] = 1.0
        asop_dict['legend_name']  = 'BARPA-R'
        asop_dict['region']       = [-30,-10,140,160]
        asop_dict['box_size']     = 1680
        asop_dict['color']        = 'red'
        asop_dict['region_size']  = 13
        asop_dict['lag_length']   = 1  
        asop_dict['grid_type']    = 'native'
        asop_dict['time_type']    = '1day'
        asop_dict['grid_desc']    = 'native'
        asop_dict['time_desc']    = 'daily'
        asop_dict['autocorr_length'] = 60*60*24
    elif key == 'BARPAC-T':
        asop_dict['infile']       = '/g/data/tp28/BARPA/trials/BARPAC-T_km4p4/era/erai/historical/r0/pp_unified/daily/pr/0p04deg/2006/pr_BARPAC-T_km4p4_erai_historical_r0_BARPAC_daily_2006010100-2006020100.nc'
        asop_dict['name']         = 'BARPAC-T'
        asop_dict['dt']           = 86400
        asop_dict['dx']           = 12
        asop_dict['dy']           = 12
        asop_dict['constraint']   = 'DAILY INTEGRATED PRECIPITATION IN MM DAY-1'
        asop_dict['scale_factor'] = 1.0
        asop_dict['legend_name']  = 'BARPAC-T'
        asop_dict['region']       = [-30,-10,140,160]
        asop_dict['box_size']     = 1680
        asop_dict['color']        = 'blue'
        asop_dict['region_size']  = 13
        asop_dict['lag_length']   = 1
        asop_dict['grid_type']    = 'native'
        asop_dict['time_type']    = 'daily'
        asop_dict['grid_desc']    = 'native'
        asop_dict['time_desc']    = 'daily'
        asop_dict['autocorr_length'] = 60*60*24

    return(asop_dict)

if __name__ == '__main__':

    datasets = ('BARPAC-T','BARPAR')
    n_datasets = len(datasets)

    # Allocate memory for multi-model fields
    max_box_distance,max_timesteps,max_boxes = asop.parameters()
    all_distance_correlations = np.zeros((n_datasets,max_box_distance))
    all_distance_ranges = np.zeros((n_datasets,3,max_box_distance))
    all_distance_max = np.zeros((n_datasets),dtype=np.int)
    all_time_correlations = np.zeros((n_datasets,max_timesteps))
    all_time_max = np.zeros((n_datasets),dtype=np.int)
    all_dt = np.zeros((n_datasets),dtype=np.int)
    all_colors = []
    all_legend_names = []

    for i in range(n_datasets):
    
        print('--> '+datasets[i])
        asop_dict = get_dictionary(datasets[i])
    
        # Read precipitation data
        precip = asop.read_precip(asop_dict)

        # Define edges of bins for 1D and 2D histograms
        # Note that on plots, the first and last edges will be
        # replaced by < and > signs, respectively.
        bins=[0,1,2,4,6,9,12,16,20,25,30,40,60,90,130,180,2e20]
        bins=np.asarray(bins)

        # Compute 1D and 2D histograms
        oned_hist, twod_hist = asop.compute_histogram(precip,bins)

        # Plot 1D and 2D histograms (e.g., Fig. 2a in Klingaman et al. 2017).
        asop.plot_histogram(oned_hist,twod_hist,asop_dict,bins,ext='.png')

        # Compute correlations as a function of native gridpoints, by dividing
        # analysis region into sub-regions (boxes of length region_size).  Also
        # computes lag correlations to a maximum lag of lag_length.
        corr_map,lag_vs_distance,autocorr,npts_map,npts = asop.compute_equalgrid_corr(precip,asop_dict)

        # Plot correlations as a function of native gridpoints and time lag
        # (e.g., Figs. 2c and 2e in Klingaman et al. 2017).
        asop.plot_equalgrid_corr(corr_map,lag_vs_distance,autocorr,npts,asop_dict,colorbar=False,ext='.png')

        # Compute correlations as a function of physical distance, by dividing
        # analysis region into sub-regions (boxes of length box_size).
        all_distance_correlations[i,:],all_distance_ranges[i,:,:],all_distance_max[i] = asop.compute_equalarea_corr(precip,asop_dict)
    
        # Compute lagged autocorrelations over all points
        all_time_correlations[i,:],all_time_max[i] = asop.compute_autocorr(precip,asop_dict)

        # Compute spatial and temporal coherence metrics, based on quartiles (4 divisions)
        space_inter, time_inter = asop.compute_spacetime_summary(precip,4)

        # Save dataset timestep information
        all_dt[i] = asop_dict['dt']

        # Save color and legend information
        all_colors.append(asop_dict['color'])
        all_legend_names.append(asop_dict['legend_name'])
    pickle.dump((all_distance_correlations,all_distance_ranges,all_distance_max,all_time_correlations,all_time_max,all_colors,all_legend_names),open("asop_coherence.pickle",'wb'))
    # Plot correlations as a function of physical distance for all datasets
    asop.plot_equalarea_corr(all_distance_correlations,all_distance_ranges,all_distance_max,colors=all_colors,legend_names=all_legend_names,set_desc='satobs',ext='.png')
    # Plot correlations as a function of physical time for all datasets
    asop.plot_autocorr(all_time_correlations,all_time_max,dt=all_dt,colors=all_colors,legend_names=all_legend_names,set_desc='satobs',ext='.png')
