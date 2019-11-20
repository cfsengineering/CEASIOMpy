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

def get_unic(vector):
    """ Return a vector with the same element having only one occurence """
    vector_unic = []
    for element in vector:
        if element not in vector_unic:
            vector_unic.append(element)
    return vector_unic

def extract_subelements(vector):
    """ from a oririginal vector [[1,2,3], [1]] return [1,2,3,1] """
    extracted = []
    for element in vector:
        for value in element :
            extracted.append(value)
    return extracted


def unexpected_sign_change(alt, cm, stability = True) :
    """ Find if  Coefficeint Moments, cm, don't cross the 0 line or more than once """
    # If cml curve does not cross the 0
    if len(np.argwhere(np.diff(np.sign(cm)))) == 0  :
        # If all Cml values are 0:
        stability = False
        if cm.count(0) == len(cm):
            log.warning('Alt = '  + str(alt) + 'Cm list is composed of 0 only.' )
        else:
            log.error('Alt = '  + str(alt) + 'Cm does not cross the 0 line, aircraft not stable.' )
    # If cml Curve crosses the 0 line more than once no stability analysis can be performed
    elif len(np.argwhere(np.diff(np.sign(cm)))) > 2 or cm.count(0) > 1:
        log.error('Alt = '  + str(alt) + 'The Cm curves crosses more than once the 0 line, no stability analysis performed')
        stability  = False
    # If cml Curve crosses the 0 line twice
    elif 0 not in np.sign(cm) and len(np.argwhere(np.diff(np.sign(cm)))) == 2:
        log.error('Alt = '  + str(alt) + 'The Cm curves crosses the 0 line twice, no stability analysis performed')
        stability  = False

    return stability

def change_sign_once(angle , cm, crossed = False) :
    """ Find if  Coefficeint Moments, cm, crosse the 0 line only once and return the corresponding angle and the cm derivative at cm=0 """
    cruise_angle = ''
    moment_derivative = ''
    # If Cm = 0 is in Cm list
    if 0 in np.sign(cm) and cm.count(0) == 1:
        crossed = True
        idx_cm_0 = [i for i in range(len(cm)) if cm[i] == 0][0]
        # If Cml = 0 is the first element in cml list, take the derivative at right
        if idx_cm_0 == 0:
            # Angles and coeffs before and after crossing the 0 line
            angle_before = angle[idx_cm_0]
            angle_after = angle[idx_cm_0+1]
            cm_before = cm[idx_cm_0]
            cm_after = cm[idx_cm_0+1]

            cruise_angle = angle_before
            moment_derivative = (cm_after-cm_before)/(angle_after-angle_before)

        # If cml = 0 is the last element of cml list, take the derivative at left
        if idx_cm_0 == len(cm) - 1:
            # Angles and coeffs before and after crossing the 0 line
            angle_before = angle[idx_cm_0-1]
            angle_after = angle[idx_cm_0]
            cm_before = cm[idx_cm_0-1]
            cm_after = cm[idx_cm_0]

            cruise_angle = angle_after
            moment_derivative = (cm_after-cm_before)/(angle_after-angle_before)

        # If cml = 0 is nor the first nor the last element in cml list, take the centered derivative
        if 0 < idx_cm_0 < len(cm)-1:
            # Angles and coeffs before and after crossing the 0 line
            angle_before = angle[idx_cm_0-1]
            angle_after = angle[idx_cm_0+1]
            cm_before = cm[idx_cm_0-1]
            cm_after = cm[idx_cm_0+1]

            cruise_angle = angle[idx_cm_0]
            moment_derivative = (cm_after - cm_before)/(angle_after - angle_before)

    # If Cms crosses the 0 line once and Cms=0 is not in cml list
    if  len(np.argwhere(np.diff(np.sign(cm)))) == 1 and 0 not in np.sign(cm):
        # Make the linear equation btween the 2 point before and after crossing the 0 ine y=ax+b
        crossed = True
        idx_cm_0 = np.argwhere(np.diff(np.sign(cm)))[0][0]

        # Angles and coeffs before and after crossing the 0 line
        angle_before = angle[idx_cm_0]
        angle_after = angle[idx_cm_0+1]
        cm_before = cm[idx_cm_0]
        cm_after = cm[idx_cm_0+1]

        fit = np.polyfit([angle_before, angle_after], [cm_before, cm_after], 1)  # returns [a,b] of y=ax+b
        cruise_angle = -fit[1]/fit[0]    # Cms = 0 for y = 0  hence cruise agngle = -b/a
        moment_derivative = fit[0]

    return (cruise_angle, moment_derivative, crossed)


def plot_multicurve(y_axis, x_axis, plot_legend, plot_title, xlabel, ylabel):
    """Function to plot graph with different curves for a varying parameter

    Function 'plot_multicurve' can plot few curves

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

def static_stability_analysis(cpacs_path, cpacs_out_path, plot=True):
    """Function to analyse a full Aeromap

    Longitudinal static staticStabilityAnalysis
    Directionnal static analysis

    Args:
        Cpacs file paths
        Aeromap uid
        plot= True or False to ask the program to plot or not

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

    Make the following tests:            (To put in the documentation)
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

    #Open tixi handles
    tixi = open_tixi(cpacs_path)
    # get aeromap uid#from ceasiompy.StabilityStatic.staticstability import
    aeromap_uid = get_value(tixi, '/cpacs/toolspecific/CEASIOMpy/stability/static/aeroMapUid')
    print('UID: ' + aeromap_uid)
    # Coeffs lists
    Coeffs = get_aeromap(tixi, aeromap_uid)

    alt_list = Coeffs.alt
    mach_list = Coeffs.mach

    aoa_list = Coeffs.aoa
    cml_list = Coeffs.cml

    aos_list = Coeffs.aos
    cms_list = Coeffs.cms


    alt_unic = get_unic(alt_list)
    mach_unic = get_unic(mach_list)
    print(mach_unic)
    aos_unic = get_unic(aos_list)
    aoa_unic = get_unic(aoa_list)

    # Init Plot variables : trim Aoa for gien alt and different mach
    #                                  trim Aoa for gien Mach and different alt
    # Gather trim aoa_list for different Alt & mach , for aos = 0
    trim_alt_longi_list = []
    trim_mach_longi_list = []
    trim_aoa_longi_list = []
    trim_aos_longi_list = []
    trim_legend_longi_list = []

    # Gather trim aos_list for different Alt & mach , for aoa = 0
    trim_alt_direc_list = []
    trim_mach_direc_list = []
    trim_aoa_direc_list = []
    trim_aos_direc_list = []
    trim_legend_direc_list = []

    # to store in cpacs result
    longi_unstable_cases = []
    direc_unstable_cases = []

    cpacs_stability_longi = True
    cpacs_stability_direc = True

    # Aero analyses for all given Altitude, Mach and aos_list, over different
    for alt in alt_unic:
        # print("*****Alt : " + str(alt))
        # Find index of altitude which have the same value
        idx_alt = [i for i in range(len(alt_list)) if alt_list[i] == alt]

        # Prepar trim condition lists
        trim_alt_longi = []
        trim_mach_longi = []
        trim_aoa_longi = []
        trim_aos_longi = []
        trim_legend_longi = []

        # Prepar trim condition lists
        trim_alt_direc = []
        trim_mach_direc = []
        trim_aoa_direc = []
        trim_aos_direc = []
        trim_legend_direc = []

        for mach in mach_unic:
            #log.info(str(mach))
            #print("***mach_list : " + str(mach))
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
                #log.info('AOS: ' +  str(aos))
                # by default, don't  cross 0 line
                crossed = False
                #print("**aos_list: " + str(count_aos))
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
                        if  aoa[jj] == aoa[jj+1] and  aoa_good :
                            aoa_good = False
                            log.warning('Alt = {} , at least 2 aoa values are equal in aoa list: {} at Mach= {}, aos = {}' .format(alt, aoa, mach, aos))

                    longitudinaly_stable = unexpected_sign_change(alt, cml, longitudinaly_stable )

                    if aoa_good and longitudinaly_stable :
                        cruise_aoa, pitch_moment_derivative, crossed = change_sign_once(aoa , cml, crossed = False)

                    if aos == 0 and crossed and aoa_good and pitch_moment_derivative < 0 and cruise_aoa != '' :
                        trim_alt_longi.append(alt)
                        trim_mach_longi.append(mach)
                        trim_aoa_longi.append(cruise_aoa)
                        trim_aos_longi.append(aos)

                    # Conclusion about stability, if the Cml curve has crossed the 0 line and there is not 2 repeated aoa for the same alt, mach and aos.
                    if crossed and aoa_good :
                        if pitch_moment_derivative < 0 :
                            log.info('Vehicle longitudinaly staticaly stable.')
                        if pitch_moment_derivative == 0 :
                            longitudinaly_stable = False
                            log.error('Alt = '  + str(alt) + 'Vehicle longitudinaly staticaly neutral stable.')
                        if pitch_moment_derivative > 0 :
                            longitudinaly_stable = False
                            log.error('Alt = '  + str(alt) + 'Vehicle *NOT* longitudinaly staticaly stable.')

                    # If not stable store the set [alt, mach, aos] at which the aircraft is unstable.
                    if not longitudinaly_stable :
                        longi_unstable_cases.append([alt,mach,aos])

            #print( LongitudinalyStable)
            if not longitudinaly_stable :
                # To write in the output CPACS that the aircraft is not longitudinaly stable
                cpacs_stability_longi = False
                # PLot Cml VS aoa for constant Alt, Mach and different aos
                if plot:
                    plot_multicurve( plot_cml, plot_aoa, plot_legend, plot_title, xlabel, ylabel)


    # Dirrectional Stability analysis-
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
                #log.info('AOA : ' + str(aoa))
                # by default, don't  cross 0 line
                crossed = False
                #print('**aoa_list: ' + str(count_aoa))
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

                    aos_good  =  True
                    for jj in range(len(aos)-1) :
                        if  aos[jj] == aos[jj+1] and  aos_good :
                                aoa_good = False
                                log.warning('At alt ={}, at least 2 aos values are equal in aoa list: {} , Mach= {}, aos = {}' .format(alt, aoa, mach, aos))

                    dirrectionaly_stable = unexpected_sign_change(alt, cms, dirrectionaly_stable )

                    if aos_good and dirrectionaly_stable :
                        [cruise_aos, side_moment_derivative, crossed] = change_sign_once(aos, cms, crossed = False)

                    if aoa == 0 and crossed and aos_good and side_moment_derivative > 0 and cruise_aos != '' :
                        trim_alt_direc.append(alt)
                        trim_mach_direc.append(mach)
                        trim_aoa_direc.append(cruise_aos)
                        trim_aos_direc.append(aoa)


                    if crossed and aos_good :
                        if side_moment_derivative > 0 :
                            log.info('Vehicle directionnaly staticaly stable.')
                        if side_moment_derivative == 0 :
                            dirrectionaly_stable = False
                            log.error('At alt = ' + str(alt) + 'Vehicle directionnaly staticaly neutral stable.')
                        if side_moment_derivative < 0 :
                            dirrectionaly_stable = False
                            log.error('Alt = '  + str(alt) + 'Vehicle *NOT* directionnaly staticaly stable.')

                    # If not stable store the set [alt, mach, aos] at which the aircraft is unstable.
                    if not dirrectionaly_stable :
                        direc_unstable_cases.append([alt,mach,aoa])


            if not dirrectionaly_stable :
                # To write in the output CPACS that the aircraft is not longitudinaly stable
                cpacs_stability_direc = False
                if plot:
                    # PLot Cms VS aos for constant Alt, Mach and different aoa
                    plot_multicurve(plot_cms, plot_aos, plot_legend, plot_title, xlabel, ylabel)


        # Add trim conditions for the given altitude (longi analysis)
        if len(trim_aoa_longi) > 0 :
            trim_aoa_longi_list.append(trim_aoa_longi)
            trim_mach_longi_list.append(trim_mach_longi)
            trim_legend_longi_list.append('Alt = ' + str(alt))

            trim_alt_longi_list.append(trim_alt_longi)
            trim_aos_longi_list.append(trim_aos_longi)
        # Add trim conditions for the given altitude (direcanalysis)
        if len(trim_aos_direc) > 0 :
            trim_aos_direc_list.append(trim_aos_direc)
            trim_mach_direc_list.append(trim_mach_direc)
            trim_legend_direc_list.append('Alt = ' + str(alt))

            trim_alt_direc_list.append(trim_alt_direc)
            trim_aoa_direc_list.append(trim_aoa_direc)

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
            if not longitudinaly_stable and plot:
                #PLot Cml VS aoa for constant Alt, aoa and different mach
                plot_multicurve(plot_cml, plot_aoa, plot_legend, plot_title, xlabel, ylabel)

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

            if not dirrectionaly_stable and plot:
                # Plot Cms VS aos for constant Alt, aoa and different mach
                plot_multicurve(plot_cms, plot_aos, plot_legend, plot_title, xlabel, ylabel)

    # Plot trim_aoa VS mach for different alt
    # If there is at least 1 element in list of trim conditions then, plot them

    if len(trim_aoa_longi_list) >= 1:
        log.info('graph : cruising aoa vs mach genrated')
        if plot:
            plot_multicurve(trim_aoa_longi_list, trim_mach_longi_list, trim_legend_longi_list, 'trim_aoa VS mach', 'mach', 'aoa')

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
                # If there is only one value  in  find_idx for a given Alt, Mach, aos_list, no analyse can be performed
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

            if not longitudinaly_stable and plot:
                # PLot Cml VS aoa for constant  Mach, aos and different Alt
                plot_multicurve(plot_cml, plot_aoa, plot_legend, plot_title, xlabel, ylabel)

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

            if not dirrectionaly_stable and plot:
            # PLot Cms VS aos for constant  Mach, aoa and different alt
                plot_multicurve(plot_cms, plot_aos, plot_legend, plot_title, xlabel, ylabel)

    # Save in the CPACS file stability results:
    trim_alt_longi_list=extract_subelements(trim_alt_longi_list)
    trim_mach_longi_list=extract_subelements(trim_mach_longi_list)
    trim_aoa_longi_list=extract_subelements(trim_aoa_longi_list)
    trim_aos_longi_list=extract_subelements(trim_aos_longi_list)

    trim_alt_direc_list=extract_subelements(trim_alt_direc_list)
    trim_mach_direc_list=extract_subelements(trim_mach_direc_list)
    trim_aoa_direc_list=extract_subelements(trim_aoa_direc_list)
    trim_aos_direc_list=extract_subelements(trim_aos_direc_list)

    # If all analysis were good: stability = True
    # If one of the analysis was not good: stability =False
    toolspecific_static_xpath = '/cpacs/toolspecific/CEASIOMpy/stability/static'

    UID_XPATH =   toolspecific_static_xpath + '/aeroMapUid'
    LONGI_XPATH = toolspecific_static_xpath + '/results/longitudinalStaticStable'
    DIREC_XPATH = toolspecific_static_xpath + '/results/directionnalStaticStable'

    # If branch does not exist
    if not tixi.checkElement(UID_XPATH):
        create_branch(tixi,UID_XPATH, add_child=False)
        add_string_vector(tixi, UID_XPATH, [aeromap_uid])

    if not tixi.checkElement(LONGI_XPATH) :
        create_branch(tixi, LONGI_XPATH, add_child=False)
    if not tixi.checkElement(DIREC_XPATH) :
        create_branch(tixi, DIREC_XPATH, add_child=False)

    # Store in the CPCS the stability results
    add_string_vector(tixi, LONGI_XPATH, [cpacs_stability_longi])
    add_string_vector(tixi, DIREC_XPATH, [cpacs_stability_direc])

    longi_cruising = toolspecific_static_xpath +'/trimconditions/longitudinal'
    direc_cruising = toolspecific_static_xpath +'/trimconditions/directional'

    create_branch(tixi,longi_cruising, add_child=False)
    create_branch(tixi,direc_cruising, add_child=False)

    add_float_vector(tixi,longi_cruising+'/altitude',trim_alt_longi_list)
    add_float_vector(tixi,longi_cruising+'/machNumber',trim_mach_longi_list)
    add_float_vector(tixi,longi_cruising+'/angleOfAttack',trim_aoa_longi_list)
    add_float_vector(tixi,longi_cruising+'/angleOfSideslip',trim_aos_longi_list)

    add_float_vector(tixi,direc_cruising+'/altitude',trim_alt_longi_list)
    add_float_vector(tixi,direc_cruising+'/machNumber',trim_mach_longi_list)
    add_float_vector(tixi,direc_cruising+'/angleOfAttack',trim_aoa_longi_list)
    add_float_vector(tixi,direc_cruising+'/angleOfSideslip',trim_aos_longi_list)

    close_tixi(tixi, cpacs_out_path)

#==============================================================================
#    MAIN
#==============================================================================


if __name__ == '__main__':

    log.info('----- Start of ' + os.path.basename(__file__) + ' -----')

    # Give the path this python file
    MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
    # Give the path of the  xml file to analyse
    cpacs_path = os.path.join(MODULE_DIR,'ToolInput','ToolInput.xml')
    cpacs_out_path = os.path.join(MODULE_DIR,'ToolOutput','ToolOutput.xml')
    # Call the function which check if imputs are well define
    #check_cpacs_input_requirements(cpacs_path)

    static_stability_analysis(cpacs_path, cpacs_out_path)

    log.info('----- End of ' + os.path.basename(__file__) + ' -----')
