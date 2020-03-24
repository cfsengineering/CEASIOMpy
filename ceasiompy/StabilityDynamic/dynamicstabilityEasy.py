"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

dynamic stability module

Python version: >=3.6

| Author: Verdier Loïc
| Creation: 2019-10-24
| Last modifiction: 2019-11-28 (AJ)

TODO:
    * Modify the code where there are "TODO"
    * If only one aos angle -> dirrectionaly_stable  ???
    * If only one aos angle -> longitudinaly_stable  ???
    * Should we also save results as report (text file)
"""

#==============================================================================
#   IMPORTS
#==============================================================================

import os
import sys
import time
import math
import numpy as np
import matplotlib as mpl, cycler
import matplotlib.patheffects
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Patch

import pandas as pd

from ceasiompy.utils.cpacsfunctions import open_tixi, open_tigl, close_tixi,   \
                                            create_branch, copy_branch, add_uid,\
                                            get_value, get_value_or_default,    \
                                            add_float_vector, get_float_vector, \
                                            add_string_vector, get_string_vector,\
                                            aircraft_name
from ceasiompy.utils.moduleinterfaces import check_cpacs_input_requirements, \
                                            get_toolinput_file_path,        \
                                            get_tooloutput_file_path
from ceasiompy.utils.apmfunctions import aeromap_to_csv, get_aeromap_uid_list, \
                                            aeromap_from_csv, get_aeromap, check_aeromap
from ceasiompy.StabilityDynamic.func import short_period, phugoid, roll, spiral, dutch_roll, \
                                            get_unic, interpolation, get_index,  trim_derivative, find_max_min, \
                                            plot_multicurve
from ceasiompy.utils.standardatmosphere import get_atmosphere, plot_atmosphere
from ceasiompy.utils.standardatmosphere import get_atmosphere
from ceasiompy.SkinFriction.skinfriction import get_largest_wing_dim
from ceasiompy.utils.ceasiomlogger import get_logger

log = get_logger(__file__.split('.')[0])

MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
MODULE_NAME = os.path.basename(os.getcwd())


#==============================================================================
#   Classes
#========================================================================


#==============================================================================
#   FUNCTIONS
#==============================================================================

def dynamic_stability_analysis(cpacs_path, cpacs_out_path):
    """Function to analyse a full Aeromap

    Function 'dynamic_stability_analysis' analyses longitudinal dynamic
    stability and directionnal dynamic.

    Args:
        cpacs_path (str): Path to CPACS file
        cpacs_out_path (str):Path to CPACS output file
        plot (boolean): Choise to plot graph or not

    Returns:
        *   Adrvertisements certifying if the aircraft is stable or Not
        *   In case of longitudinal dynamic UNstability or unvalid test on data:
                -	Plot cms VS aoa for constant Alt, Mach and different aos
                -	Plot cms VS aoa for const alt and aos and different mach
                -	plot cms VS aoa for constant mach, AOS and different altitudes
        *  In case of directionnal dynamic UNstability or unvalid test on data:
                -	Pcot cml VS aos for constant Alt, Mach and different aoa
                -	Plot cml VS aos for const alt and aoa and different mach
                -	plot cml VS aos for constant mach, AOA and different altitudes
        *  Plot one graph of  cruising angles of attack for different mach and altitudes

    Make the following tests:            (To put in the documentation)
        *   Check the CPACS path
        *   For longitudinal dynamic stability analysis:
                -   If there is more than one angle of attack for a given altitude, mach, aos
                -   If cml values are only zeros for a given altitude, mach, aos
                -   If there one aoa value which is repeated for a given altitude, mach, aos
        *   For directionnal dynamic stability analysis:
                -   If there is more than one angle of sideslip for a given altitude, mach, aoa
                -   If cms values are only zeros for a given altitude, mach, aoa
                -   If there one aos value which is repeated for a given altitude, mach, aoa
    """

    # Xpath definition
    dynamic_analysis_xpath = '/cpacs/toolspecific/CEASIOMpy/stability/dynamic'
    aeromap_uid_xpath =   dynamic_analysis_xpath + '/aeroMapUid'
    model_xpath = '/cpacs/vehicles/aircraft/model'
    ref_area_xpath = model_xpath + '/reference/area'
    ref_length_xpath = model_xpath + '/reference/length'

    # Ask user if reference area is : Wing already
    # user has to answer y, if after 30 sec user has not answered make claculation
    tixi = open_tixi(cpacs_path)

    # Get aeromap uid
    aeromap_uid = get_value(tixi, aeromap_uid_xpath )
    log.info('The following aeroMap will be analysed: ' + aeromap_uid)
    # Mass configuration: (Maximum landing mass, Maximum ramp mass (the maximum weight authorised for the ground handling), Take off mass, Zero Fuel mass)
    mass_config = get_value(tixi, '/cpacs/toolspecific/CEASIOMpy/stability/dynamic/MassConfiguration')
    log.info('The aircraft mass configuration used for analysis is: ' + mass_config)
    # Analyses to do [Short, phug, roll, spiral, Dutch_roll]
    short_analysis = get_value(tixi, dynamic_analysis_xpath + '/instabilityModes/shortPeriod')
    phugoid_analysis = get_value(tixi, dynamic_analysis_xpath + '/instabilityModes/phugoid')
    roll_analysis = get_value(tixi, dynamic_analysis_xpath + '/instabilityModes/roll')
    spiral_analysis = get_value(tixi, dynamic_analysis_xpath + '/instabilityModes/spiral')
    dutch_analysis = get_value(tixi, dynamic_analysis_xpath + '/instabilityModes/dutchRoll')
    analysis = [short_analysis, phugoid_analysis, roll_analysis, spiral_analysis, spiral_analysis, dutch_analysis ]
    # Plots configuration with Setting GUI
    show_plots = get_value_or_default(tixi,'/cpacs/toolspecific/CEASIOMpy/stability/dynamic/showPlots',False)
    save_plots = get_value_or_default(tixi,'/cpacs/toolspecific/CEASIOMpy/stability/dynamic/savePlots',False)

    mass_config_xpath = model_xpath + '/analyses/massBreakdown/designMasses/' + mass_config
    if tixi.checkElement(mass_config_xpath):
        mass_xpath = mass_config_xpath + '/mass'
        i_xx_xpath  = mass_config_xpath + '/massInertia/Jxx'
        i_yy_xpath  = mass_config_xpath + '/massInertia/Jyy'
        i_zz_xpath = mass_config_xpath + '/massInertia/Jzz'
    else :
        raise ValueError(' !!! The mass configuration : {} is not defined in the CPACS file !!!'.format(mass_config))

    s = get_value(tixi,ref_area_xpath)     # Wing area : s
    ref_length = get_value(tixi,ref_length_xpath) # Mean aerodynamic chord: mac, different of mach (speed)
    # if wing span not stored in cpacs, then calculate it.

    wing_span_xpath = dynamic_analysis_xpath + '/largestSpan'
    if tixi.checkElement(wing_span_xpath) :
        b = get_value(tixi, wing_span_xpath)
    else :
        tigl = open_tigl(tixi)
        max_area, b  = get_largest_wing_dim(tixi,tigl) # Maximum wing area,  maximum span calulated in Skin friction module

    mac = s/b
    log.info('The mean aero chord calculated from wing area and span (S/b) is : {}'.format(mac_calculated))

    m = get_value(tixi,mass_xpath) # aircraft mass
    i_xx = get_value(tixi,i_xx_xpath) # X inertia
    i_yy = get_value(tixi,i_yy_xpath) # Y inertia
    i_zz = get_value(tixi,i_zz_xpath) # Z inertia

    Coeffs = get_aeromap(tixi, aeromap_uid)

    alt_list = Coeffs.alt
    mach_list = Coeffs.mach
    aoa_list = Coeffs.aoa
    aos_list = Coeffs.aos
    cl_list = Coeffs.cl
    cd_list = Coeffs.cd
    cd_list = Coeffs.cd
    cml_list = Coeffs.cml # For Directional
    cms_list = Coeffs.cms # For Longi
    cmd_list = Coeffs.cmd # For spiral
    dcmsdqstar_list = Coeffs.dcmsdqstar
    dcmldqstar_list = Coeffs.dcmldqstar
    dcmddpstar_list = Coeffs.dcmddpstar
    dcmldpstar_list = Coeffs.dcmldpstar
    dcmldrstar_list = Coeffs.dcmldrstar
    dcmddrstar_list = Coeffs.dcmddrstar

    # Initialise variables
    longi_data= []
    lat_dir_data = []
    cpacs_stability_short = True
    cpacs_stability_phugoid = True
    cpacs_stability_roll = True
    cpacs_stability_spiral = True
    cpacs_stability_dutch = True

    # All different allue with only one occurence
    alt_unic = get_unic(alt_list)
    mach_unic = get_unic(mach_list)
    aos_unic = get_unic(aos_list)
    aoa_unic = get_unic(aoa_list)

    for alt in alt_unic:
        idx_alt = [i for i in range(len(alt_list)) if alt_list[i] == alt]

        Atm = get_atmosphere(alt)
        g = Atm.grav # gravity acceleration at alt
        a = Atm.sos # speed of sound at alt
        rho = Atm.dens # air density at alt

        for mach in mach_unic:
            idx_mach = [i for i in range(len(mach_list)) if mach_list[i] == mach]
            u0 = a*mach # Trimm speed
            q = 0.5 * rho * u0**2 # Static pressure
            qs = q*s

            plot_damp_longi = []
            plot_freq_longi = []
            legend_longi = []

            plot_damp_dir = []
            plot_freq_dir = []
            legend_dir = []

            # Longitudinal dynamic stability, Hyp: trim condition when dcml/cbeta = 0 and do it for each AOA
            if short_analysis or phugoid_analysis:
                for aos in aos_unic:
                    print('AOS = ' + str(aos))
                    idx_aos = [i for i in range(len(aos_list)) if aos_list[i] == aos]
                    find_index = get_index(idx_alt, idx_mach, idx_aos)
                    # If there is only one data at (alt, mach, aos) then dont make stability anlysis
                    if len(find_index) == 1:
                        log.info('Only one data at : Alt = {} , mach = {}, aos = {} '.format(alt,mach,aos))
                    # If there is at leat 2 data at (alt, mach, aos) then, make stability anlysis
                    else:
                        # Find all cms_list values for index corresonding to an altitude, a mach, an aos_list=0, and different aoa_list
                        cms = []
                        aoa = []
                        cl = []
                        cd = []
                        dcmsdqstar = []

                        for index in find_index:
                            cms.append(cms_list[index])
                            aoa.append(aoa_list[index])
                            cl.append(cl_list[index])
                            cd.append(cd_list[index])
                            dcmsdqstar.append(dcmsdqstar_list[index])

                        # Trimm condition
                        trim_aoa, cms_alpha, idx_trim_before, idx_trim_after, ratio = trim_derivative(alt, mach, cms, aoa)
                        data = [alt, mach, aos,trim_aoa]
                        # Lift coefficient derivative with respect to AOA at trimm
                        cl_alpha = (cl[idx_trim_after] - cl[idx_trim_before]) / (aoa[idx_trim_after] - aoa[idx_trim_before])

                        cd0 =interpolation(cd, idx_trim_before, idx_trim_after, ratio) # Dragg coeff at trim
                        cl0 =interpolation(cl, idx_trim_before, idx_trim_after, ratio) # Lift coeff at trim
                        dcmsdqstar0 = interpolation(dcmsdqstar, idx_trim_before, idx_trim_after, ratio)
                        cm_alpha = cms_alpha

                        # In litterature damping derivatives are calculated using rotational rates [rad/s], normalized by:
                        # Rate*ReferenceLength/(2*flow) speed whereas in ceasiom: Rate*ReferenceLength/flow
                        cm_q = dcmsdqstar0*2 # No need to multiply by mac/b for longitudinal moment coeff

                        if short_period :
                            short_damp , short_freq = short_period(u0, qs, m, i_yy, mac, cm_alpha,  cd0, cl_alpha, cm_q )
                            data.append(short_damp), data.append(short_freq)
                            if short_damp >= 0 :
                                log.warning('Alt = {}, Mach= {} & AOS = {}°, aircraft NOT stable in Short Period Mode'.format(alt, mach, aos))
                                cpacs_stability_short = False
                            else :
                                log.info('Alt = {}, Mach= {} & AOS = {}°, aircraft is stable in Short Period Mode'.format(alt, mach, aos))
                        else :
                            short_damp , short_freq = [0, 0]
                        if phugoid:
                            phug_damp, phug_freq = phugoid(u0, cd0, cl0, g)
                            data.append(phug_damp), data.append(phug_freq)
                            if phug_damp >= 0 :
                                log.warning('Alt = {}, Mach= {} & AOS = {}°, aircraft NOT stable in Phugoid Mode'.format(alt, mach, aos))
                                cpacs_stability_phugoid = False
                            else:
                                log.info('Alt = {}, Mach= {} & AOS = {}°, aircraft is stable in Phugoid Mode'.format(alt, mach, aos))
                        else:
                            phug_damp, phug_freq = [0, 0]

                        # For plotting :
                        longi_data.append(data)
                        plot_damp_longi.append([short_damp, phug_damp])
                        plot_freq_longi.append([short_freq, phug_freq])
                        legend_longi.append('AOS = ' + str(aos) +r', $\alpha_{trim}$ = '+ str(trim_aoa) + '°')
                # Plots longi  for Alt Mach and different Aos  Im Vs Real    for diff
                # @ Alt MAch in legend all the different AOS, and the trimm AOA
                if plot_damp_longi:
                    title_longi = 'Alt = {} , Mach = {}, and different AOS'.format(alt, mach)
                    plot_multicurve(analysis, plot_damp_longi, plot_freq_longi,  legend_longi, title_longi, 'Re', 'Im', show_plots, save_plots)

            # Directional,  Hyp: trim condition when dcml/cbeta = 0 and do it for each AOA
            if roll_analysis or spiral_analysis or dutch_analysis:
                for aoa in aoa_unic :
                    idx_aoa = [i for i in range(len(aoa_list)) if aoa_list[i] == aoa]
                    find_index = get_index(idx_alt, idx_mach,  idx_aoa)

                    # If there is only one data at (alt, mach, aos) then dont make stability anlysis
                    if len(find_index) == 1:
                        log.info('Only one data at : Alt = {} , mach = {}, aoa = {} '.format(alt,mach,aos))
                    # If there is at leat 2 data at (alt, mach, aos) then, stability anlysis
                    else:
                        # Find all cms_list values for index corresonding to an altitude, a mach, an aos_list=0, and different aoa_list
                        cml = []
                        cmd = []
                        aos = []
                        cl = []
                        cd = []
                        dcmddpstar = []
                        dcmldqstar = []
                        dcmldpstar = []
                        dcmldrstar = []
                        dcmddrstar = []

                        for index in find_index:
                            cml.append(cml_list[index])
                            cmd.append(cmd_list[index])
                            aos.append(aos_list[index])
                            dcmddpstar.append(dcmddpstar_list[index]) # For Roll
                            dcmldpstar.append(dcmldpstar_list[index]) # For Roll
                            dcmldrstar.append(dcmldrstar_list[index])
                            dcmddrstar.append(dcmddrstar_list[index])

                        # Trimm condition
                        trim_aos, cml_alpha, idx_trim_before, idx_trim_after, ratio = trim_derivative(alt, mach, cml, aos)
                        data = [alt, mach, aoa, trim_aos]
                        # Roll Mode
                        dcmddpstar0  = interpolation(dcmddpstar, idx_trim_before, idx_trim_after, ratio) # For Roll
                        dcmldpstar0 = interpolation(dcmldpstar, idx_trim_before, idx_trim_after, ratio) # For Roll

                        # In litterature damping derivatives are calculated using rotational rates [rad/s], normalized by:
                        # Rate*ReferenceLength/(2*flow) speed whereas in ceasiom: Rate*ReferenceLength/flow
                        cl_p = dcmddpstar0*2*mac/b #  L moment derrivative, For Roll
                        cn_p = dcmldpstar0*2 *mac/b # N moment derrivative,  For Roll

                        if roll_analysis:
                            roll_damp, roll_freq = roll(u0, qs, i_xx, i_zz, b, cl_p, cn_p)
                            data.append(roll_damp), data.append(roll_freq)
                            if roll_damp >= 0 :
                                cpacs_stability_roll = False
                                log.warning('Alt = {}, Mach= {} & AOA = {}°, aircraft NOT stable in Roll Mode'.format(alt, mach, aoa))
                            else:
                                log.info('Alt = {}, Mach= {} & AOA = {}°, aircraft is stable in Roll Mode'.format(alt, mach, aoa))
                        else:
                            roll_damp, roll_freq = [0, 0]

                        # Spiral Mode
                        dcmldrstar0 =  interpolation(dcmldrstar, idx_trim_before, idx_trim_after, ratio)
                        dcmddrstar0 =  interpolation(dcmddrstar, idx_trim_before, idx_trim_after, ratio)

                        # In litterature damping derivatives are calculated using rotational rates [rad/s], normalized by:
                        # Rate*ReferenceLength/(2*flow) speed whereas in ceasiom: Rate*ReferenceLength/flow
                        cn_r = dcmldrstar0*2*mac/b
                        cl_r = dcmddrstar0*2*mac/b
                        # L & N moment derivative against beta in conventional , respectively  cmd & cml ceasiompy
                        cmd_beta = (cmd[idx_trim_after] - cmd[idx_trim_before]) / (aos[idx_trim_after] - aos[idx_trim_before])
                        cml_beta = (cml[idx_trim_after] - cml[idx_trim_before]) / (aos[idx_trim_after] - aos[idx_trim_before])
                        # L moment derivative in litterature
                        cl_beta = cmd_beta*mac/b
                        cn_beta = cml_beta*mac/b

                        if spiral_analysis :
                            spiral_damp, spiral_freq = spiral(u0, qs, b, i_xx, i_yy, cn_r, cl_r, cl_beta, cn_beta)
                            data.append(spiral_damp), data.append(spiral_freq)
                            if spiral_damp >= 0 :
                                cpacs_stability_spiral = False
                                log.warning('Alt = {}, Mach= {} & AOA = {}°, aircraft NOT stable in Spiral Mode'.format(alt, mach, aoa))
                            else:
                                log.info('Alt = {}, Mach= {} & AOA = {}°, aircraft is stable in Roll Mode'.format(alt, mach, aoa))
                        else :
                            spiral_damp, spiral_freq = [0, 0]

                        # Dutch Roll: all coefficients are already found ,  dutch roll : combination of spiral and roll
                        if dutch_analysis :
                            dutch_damp, dutch_freq =dutch_roll(u0, qs, b, i_xx, i_zz, cl_p, cl_r, cl_beta , cn_p, cn_r, cn_beta)
                            data.append(dutch_damp), data.append(dutch_freq)
                            if dutch_damp >= 0 :
                                log.warning('Alt = {}, Mach= {} & AOA = {}°, aircraft NOT stable in Dutch-Roll Mode'.format(alt, mach, aoa))
                                cpacs_stability_dutch = False
                            else:
                                log.info('Alt = {}, Mach= {} & AOA = {}°, aircraft is stable in Roll Mode'.format(alt, mach, aoa))
                        else:
                            dutch_damp, dutch_freq = [0, 0]

                        # For plotting
                        lat_dir_data.append(data)
                        plot_damp_dir.append([roll_damp, spiral_damp, dutch_damp])
                        plot_freq_dir.append([roll_freq, spiral_freq, dutch_freq])
                        legend_dir.append('AOA = ' + str(aoa) + r'°, $\beta_{trim}$ = ' + str(trim_aos) + '°')
                # If there is at least one curve to plot , plot_damp_dir is not empty
                if plot_damp_dir:
                    # Plot Directionnal-Lateral for Alt Mach and different aoa
                    title_dir = 'Alt = {} , mach = {}, and different AOA'.format(alt, mach)
                    plot_multicurve(analysis, plot_damp_dir, plot_freq_dir,  legend_dir, title_dir, 'Re', 'Im', show_plots, save_plots)

    # Graphs for Alt, AOS-AOA and different mach
    # Longi
    if short_analysis or phugoid_analysis :
        for alt in alt_unic :
            plot_damp_longi = []
            plot_freq_longi = []
            legend_longi = []
            #idx_alt = [i for i in range(len(longi_data)) if longi_data[i][0] == alt]
            for aos in aos_unic :
                # idx_aos= [i for i in range(len(longi_data)) if longi_data[i][2] == aos]
                for mach in mach_unic :
                    # idx_mach= [i for i in range(len(longi_data)) if longi_data[i][1] == mach]
                    for data in longi_data :
                        if data[0] == alt and data[1] == mach and data[2] == aos :
                            # Get the data to plot in the element of longi_data at (alt, mach, aos)
                            # index = get_index(idx_alt, idx_aos,idx_mach)[0] # will return one index
                            # print('index' + str(index))

                            # trim_aoa = longi_data[index][3]
                            # short_damp = longi_data[index][4]
                            # short_freq = longi_data[index][5]
                            # phugoid_damp = longi_data[index][6]
                            # phugoid_freq = aeromap_uidlongi_data[index][7]
                            trim_aoa = data[3]
                            short_damp = data[4]
                            short_freq = data[5]
                            phugoid_damp = data[6]
                            phugoid_freq = data[7]
                            # Prepare for plotting
                            plot_damp_longi.append([short_damp, phug_damp])
                            plot_freq_longi.append([short_freq, phug_freq])
                            legend_longi.append('mach = ' + str(mach) + r', $\alpha_{trim}$ = ' + str(trim_aoa) + '°')
            title_longi = 'Alt = {} , AOS= {}°, and different mach'.format(alt, aos)
            plot_multicurve(analysis, plot_damp_longi, plot_freq_longi,  legend_longi, title_longi, 'Re', 'Im', show_plots, save_plots)
    # Directional-Lateral
    if roll_analysis or spiral_analysis  or dutch_analysis :
        for alt in alt_unic :
            plot_damp_dir = []
            plot_freq_dir = []
            legend_dir = []
            for aoa in aoa_unic :
                for mach in mach_unic :
                    for data in lat_dir_data :
                        if data[0] == alt and data[1] == mach and data[2] == aoa :
                            # Get the data to plot in the element of lat_dir_data at (alt, mach, aos)
                            trim_aos = data[3]
                            roll_damp = data[4]
                            roll_freq = data[5]
                            spiral_damp = data[6]
                            spiral_freq = data[7]
                            dutchl_damp = data[8]
                            dutch_freq = data[9]
                            # Prepare for plotting
                            plot_damp_dir.append([roll_damp, spiral_damp, dutch_damp])
                            plot_freq_dir.append([roll_freq, spiral_freq, dutch_freq])
                            legend_dir.append('mach = ' + str(mach) + r', $\beta_{trim}$ = ' + str(trim_aos) + '°' )
            # Plot Directionnal-Lateral for Alt Mach and different aoa
            title_dir = 'Alt = {} , AOA = {}°, and different mach'.format(alt, aoa)
            plot_multicurve(analysis, plot_damp_dir, plot_freq_dir,  legend_dir, title_dir, 'Re', 'Im', show_plots, save_plots)

    # Graphs for mach, AOS-AOA and different alt
    # Longi
    if short_analysis or phugoid_analysis :
        for mach in mach_unic :
            plot_damp_longi = []
            plot_freq_longi = []
            legend_longi = []
            for aos in aos_unic :
                for alt in alt_unic :
                    for data in longi_data :
                        if data[0] == alt and data[1] == mach and data[2] == aos :
                            # Get the data to plot in the element of longi_data at (alt, mach, aos)
                            trim_aoa = data[3]
                            short_damp = data[4]
                            short_freq = data[5]
                            phugoid_damp = data[6]
                            phugoid_freq = data[7]
                            # Prepare for plotting
                            plot_damp_longi.append([short_damp, phug_damp])
                            plot_freq_longi.append([short_freq, phug_freq])
                            legend_longi.append('alt = ' + str(alt) + r', $\alpha_{trim}$ = ' + str(trim_aoa) + '°')
            title_longi = 'Mach= {} , AOS= {}°, and different AOS'.format(mach, aos)
            plot_multicurve(analysis, plot_damp_longi, plot_freq_longi,  legend_longi, title_longi, 'Re', 'Im', show_plots, save_plots)
    # Directional-Lateral
    if roll_analysis or spiral_analysis  or dutch_analysis :
        for mach in mach_unic :
            plot_damp_dir = []
            plot_freq_dir = []
            legend_dir = []
            for aoa in aoa_unic :
                for alt in alt_unic :
                    for data in lat_dir_data :
                        if data[0] == alt and data[1] == mach and data[2] == aoa :
                            # Get the data to plot in the element of lat_dir_data at (alt, mach, aos)
                            trim_aos = data[3]
                            roll_damp = data[4]
                            roll_freq = data[5]
                            spiral_damp = data[6]
                            spiral_freq = data[7]
                            dutchl_damp = data[8]
                            dutch_freq = data[9]
                            # Prepare for plotting
                            plot_damp_dir.append([roll_damp, spiral_damp, dutch_damp])
                            plot_freq_dir.append([roll_freq, spiral_freq, dutch_freq])
                            legend_dir.append('mach = ' + str(mach) + r', $\beta_{trim}$ = ' + str(trim_aos) + '°')
            # Plot Directionnal-Lateral for Alt Mach and different aoa
            title_dir = 'mach= {} , AOA = {}°, and different alt'.format(mach, aoa)
            plot_multicurve(analysis, plot_damp_dir, plot_freq_dir,  legend_dir, title_dir, 'Re', 'Im', show_plots, save_plots)
    # Save results:
    # xpath definition for saving results
    short_xpath = aeromap_uid_xpath + '/results/shortPeriodStable'
    phugoid_xpath = aeromap_uid_xpath + '/results/phugoidStable'
    roll_xpath = aeromap_uid_xpath + '/results/rollStable'
    spiral_xpath = aeromap_uid_xpath + '/results/spiralPeriodStable'
    dutch_xpath = aeromap_uid_xpath + '/results/dutchRollStable'
    # CPACS brench
    create_branch(tixi, short_xpath )
    create_branch(tixi, phugoid_xpath)
    create_branch(tixi, roll_xpath)
    create_branch(tixi, spiral_xpath )
    create_branch(tixi, dutch_xpath )
    # Store results in CPACS
    if short_analysis :
        tixi.updateTextElement(short_xpath, str(cpacs_stability_short))
    else:
        tixi.updateTextElement(short_xpath, str('notAnalysed'))
    if phugoid_analysis :
        tixi.updateTextElement(phugoid_xpath, str(cpacs_stability_phugoid))
    else:
        tixi.updateTextElement(phugoid_xpath, str('notAnalysed'))
    if roll_analysis:
        tixi.updateTextElement(roll_xpath, str(cpacs_stability_roll))
    else:
        tixi.updateTextElement(roll_xpath, str('notAnalysed'))
    if spiral_analysis:
        tixi.updateTextElement(spiral_xpath, str(cpacs_stability_spiral))
    else:
        tixi.updateTextElement(spiral_xpath, str('notAnalysed'))
    if dutch_analysis:
        tixi.updateTextElement(dutch_xpath, str(cpacs_stability_dutch))
    else:
        tixi.updateTextElement(dutch_xpath, str('notAnalysed'))

    close_tixi(tixi, cpacs_out_path)


#==============================================================================
#    MAIN
#==============================================================================


# if __name__ == '__main__':
#
#     log.info('----- Start of ' + MODULE_NAME + ' -----')
#
#     cpacs_path = get_toolinput_file_path(MODULE_NAME)
#     cpacs_out_path = get_tooloutput_file_path(MODULE_NAME)
#
#     # Call the function which check if imputs are well define
#     check_cpacs_input_requirements(cpacs_path)
#
#     # Call the main function for static stability analysis
#     static_stability_analysis(cpacs_path, cpacs_out_path)
#
#     log.info('----- End of ' + MODULE_NAME + ' -----')


# ############## Main #########
# MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
# cpacs_path = MODULE_DIR  + '/toolInput/toolInput.xml'
# cpacs_out_path = MODULE_DIR  + '/toolOuput/toolOutput.xml'
# dynamic_stability_analysis(cpacs_path, cpacs_out_path)
