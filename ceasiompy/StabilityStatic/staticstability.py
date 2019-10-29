"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Static stability module

Python version: >=3.6

| Author: Verdier Loïc
| Creation: 2019-10-24
| Last modifiction: 2019-10-24

TODO:
    * Determine the inputs
    * Remove the print once tests have been complteted
    * how to save the results
    *
"""

#==============================================================================
#   IMPORTS
#==============================================================================

import os
import sys
import time
import math
import numpy as np
import matplotlib as mpl
import matplotlib.patheffects
import matplotlib.pyplot as plt

import pandas as pd

from ceasiompy.utils.ceasiomlogger import get_logger
from ceasiompy.utils.cpacsfunctions import open_tixi, open_tigl, close_tixi,   \
                                           add_uid, create_branch, copy_branch,\
                                           get_value, get_value_or_default,    \
                                           aircraft_name
from ceasiompy.utils.mathfunctions import euler2fix, fix2euler
from ceasiompy.utils.standardatmosphere import get_atmosphere, plot_atmosphere
from ceasiompy.utils.moduleinterfaces import check_cpacs_input_requirements
from ceasiompy.utils.apmfunctions import aeromap_to_csv, get_aeromap_uid_list, aeromap_from_csv, get_aeromap


from ceasiompy.utils.ceasiomlogger import get_logger

from ceasiompy.utils.cpacsfunctions import open_tixi, open_tigl, close_tixi,   \
    create_branch, copy_branch, add_uid,\
    get_value, get_value_or_default,    \
    add_float_vector, get_float_vector, \
    add_string_vector, get_string_vector

log = get_logger(__file__.split('.')[0])

#==============================================================================
#   FUNCTIONS
#==============================================================================

def plot_torque_vs_angle(y_axis, x_axis, plot_legend, plot_title, xlabel, ylabel):
    """Function to plot graph with different curves for a varying parameter

    Function 'plot_torque_vs_angle' can plot few curves

    Args:
        x_axis : list of vector of each curve's X coordinates
        y axis: : list of vector of each curve's Y coordinates
        the list of the leggends of all the different curves: Lgend_list
        The plot title
        the x label
        the y label

    Returns:
        A plot with different curves if asked.
    """
    fig = plt.figure(figsize=(9, 3))
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.title(plot_title, fontdict=None, loc='center', pad=None)

    for n in range(len(x_axis)):
        plt.plot(x_axis[n], y_axis[n], marker='o', markersize=4, linewidth=1)
        # Find x and y axis limits
        if n==0 :
            y_max = max(y_axis[0])
            y_min = min(y_axis[0])
            x_max = max(x_axis[0])
            x_min = min(x_axis[0])
        if n >0  and max(y_axis[n]) > y_max :
            y_max = max(y_axis[n])
        if n >0  and min(y_axis[n]) < y_min :
            y_min  = min(y_axis[n])
        if n >0  and max(x_axis[n]) > x_max :
            x_max = max(x_axis[n])
        if n >0  and min(x_axis[n]) < x_min :
            x_min = min(x_axis[n])

    ax = plt.gca()
    # Remove Top and right axes
    ax.spines['right'].set_color('none')
    ax.spines['top'].set_color('none')
    #Locate horizontal axis in a coherent way
    if y_max < 0 :
        ax.spines['bottom'].set_position(('axes',1))
    elif y_min > 0 :
        ax.spines['bottom'].set_position(('axes',0))
    elif len(np.argwhere(np.diff(np.sign([y_min, y_max])))) != 0 :
        ax.spines['bottom'].set_position(('data',0))

    #Locate vertical axis in a coherent way
    if x_max < 0 :
        ax.spines['left'].set_position(('axes',1))
    elif x_min > 0 :
        ax.spines['left'].set_position(('axes',0))
    elif len(np.argwhere(np.diff(np.sign([x_min, x_max])))) != 0 :
        ax.spines['left'].set_position(('data',0))

    #Legend
    ax.legend(plot_legend, loc='upper right')

    plt.show()

def static_stability_analysis(cpacs_path, aeromap_uid):
    """Function to analyse a full Aeromap

    Longitudinal static staticStabilityAnalysis
    Directionnal static analysis

    Args:
        Cpacs file paths
        Aeromap uid

    Returns:
        *   Adrvertisements certifying if the aircraft is stable or Not
        *   In case of longitudinal static UNstability or unvalid test on data:
                -	Plot cml VS aoa for constant Alt, Mach and different aos
                -	Plot cml VS aoa for const alt and aos and different mach
                -	plot cml VS aoa for constant mach, AOS and different altitudes
        *  In case of directionnal static UNstability or unvalid test on data:
                -	Pcot cms VS aos for constant Alt, Mach and different aoa
                -	Plot cms VS aos for const alt and aoa and different mach
                -	plot cms VS aos for constant mach, AOA and different altitudes
        *  Plot one graph of  cruising angles of attack for different mach and altitudes

    Make the following tests:
        *   Check the CPACS path
        *   For longitudinal static stability analysis:
                -   If there is more than one angle of attack for a given altitude, mach, aos
                -   If cml values are only zeros for a given altitude, mach, aos
                -   If there one aoa value which is repeated for a given altitude, mach, aos
        *   For directionnal static stability analysis:
                -   If there is more than one angle of sideslip for a given altitude, mach, aoa
                -   If cml values are only zeros for a given altitude, mach, aoa
                -   If there one aos value which is repeated for a given altitude, mach, aoa
    """

    # Call the function which check if imputs are well define
    check_cpacs_input_requirements(cpacs_path)
    #Open tixi handles
    tixi = open_tixi(cpacs_path)
    # Coeffs lists
    Coeffs = get_aeromap(tixi, aeromap_uid)

    alt_list = Coeffs.alt
    mach_list = Coeffs.mach

    aoa_list = Coeffs.aoa
    cml_list = Coeffs.cml

    aos_list = Coeffs.aos
    cms_list = Coeffs.cms


    alt_unic = []
    mach_unic = []
    aos_unic = []
    aoa_unic = []

    for element in alt_list:
        if element not in alt_unic :
            alt_unic.append(element)

    for element in mach_list :
        if element not in mach_unic :
            mach_unic.append(element)

    for element in aos_list :
        if element not in aos_unic :
            aos_unic.append(element)

    for element in aoa_list:
        if element not in aoa_unic :
            aoa_unic.append(element)

    # Init Plot variables : trim Aoa for gien alt and different mach
    #                                  trim Aoa for gien Mach and different alt
    # Gather trim aoa_list for different Alt & mach , for aos = 0
    trim_aoa_list = []
    trim_mach_list = []
    trim_legend_list = []
    longi_unstable_cases = []
    direc_unstable_cases = []

    # Aero analyses for all given Altitude, Mach and aos_list, over different
    for alt in alt_unic:
        print("*****Alt : " + str(alt))
        # Find index of altitude which have the same value
        idx_alt = [i for i in range(len(alt_list)) if alt_list[i] == alt]

        # Prepar trim condition lists
        trim_aoa =[]
        trim_mach = []
        trim_legend = []

        for mach in mach_unic:
            print("***mach_list : " + str(mach))
            # Find index of mach which have the same value
            idx_mach = [j for j in range(len(mach_list)) if mach_list[j] == mach]

    # Longitudinal stability
            count_aos = 0
        # Analyse in function of  the angle of attack for given, Alt, Mach and aos_list
            # Prepare variables for plots
            plot_cml = []
            plot_aoa = []
            plot_legend = []
            plot_title = 'Cml vs aoa, @Atl = ' + str(alt) + ' and Mach = ' + str(mach)
            xlabel= 'aoa'
            ylabel= 'Cml'
            # Init for determining if it's an unstable case
            longitudinaly_stable = True
            # Find index of slip angle which have the same value

            for aos in aos_unic:
                # by default, don't  cross 0 line
                crossed = False
                print("**aos_list: " + str(count_aos))
                count_aos += 1
                idx_aos = [k for k in range(len(aos_list)) if aos_list[k] == aos]
                # List of index of elements which have the same index  in vectors alt_list, mach_list, aos_list
                find_idx = []
                # Fill   the liste find_index
                for idx1 in idx_alt:
                    for idx2 in idx_mach:
                        for idx3 in idx_aos:
                            if idx1 == idx2 == idx3:
                                find_idx.append(idx1)

                # If find_idx is empty an APM function would have corrected before
                # If there there is only one value  in  find_idx for a given Alt, Mach, aos_list, no analyse can be performed
                if len(find_idx) == 1:
                    log.info('Only one data, one aoa(' +str(aoa_list[idx1])+ '), for Altitude =  '+ str(alt) +
                             ' , Mach = ' + str(mach) + '  and aos = ' + str(aos) + '  no stability analyse performed' )
                # If there is at least 2 values in find_idx :
                if len(find_idx) > 1:
                    # Find all cml_list values for index corresonding to an altitude, a mach, an aos_list=0, and different aoa_list
                    cml = []
                    aoa = []
                    for index in find_idx:
                        cml.append(cml_list[index])
                        aoa.append(aoa_list[index])

                    curve_legend = 'aos = '+ str(aos) + '°'

                    # Store  Cml values in cml_list
                    plot_cml.append(cml)
                    # Store list_attack in list_list_attack
                    plot_aoa.append(aoa)
                    # Store the legend in plot_legend
                    plot_legend.append(curve_legend)

                    # If all aoa values are the same while the calculating the derivative, a division by zero will be prevented.
                    aoa_good = True
                    for jj in range(len(aoa)-1) :
                        if  aoa[jj] == aoa[jj+1] and  aoa_good == True :
                                aoa_good = False
                                log.warning(' At least 2 aoa values are equal in aoa list: {} at Alt = {}, Mach= {}, aos = {}' .format(aoa, alt, mach, aos))
                    # retrieve the index in of element in cml just before crossing 0,
                    # np.argwher returns an array as [[idx]], that'a why there is [0][0] at the end
                    # If cml curve does not cross the 0
                    if len(np.argwhere(np.diff(np.sign(cml)))) == 0  :
                        # If all Cml values are 0:
                        longitudinaly_stable = False
                        longi_unstable_cases.append([alt,mach,aos])
                        if cml.count(0) == len(cml):
                            log.info('Cml list is composed of 0 only.' )
                        else:
                            log.info('The aircraft has a cruising aoa_list at which Cml is not 0.' )
                    # If cml Curve crosses the 0 line more than once no stability analysis can be performed
                    if len(np.argwhere(np.diff(np.sign(cml)))) > 2 or cml.count(0) > 1:
                        log.info('The Cml curves crosses more than once the 0 line, no stability analysis performed')
                        longitudinaly_stable = False
                        longi_unstable_cases.append([alt,mach,aos])
                    # If cml Curve crosses the 0 line twice
                    if 0 not in np.sign(cml) and len(np.argwhere(np.diff(np.sign(cml)))) == 2:
                        log.info('The Cml curves crosses the 0 line twice, no stability analysis performed')
                        longitudinaly_stable = False
                        longi_unstable_cases.append([alt,mach,aos])
                    # If Cml = 0 is in Cml list  only once
                    if 0 in np.sign(cml) and cml.count(0) == 1 and aoa_good == True:
                        idx_cml_0 = [i for i in range(len(cml)) if cml[i] == 0][0]

                        # If Cml = 0 is the first element in cml list, take the derivative at right
                        if idx_cml_0 == 0:
                            # Angles and coeffs before and after crossing the 0 line
                            aoa_before = aoa_list[find_idx[idx_cml_0]]
                            aoa_after = aoa_list[find_idx[idx_cml_0+1]]
                            cml_before = cml_list[find_idx[idx_cml_0]]
                            cml_after = cml_list[find_idx[idx_cml_0+1]]

                            cruise_aoa = aoa_before
                            pitch_moment_derivative = (cml_after-cml_before)/(aoa_after-aoa_before)

                        # If cml = 0 is the last element of cml list, take the derivative at left
                        if idx_cml_0 == len(cml)-1:
                            # Angles and coeffs before and after crossing the 0 line
                            aoa_before = aoa_list[find_idx[idx_cml_0-1]]
                            aoa_after = aoa_list[find_idx[idx_cml_0]]
                            cml_before = cml_list[find_idx[idx_cml_0-1]]
                            cml_after = cml_list[find_idx[idx_cml_0]]

                            cruise_aoa = aoa_after
                            pitch_moment_derivative = (cml_after-cml_before)/(aoa_after-aoa_before)

                        # If cml = 0 is nor the first nor the last element in cml list, take the centered derivative
                        if 0 < idx_cml_0 < len(cml)-1:
                            # Angles and coeffs before and after crossing the 0 line
                            aoa_before = aoa_list[find_idx[idx_cml_0-1]]
                            aoa_after = aoa_list[find_idx[idx_cml_0+1]]
                            cml_before = cml_list[find_idx[idx_cml_0-1]]
                            cml_after = cml_list[find_idx[idx_cml_0+1]]

                            cruise_aoa = aoa_list[find_idx[idx_cml_0]]
                            pitch_moment_derivative = (cml_after-cml_before)/(aoa_after-aoa_before)
                    # If Cml crosses the 0 line once and Cml=0 is not in cml list
                    if  len(np.argwhere(np.diff(np.sign(cml)))) == 1 and 0 not in np.sign(cml) and aoa_good == True:
                        # Make the linear equation btween the 2 point before and after crossing lthe 0 ine y=ax+b
                        crossed = True
                        idx_cml_0 = np.argwhere(np.diff(np.sign(cml)))[0][0]

                        # Angles and coeffs before and after crossing the 0 line
                        aoa_before = aoa_list[find_idx[idx_cml_0]]
                        aoa_after = aoa_list[find_idx[idx_cml_0+1]]

                        cml_before = cml_list[find_idx[idx_cml_0]]
                        cml_after = cml_list[find_idx[idx_cml_0+1]]

                        fit = np.polyfit([aoa_before, aoa_after], [cml_before, cml_after], 1)  # returns [a,b] of y=ax+b
                        cruise_aoa = -fit[1]/fit[0]    # Cml = 0 for y = 0  hence cruise agngle = -b/a
                        pitch_moment_derivative = fit[0]

                    if aos == 0 and crossed == True and aoa_good == True and pitch_moment_derivative < 0:
                        trim_mach.append(mach)
                        trim_aoa.append(cruise_aoa)

                    if crossed== True and aoa_good == True:
                        if pitch_moment_derivative < 0 :
                            log.info('Vehicle longitudinaly staticaly stable.')
                        if pitch_moment_derivative == 0 :
                            longitudinaly_stable = False
                            longi_unstable_cases.append([alt,mach,aos])
                            log.info('Vehicle longitudinaly staticaly neutral stable.')
                        if pitch_moment_derivative > 0 :
                            longitudinaly_stable = False
                            longi_unstable_cases.append([alt,mach,aos])
                            log.info('Vehicle *NOT* longitudinaly staticaly stable.')
            #print( LongitudinalyStable)
            if  longitudinaly_stable == False :
                # PLot Cml VS aoa for constant Alt, Mach and different aos
                plot_torque_vs_angle( plot_cml, plot_aoa, plot_legend, plot_title, xlabel, ylabel)

    # Dirrectional Stability analysis
            count_aoa = 0

            plot_cms = []
            plot_aos = []
            plot_legend = []
            plot_title = 'Cms vs aos, @Atl = ' + str(alt) + ' and Mach = ' + str(mach)
            xlabel= 'aos'
            ylabel= 'Cms'
            # Init for determinig if it is an unstability case
            dirrectionaly_stable = True
            # Find INDEX
            for aoa in aoa_unic:
                # by default, don't  cross 0 line
                crossed = False
                print('**aoa_list: ' + str(count_aoa))
                count_aoa += 1
                idx_aoa = [jj for jj in range(len(aoa_list)) if aoa_list[jj] == aoa]
                # List of index of elements which have the same index  in vectors alt_list, mach_list, aos_list
                find_idx = []
                # Fill   the liste find_index
                for idx1 in idx_alt:
                    for idx2 in idx_mach:
                        for idx3 in idx_aoa:
                            if idx1 == idx2 == idx3:
                                find_idx.append(idx1)

                # If find_idx is empty an APM function would have corrected before
                # If there there is only one value  in  find_idx for a given Alt, Mach, aos_list, no analyse can be performed
                if len(find_idx) == 1:
                    log.info('Only one data, one aos (' +str(aos_list[idx1])+'), for Altitude = ' + str(alt) +
                             ' , Mach = ' + str(mach) + ' and aoa = ' + str(aoa) + ' no stability analyse performed')
                # If there is at list 2 values in find_idx :
                if len(find_idx) > 1:
                    cms = []
                    aos = []
                    for index in find_idx:
                        cms.append(cms_list[index])
                        aos.append(aos_list[index])

                    # retrieve the index in of element in cml just before crossing 0,
                    # np.argwher returns an array as [[idx]], that'a why there is [0][0] at the end
                    #  If cms Curve crosses th 0 line more than once na stability analysis can be performed
                    curve_legend = 'aoa = ' + str(aoa) + '°'
                    # Store  Cms values in cml_list
                    plot_cms.append(cms)
                    # Store the list of aos  in plot_aos
                    plot_aos.append(aos)
                    # Store the legend in plot_legend
                    plot_legend.append(curve_legend)

                    # If all aoa values are the same while the calculating the derivative, a division by zero will be prevented.
                    aos_good = True
                    for jj in range(len(aos)-1) :
                        if  aos[jj] == aos[jj+1] and  aos_good == True :
                            aos_good = False
                            log.warning('At least 2 values are equal in aos list: {} at Alt = {}, Mach= {}, aoa = {}, dividing by zero while derivating, no stability analyse performed'.format(aos, alt, mach, aoa))
                    # If cml curve does not cross the 0
                    if len(np.argwhere(np.diff(np.sign(cms)))) == 0  :
                        dirrectionaly_stable = False
                        direc_unstable_cases.append([alt, mach, aoa])
                        # If all Cms values are 0:
                        if cms.count(0) == len(cms):
                            log.info('Cms list is composed of 0 only.')
                        else:
                            log.info('The aircraft has a cruising aos_list at which Cms is not 0.')
                    # If cms Curve crosses the 0 line more than once no stability analysis can be performed
                    if len(np.argwhere(np.diff(np.sign(cms)))) > 2 or cms.count(0) > 1:
                        dirrectionaly_stable = False
                        direc_unstable_cases.append([alt, mach, aoa])
                        log.info('The Cms curves crosses more than once the 0 line, no stability analysis performed')
                    # If cms Curve crosses the 0 line twice
                    if 0 not in np.sign(cms) and len(np.argwhere(np.diff(np.sign(cms)))) == 2:
                        dirrectionaly_stable = False
                        direc_unstable_cases.append([alt, mach, aoa])
                        log.info('The Cms curves crosses the 0 line twice, no stability analysis performed')
                    # If Cms = 0 is in Cml list
                    if 0 in np.sign(cms) and cms.count(0) == 1 and aos_good == True:
                        crossed = True
                        idx_cms_0 = [i for i in range(len(cms)) if cms[i] == 0][0]
                        # If Cml = 0 is the first element in cml list, take the derivative at right
                        if idx_cms_0 == 0:
                            # Angles and coeffs before and after crossing the 0 line
                            aos_before = aos_list[find_idx[idx_cms_0]]
                            aos_after = aos_list[find_idx[idx_cms_0+1]]
                            cms_before = cms_list[find_idx[idx_cms_0]]
                            cms_after = cms_list[find_idx[idx_cms_0+1]]

                            cruise_aos = aos_before
                            side_moment_derivative = (cms_after-cms_before)/(aos_after-aos_before)

                        # If cml = 0 is the last element of cml list, take the derivative at left
                        if idx_cms_0 == len(cms) - 1:
                            # Angles and coeffs before and after crossing the 0 line
                            aos_before = aos_list[find_idx[idx_cms_0-1]]
                            aos_after = aos_list[find_idx[idx_cms_0]]
                            cms_before = cms_list[find_idx[idx_cms_0-1]]
                            cms_after = cms_list[find_idx[idx_cms_0]]

                            cruise_aos = aos_after
                            side_moment_derivative = (cms_after-cms_before)/(aos_after-aos_before)

                        # If cml = 0 is nor the first nor the last element in cml list, take the centered derivative
                        if 0 < idx_cms_0 < len(cms)-1:
                            # Angles and coeffs before and after crossing the 0 line
                            aos_before = aos_list[find_idx[idx_cms_0-1]]
                            aos_after = aos_list[find_idx[idx_cms_0+1]]
                            cms_before = cms_list[find_idx[idx_cms_0-1]]
                            cms_after = cms_list[find_idx[idx_cms_0+1]]

                            cruise_aos = aos_list[find_idx[idx_cms_0]]
                            side_moment_derivative = (cms_after - cms_before)/(aos_after - aos_before)
                    # If Cms crosses the 0 line once and Cms=0 is not in cml list
                    if  len(np.argwhere(np.diff(np.sign(cms)))) == 1 and 0 not in np.sign(cms) and aos_good == True:
                        # Make the linear equation btween the 2 point before and after crossing the 0 ine y=ax+b
                        crossed = True
                        idx_cms_0 = np.argwhere(np.diff(np.sign(cms)))[0][0]

                        # Angles and coeffs before and after crossing the 0 line
                        aos_before = aos_list[find_idx[idx_cms_0]]
                        aos_after = aos_list[find_idx[idx_cms_0+1]]

                        cms_before = cms_list[find_idx[idx_cms_0]]
                        cms_after = cms_list[find_idx[idx_cms_0+1]]

                        fit = np.polyfit([aos_before, aos_after], [cms_before, cms_after], 1)  # returns [a,b] of y=ax+b
                        cruise_aos = -fit[1]/fit[0]    # Cms = 0 for y = 0  hence cruise agngle = -b/a
                        side_moment_derivative = fit[0]

                    if crossed == True and aos_good == True :
                        if side_moment_derivative > 0 :
                            log.info('Vehicle directionnaly staticaly stable.')
                        if side_moment_derivative == 0 :
                            dirrectionaly_stable = False
                            direc_unstable_cases.append([alt, mach, aoa])
                            log.info('Vehicle directionnaly staticaly neutral stable.')
                        if side_moment_derivative < 0 :
                            dirrectionaly_stable = False
                            direc_unstable_cases.append([alt, mach, aoa])
                            log.info('Vehicle *NOT* directionnaly staticaly stable.')

            if dirrectionaly_stable == False :
                # PLot Cms VS aos for constant Alt, Mach and different aoa
                plot_torque_vs_angle(plot_cms, plot_aos, plot_legend, plot_title, xlabel, ylabel)

        # Plot cml vs aoa for const alt and aos and different mach
        for aos in aos_unic:
            idx_aos = [k for k in range(len(aos_list)) if aos_list[k] == aos]
            plot_cml = []
            plot_aoa = []
            plot_legend= []
            plot_title = 'Cml vs aoa, @Atl = ' + str(alt) + ' and aos = ' + str(aos)
            xlabel= 'aoa'
            ylabel= 'Cml'
            # Init for determinig if it is an unstability case
            longitudinaly_stable = True

            for mach in mach_unic:
                idx_mach = [k for k in range(len(mach_list)) if mach_list[k] == mach]
                # List of index of elements which have the same index  in vectors alt_list, mach_list, aos_list
                find_idx = []
                # Fill   the liste find_index
                for idx1 in idx_alt:
                    for idx2 in idx_aos:
                        for idx3 in idx_mach:
                            if idx1 == idx2 == idx3:
                                find_idx.append(idx1)

                # If there is only one value in Find_idx
                # An error message has been already printed through the first part of the code
                # Check if it is an unstability case detected previously
                for combination in longi_unstable_cases :
                    if combination[0] == alt and combination[1] == mach and combination[2] == aos :
                        longitudinaly_stable = False

                # If there is at list 2 values in find_idx :
                if len(find_idx) > 1:
                    # Find all cml_list values for index corresonding to an altitude, a mach, an aos_list=0, and different aoa_list
                    cml = []
                    aoa = []
                    for index in find_idx:
                        cml.append(cml_list[index])
                        aoa.append(aoa_list[index])

                    curve_legend = 'Mach = ' + str(mach)

                    # Store  Cml values in cml_list
                    plot_cml.append(cml)
                    # Store list_attack in list_list_attack
                    plot_aoa.append(aoa)
                    # Store the legend in plot_legend
                    plot_legend.append(curve_legend)
            if longitudinaly_stable == False :
                #PLot Cml VS aoa for constant Alt, aoa and different mach
                plot_torque_vs_angle(plot_cml, plot_aoa, plot_legend, plot_title, xlabel, ylabel)

        # Plot cms vs aos for const alt and aoa and different mach
        for aoa in aoa_unic:
            idx_aoa = [k for k in range(len(aoa_list)) if aoa_list[k] == aoa]
            plot_cms = []
            plot_aos = []
            plot_legend = []
            plot_title  = 'Cms vs aos, @Atl = ' + str(alt) + ' and aoa = ' + str(aoa)
            xlabel = 'aos'
            ylabel = 'Cms'
            # Init for determinig if it is an unstability case
            dirrectionaly_stable = True

            for mach in mach_unic:
                idx_mach = [k for k in range(len(mach_list)) if mach_list[k] == mach]
                # List of index of elements which have the same index  in vectors alt_list, mach_list, aos_list
                find_idx = []
                # Fill   the liste find_index
                for idx1 in idx_alt:
                    for idx2 in idx_aoa:
                        for idx3 in idx_mach:
                            if idx1 == idx2 == idx3:
                                find_idx.append(idx1)

                #If there is only one valur in Find_idx
                # An error message has been already printed through the first part of the code

                # Check if it is an unstability case detected previously
                for combination in direc_unstable_cases :
                    if combination[0] == alt and combination[1] == mach and combination[2] == aoa :
                        dirrectionaly_stable = False

                # If there is at list 2 values in find_idx :
                if len(find_idx) > 1:
                    # Find all cml_list values for index corresonding to an altitude, a mach, an aos_list=0, and different aoa_list
                    cms = []
                    aos= []
                    for index in find_idx:
                        cms.append(cms_list[index])
                        aos.append(aos_list[index])

                    curve_legend = 'Mach = ' + str(mach)

                    # Store  Cml values in cml_list
                    plot_cms.append(cms)
                    # Store list_attack in list_list_attack
                    plot_aos.append(aos)
                    # Store the legend in plot_legend
                    plot_legend.append(curve_legend)

            if dirrectionaly_stable == False :
                # Plot Cms VS aos for constant Alt, aoa and different mach
                plot_torque_vs_angle(plot_cms, plot_aos, plot_legend, plot_title, xlabel, ylabel)

        # Add trim conditions for the given altitude
        if len(trim_aoa) > 0 :
            trim_aoa_list.append(trim_aoa)
            trim_mach_list.append(trim_mach)
            trim_legend_list.append('Alt = ' + str(alt))

    # Plot trim_aoa VS mach for different alt
    # If there is at least 1 element in list of trim conditions then, plot them
    if len(trim_aoa_list) >= 1:
        plot_torque_vs_angle(trim_aoa_list, trim_mach_list, trim_legend_list, 'trim_aoa VS mach', 'aoa','mach')

    # plot Cml VS aoa for constant mach, aos_list and different altitudes:
    for aos in aos_unic:
        # Find index of altitude which have the same value
        idx_aos = [i for i in range(len(aos_list)) if aos_list[i] == aos]
        for mach in mach_unic:
            # Find index of mach which have the same value
            idx_mach = [j for j in range(len(mach_list)) if mach_list[j] == mach]
            # Prepare variables for plots
            plot_cml = []
            plot_aoa = []
            plot_legend = []
            plot_title = 'Cml vs aoa, @ Mach = ' + str(mach) + ' and aos = '+ str(aos)
            xlabel = 'aoa'
            ylabel = 'Cml'

            longitudinaly_stable = True

            # Find index of slip angle which have the same value
            for alt in alt_unic:
                idx_alt = [k for k in range(len(alt_list)) if alt_list[k] == alt]
                # List of index of elements which have the same index  in vectors alt_list, mach_list, aos_list
                find_idx = []
                # Fill   the liste find_index
                for idx3 in idx_aos:
                    for idx2 in idx_mach:
                        for idx1 in idx_alt:
                            if idx1 == idx2 == idx3:
                                find_idx.append(idx1)

                # If find_idx is empty an APM function would have corrected before
                # If there there is only one value  in  find_idx for a given Alt, Mach, aos_list, no analyse can be performed
                # An error message has been already printed through the first part of the code

                # Check if it is an unstability case detected previously
                for combination in longi_unstable_cases :
                    if  combination[0] == alt and combination[1] == mach and combination[2] == aos :
                        longitudinaly_stable = False

                # If there is at list 2 values in find_idx :
                if len(find_idx) > 1:
                    # Find all cml_list values for index corresonding to an altitude, a mach, an aos_list=0, and different aoa_list
                    cml = []
                    aoa = []
                    for index in find_idx:
                        cml.append(cml_list[index])
                        aoa.append(aoa_list[index])

                    curve_legend = 'Altitude = ' + str(alt)

                    # Store  Cml values in cml_list
                    plot_cml.append(cml)
                    # Store list_attack in list_list_attack
                    plot_aoa.append(aoa)
                    # Store the legend in plot_legend
                    plot_legend.append(curve_legend)

            if longitudinaly_stable == False :
                # PLot Cml VS aoa for constant  Mach, aos and different Alt
                plot_torque_vs_angle(plot_cml, plot_aoa, plot_legend, plot_title, xlabel, ylabel)

    # plot Cms VS aos for constant mach, aoa_list and different altitudes:
    for aoa in aoa_unic:
        # Find index of altitude which have the same value
        idx_aoa = [i for i in range(len(aoa_list)) if aoa_list[i] == aoa]
        for mach in mach_unic:
            # Find index of mach which have the same value
            idx_mach = [j for j in range(len(mach_list)) if mach_list[j] == mach]
            # Prepare variables for plots
            plot_cms = []
            plot_aos = []
            plot_legend = []
            plot_title = 'Cms vs aos, @ Mach = ' + str(mach) + ' and aoa= ' + str(aoa)
            xlabel= 'aos'
            ylabel= 'Cms'

            dirrectionaly_stable = True

            # Find index of slip angle which have the same value
            for alt in alt_unic:
                idx_alt = [k for k in range(len(alt_list)) if alt_list[k] == alt]
                # List of index of elements which have the same index  in vectors alt_list, mach_list, aos_list
                find_idx = []
                # Fill   the liste find_index
                for idx3 in idx_aoa:
                    for idx2 in idx_mach:
                        for idx1 in idx_alt:
                            if idx1 == idx2 == idx3:
                                find_idx.append(idx1)
                # If find_idx is empty an APM function would have corrected before
                # If there there is only one value  in  find_idx for a given Alt, Mach, aos_list, no analyse can be performed
                # An error message has been already printed through the first part of the code

                # Check if it is an unstability case detected previously
                for combination in direc_unstable_cases :
                    if combination[0] == alt and combination[1] == mach and combination[2] == aoa :
                        dirrectionaly_stable = False

                # If there is at list 2 values in find_idx :
                if len(find_idx) > 1:
                    # Find all cml_list values for index corresonding to an altitude, a mach, an aos_list=0, and different aoa_list
                    cms = []
                    aos = []
                    for index in find_idx:
                        cms.append(cms_list[index])
                        aos.append(aos_list[index])

                    curve_legend = 'Altitude = ' + str(alt)

                    # Store  Cml values in cml_list
                    plot_cms.append(cms)
                    # Store list_attack in list_list_attack
                    plot_aos.append(aos)
                    # Store the legend in plot_legend
                    plot_legend.append(curve_legend)

            if dirrectionaly_stable == False :
                # PLot Cms VS aos for constant  Mach, aoa and different alt
                plot_torque_vs_angle(plot_cms, plot_aos, plot_legend, plot_title, xlabel, ylabel)


#==============================================================================
#    MAIN
#==============================================================================


if __name__ == '__main__':

    log.info('----- Start of ' + os.path.basename(__file__) + ' -----')

    # Give the path this python file
    MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
    # Give the path of the  xml file to analyse
    cpacs_path = os.path.join(MODULE_DIR,'ToolInput','cpacs_test_file.xml')
    # Call the function which check if the imput file is well define
    check_cpacs_input_requirements(cpacs_path)
    # Run the static analysis
    static_stability_analysis(cpacs_path, aeromap_uid)

    log.info('----- End of ' + os.path.basename(__file__) + ' -----')
