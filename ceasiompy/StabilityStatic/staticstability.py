"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Static stability module

Python version: >=3.6

| Author: Verdier Loïc
| Creation: 2019-10-24
| Last modifiction: 2019-11-21 (AJ)

TODO:
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
import matplotlib as mpl
import matplotlib.patheffects
import matplotlib.pyplot as plt

import pandas as pd

from ceasiompy.utils.cpacsfunctions import open_tixi, open_tigl, close_tixi,   \
                                           add_uid, create_branch, copy_branch,\
                                           get_value, get_value_or_default,    \
                                           aircraft_name
from ceasiompy.utils.standardatmosphere import get_atmosphere, plot_atmosphere
from ceasiompy.utils.moduleinterfaces import check_cpacs_input_requirements, \
                                             get_toolinput_file_path,        \
                                             get_tooloutput_file_path
from ceasiompy.utils.apmfunctions import aeromap_to_csv, get_aeromap_uid_list, \
                                         aeromap_from_csv, get_aeromap


from ceasiompy.utils.cpacsfunctions import open_tixi, open_tigl, close_tixi,   \
                                           create_branch, copy_branch, add_uid,\
                                           get_value, get_value_or_default,    \
                                           add_float_vector, get_float_vector, \
                                           add_string_vector, get_string_vector\

from ceasiompy.utils.ceasiomlogger import get_logger

log = get_logger(__file__.split('.')[0])

MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
MODULE_NAME = os.path.basename(os.getcwd())

#==============================================================================
#   FUNCTIONS
#==============================================================================

def get_unic(vector):
    """Return a vector with the same element having only one occurence.

    Args:
        vector (list): List of element which may contains double elements

    Returns:
        vector_unic (list): List of unique value
    """

    vector_unic = []
    for elem in vector:
        if elem not in vector_unic:
            vector_unic.append(elem)

    return vector_unic


def extract_subelements(vector):
    """ Transform multiple element list into a 1D vector

    Function 'extract_subelements' return [1,2,3,1] from an oririginal vector
    like [[1,2,3], [1]]

    Args:
        vector (list of list): Original list of list

    Returns:
        extracted (list): Return 1D list
    """

    extracted = []
    for elem in vector:
        for value in elem :
            extracted.append(value)

    return extracted

def change_sign(alt, angles, cm):
    """Find if a moments coefficeint cm. cross the 0 line, once or more
       Find if a moment coefficeint cm. crosse the 0 line only once and return
        the corresponding angle and the cm derivative at cm=0

    Args:
        alt (float): Altitude [m]
        cm (list): Moment coefficient
        angle (list): Angle of attack (or sideslip)

    Returns:
        cruise_angle (float): Angle to get cm. = 0
        moment_derivative (float): Moment derivative at cruise_angle
        cross (boolean): List of unique value
    """

    crossed = True
    cruise_angle = ''
    moment_derivative = ''

    if len(np.argwhere(np.diff(np.sign(cm)))) == 0  :
        # If all Cm. values are 0:
        crossed = False
        if cm.count(0) == len(cm):
            log.warning('Alt = '  + str(alt) + 'Cm list is composed of 0 only.' )
        else:
            log.error('Alt = '  + str(alt) + 'Cm does not cross the 0 line, aircraft not stable.' )
    # If cm. Curve crosses the 0 line more than once no stability analysis can be performed
    elif len(np.argwhere(np.diff(np.sign(cm)))) > 2 or cm.count(0) > 1:
        log.error('Alt = '  + str(alt) + 'The Cm curves crosses more than once the 0 line, no stability analysis performed')
        crossed  = False
    # If cm. Curve crosses the 0 line twice
    elif 0 not in np.sign(cm) and len(np.argwhere(np.diff(np.sign(cm)))) == 2:
        log.error('Alt = '  + str(alt) + 'The Cm curves crosses the 0 line twice, no stability analysis performed')
        crossed = False

    # If Cm = 0 is in Cm list, and cm crosses oly once the 0 line
    elif 0 in np.sign(cm) and cm.count(0) == 1 and crossed:
        idx_cm_0 = [i for i in range(len(cm)) if cm[i] == 0][0]
        # If cm. = 0 is the first element in cm. list, take the derivative at right
        if idx_cm_0 == 0:
            # Angles and coeffs before and after crossing the 0 line
            angle_before = angles[idx_cm_0]
            angle_after = angles[idx_cm_0+1]
            cm_before = cm[idx_cm_0]
            cm_after = cm[idx_cm_0+1]

            cruise_angle = angle_before
            moment_derivative = (cm_after-cm_before)/(angle_after-angle_before)

        # If cm. = 0 is the last element of cm. list, take the derivative at left
        elif idx_cm_0 == len(cm) - 1:
            # Angles and coeffs before and after crossing the 0 line
            angle_before = angles[idx_cm_0-1]
            angle_after = angles[idx_cm_0]
            cm_before = cm[idx_cm_0-1]
            cm_after = cm[idx_cm_0]

            cruise_angle = angle_after
            moment_derivative = (cm_after-cm_before)/(angle_after-angle_before)

        # If cm. = 0 is nor the first nor the last element in cm. list, take the centered derivative
        elif 0 < idx_cm_0 < len(cm)-1:
            # Angles and coeffs before and after crossing the 0 line
            angle_before = angles[idx_cm_0-1]
            angle_after = angles[idx_cm_0+1]
            cm_before = cm[idx_cm_0-1]
            cm_after = cm[idx_cm_0+1]

            cruise_angle = angles[idx_cm_0]
            moment_derivative = (cm_after - cm_before)/(angle_after - angle_before)

    # If cm. crosses the 0 line once and Cm.= 0 is not in cm. list
    elif  len(np.argwhere(np.diff(np.sign(cm)))) == 1 and 0 not in np.sign(cm) and crossed:
        # Make the linear equation btween the 2 point before and after crossing the 0 ine y=ax+b
        idx_cm_0 = np.argwhere(np.diff(np.sign(cm)))[0][0]

        # Angles and coeffs before and after crossing the 0 line
        angle_before = angles[idx_cm_0]
        angle_after = angles[idx_cm_0+1]
        cm_before = cm[idx_cm_0]
        cm_after = cm[idx_cm_0+1]

        fit = np.polyfit([angle_before, angle_after], [cm_before, cm_after], 1)  # returns [a,b] of y=ax+b
        cruise_angle = -fit[1]/fit[0]    # Cm. = 0 for y = 0  hence cruise agngle = -b/a
        moment_derivative = fit[0]

    return (cruise_angle, moment_derivative, crossed)


def plot_multicurve(y_axis, x_axis, plot_legend, plot_title, xlabel, ylabel, show_plots, save_plots):
    """Function to plot graph with different curves for a varying parameter

    Function 'plot_multicurve' can plot few curves

    Args:
        x_axis (list): List of vector of each curve's X coordinates
        y axis (list): List of vector of each curve's Y coordinates
        plot_legend (list): List of the leggends of all the different curves
        plot_title (str): Tile of the plot
        xlabel (str): Label of the x axis
        ylabel (str): Label of the y axis
        show_plot (boolean): To show plots on screen or not
        save_plot (boolean): To save plots in the /ToolOutput dir or not

    Returns:
        A plot with different curves if asked.
    """

    # Avoid to do the rest of the function if nothing to plot or save
    if not show_plots and not save_plots:
        return None

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

    if save_plots:
        fig_titile = plot_title.replace(' ','_')
        fig_path = os.path.join(MODULE_DIR,'ToolOutput',fig_titile) + '.svg'
        plt.savefig(fig_path)

    if show_plots:
        plt.show()


def get_index(value_list,value,idx_list1,idx_list2):
    """Function to get index list

    Function 'get_index' returns the index of list at value  .???.. for list1 and list2

    Args:
        value_list (list): ...??
        value (float): ...??
        idx_list1 (list): index list at which the current corresonding value as been found
        idx_list2 (list): index list at which the current corresonding value as been found

    Returns:
        find_idx (list): list of index
    """

    # List of index of elements which have the same index in vectors list, list1, list2
    find_idx = []

    idx_value_list = [k for k in range(len(value_list)) if value_list[k] == value]

    # Fill   the liste find_index
    for idx1 in idx_list1:
        for idx2 in idx_list2:
            for idx3 in idx_value_list:
                if idx1 == idx2 == idx3:
                    find_idx.append(idx1)

    return find_idx


def static_stability_analysis(cpacs_path, cpacs_out_path):
    """Function to analyse a full Aeromap

    Function 'static_stability_analysis' analyses longitudinal static static
    stability and directionnal static.

    Args:
        cpacs_path (str): Path to CPACS file
        cpacs_out_path (str):Path to CPACS output file
        plot (boolean): Choise to plot graph or not

    Returns:
        *   Adrvertisements certifying if the aircraft is stable or Not
        *   In case of longitudinal static UNstability or unvalid test on data:
                -	Plot cms VS aoa for constant Alt, Mach and different aos
                -	Plot cms VS aoa for const alt and aos and different mach
                -	plot cms VS aoa for constant mach, AOS and different altitudes
        *  In case of directionnal static UNstability or unvalid test on data:
                -	Pcot cml VS aos for constant Alt, Mach and different aoa
                -	Plot cml VS aos for const alt and aoa and different mach
                -	plot cml VS aos for constant mach, AOA and different altitudes
        *  Plot one graph of  cruising angles of attack for different mach and altitudes

    Make the following tests:            (To put in the documentation)
        *   Check the CPACS path
        *   For longitudinal static stability analysis:
                -   If there is more than one angle of attack for a given altitude, mach, aos
                -   If cml values are only zeros for a given altitude, mach, aos
                -   If there one aoa value which is repeated for a given altitude, mach, aos
        *   For directionnal static stability analysis:
                -   If there is more than one angle of sideslip for a given altitude, mach, aoa
                -   If cms values are only zeros for a given altitude, mach, aoa
                -   If there one aos value which is repeated for a given altitude, mach, aoa
    """

    tixi = open_tixi(cpacs_path)

    # Get aeromap uid
    aeromap_uid = get_value(tixi, '/cpacs/toolspecific/CEASIOMpy/stability/static/aeroMapUid')
    log.info('The following aeroMap will be analysed: ' + aeromap_uid)

    show_plots = get_value_or_default(tixi,'/cpacs/toolspecific/CEASIOMpy/stability/static/showPlot',False)
    save_plots = get_value_or_default(tixi,'/cpacs/toolspecific/CEASIOMpy/stability/static/savePlot',False)

    Coeffs = get_aeromap(tixi, aeromap_uid)

    alt_list = Coeffs.alt
    mach_list = Coeffs.mach
    aoa_list = Coeffs.aoa
    aos_list = Coeffs.aos
    cml_list = Coeffs.cml
    cms_list = Coeffs.cms

    alt_unic = get_unic(alt_list)
    mach_unic = get_unic(mach_list)
    aos_unic = get_unic(aos_list)
    aoa_unic = get_unic(aoa_list)

    # Init Plot variables : trim Aoa for given alt and different mach
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

    # To store in cpacs result
    longi_unstable_cases = []
    direc_unstable_cases = []

    cpacs_stability_longi = True
    cpacs_stability_direc = True

    # Aero analyses for all given altitude, mach and aos_list, over different
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
            #print("***mach_list : " + str(mach))
            # Find index of mach which have the same value
            idx_mach = [j for j in range(len(mach_list)) if mach_list[j] == mach]

            # Longitudinal stability
            # Analyse in function of the angle of attack for given, alt, mach and aos_list
            # Prepare variables for plots
            plot_cms = []
            plot_aoa = []
            plot_legend = []
            plot_title = 'cms vs aoa @ atl = ' + str(alt) + ' m and Mach = ' + str(mach)
            xlabel= 'Angle of attack [deg]'
            ylabel= 'Pitching moment coefficient [-]'
            # Init for determining if it's an unstable case
            longitudinaly_stable = True
            # Find index of slip angle which have the same value

            for aos in aos_unic:
                #log.info('AOS: ' +  str(aos))
                # by default, don't  cross 0 line
                crossed = False

                find_idx = get_index(aos_list,aos,idx_alt,idx_mach)

                # If find_idx is empty an APM function would have corrected before
                # If there there is only one value  in  find_idx for a given Alt, Mach, aos_list, no analyse can be performed
                if len(find_idx) == 1:
                    log.info('Only one data, one aoa(' +str(aoa_list[find_idx[0]]) \
                    + '), for Altitude =  '+ str(alt) + '[m] , Mach = ' \
                    + str(mach) + '  and aos = ' + str(aos)             \
                    + '  no stability analyse will be performed' )

                elif len(find_idx) > 1: # if there is at least 2 values in find_idx :

                    # Find all cms_list values for index corresonding to an altitude, a mach, an aos_list=0, and different aoa_list
                    cms = []
                    aoa = []
                    for index in find_idx:
                        cms.append(cms_list[index])
                        aoa.append(aoa_list[index])

                    # Save values which will be plot
                    plot_cms.append(cms)
                    plot_aoa.append(aoa)
                    curve_legend = 'aos = '+ str(aos) + '°'
                    plot_legend.append(curve_legend)

                    # If all aoa values are the same while the calculating the derivative, a division by zero will be prevented.
                    aoa_good = True
                    for jj in range(len(aoa)-1):
                        if  aoa[jj] == aoa[jj+1]:
                            aoa_good = False
                            log.error('Alt = {} , at least 2 aoa values are equal in aoa list: {} at Mach= {}, aos = {}' .format(alt, aoa, mach, aos))
                            break

                    if aoa_good :
                        cruise_aoa, pitch_moment_derivative, crossed = change_sign(alt, aoa, cms)

                    # Conclusion about stability, if the cms curve has crossed the 0 line and there is not 2 repeated aoa for the same alt, mach and aos.
                    if crossed and aoa_good :
                        if pitch_moment_derivative < 0 :
                            log.info('Vehicle longitudinaly staticaly stable.')
                            if aos == 0 :
                                trim_alt_longi.append(alt)
                                trim_mach_longi.append(mach)
                                trim_aoa_longi.append(cruise_aoa)
                                trim_aos_longi.append(aos)
                        elif pitch_moment_derivative == 0 :
                            longitudinaly_stable = False
                            log.error('Alt = '  + str(alt) + 'Vehicle longitudinaly staticaly neutral stable.')
                        else: #pitch_moment_derivative > 0
                            longitudinaly_stable = False
                            log.error('Alt = '  + str(alt) + 'Vehicle *NOT* longitudinaly staticaly stable.')

                    # If not stable store the set [alt, mach, aos] at which the aircraft is unstable.
                    if not longitudinaly_stable :
                        longi_unstable_cases.append([alt,mach,aos])
                        # To write in the output CPACS that the aircraft is not longitudinaly stable
                        cpacs_stability_longi = False

                # To write in the output CPACS that the aircraft is not longitudinaly stable

            # PLot cms VS aoa for constant Alt, Mach and different aos
            if longi_unstable_cases:
                plot_multicurve(plot_cms, plot_aoa, plot_legend, plot_title, xlabel, ylabel, show_plots, save_plots)


            # Dirrectional Stability analysis-
            count_aoa = 0

            plot_cml = []
            plot_aos = []
            plot_legend = []
            plot_title = 'cml vs aos @ atl = ' + str(alt) + ' m and Mach = ' + str(mach)
            xlabel= 'Angle of sideslip [deg]'
            ylabel= 'cml'
            # Init for determinig if it is an unstability case
            dirrectionaly_stable = True
            # Find INDEX
            for aoa in aoa_unic:
                #log.info('AOA : ' + str(aoa))
                # by default, don't  cross 0 line
                crossed = False
                #print('**aoa_list: ' + str(count_aoa))
                count_aoa += 1

                find_idx = get_index(aoa_list,aoa,idx_alt,idx_mach)

                # If find_idx is empty an APM function would have corrected before
                # If there there is only one value  in  find_idx for a given Alt, Mach, aos_list, no analyse can be performed
                if len(find_idx) == 1:
                    log.info('Only one data, one aos (' + str(aos_list[find_idx[0]])  \
                              +'), for Altitude = '+str(alt)+'[m] , Mach = '   \
                              + str(mach) + ' and aoa = ' + str(aoa)           \
                              + ' no stability analyse performed')

                elif len(find_idx)> 1: #if there is at least 2 values in find_idx
                    cml = []
                    aos = []
                    for index in find_idx:
                        cml.append(cml_list[index])
                        aos.append(aos_list[index])

                    # retrieve the index in of element in cml just before crossing 0,
                    # np.argwher returns an array as [[idx]], that'a why there is [0][0] at the end
                    #  If cml Curve crosses th 0 line more than once na stability analysis can be performed
                    curve_legend = 'aoa = ' + str(aoa) + '°'

                    # Save values which will be plot
                    plot_cml.append(cml)
                    plot_aos.append(aos)
                    plot_legend.append(curve_legend)

                    aos_good = True
                    for jj in range(len(aos)-1):
                        if  aos[jj] == aos[jj+1]:
                            aos_good = False
                            log.error('Alt = {} , at least 2 aos values are equal in aos list: {} , Mach= {}, aos = {}' .format(alt, aoa, mach, aos))
                            break

                    if aos_good :
                        [cruise_aos, side_moment_derivative, crossed] = change_sign(alt, aos, cml)

                    if crossed and aos_good :
                        if side_moment_derivative > 0 :
                            log.info('Vehicle directionnaly staticaly stable.')
                            if aoa == 0 :
                                trim_alt_direc.append(alt)
                                trim_mach_direc.append(mach)
                                trim_aoa_direc.append(cruise_aos)
                                trim_aos_direc.append(aoa)
                        if side_moment_derivative == 0 :
                            dirrectionaly_stable = False
                            log.error('At alt = ' + str(alt) + 'Vehicle directionnaly staticaly neutral stable.')
                        if side_moment_derivative < 0 :
                            dirrectionaly_stable = False
                            log.error('Alt = '  + str(alt) + 'Vehicle *NOT* directionnaly staticaly stable.')

                    # If not stable store the set [alt, mach, aos] at which the aircraft is unstable.
                    if not dirrectionaly_stable :
                        direc_unstable_cases.append([alt,mach,aoa])
                        # To write in the output CPACS that the aircraft is not longitudinaly stable
                        cpacs_stability_direc = False

            # PLot cml VS aos for constant alt, mach and different aoa if not stable
            if direc_unstable_cases:
                plot_multicurve(plot_cml, plot_aos, plot_legend, plot_title, xlabel, ylabel, show_plots, save_plots)

        # Add trim conditions for the given altitude (longi analysis)
        if trim_aoa_longi:
            trim_aoa_longi_list.append(trim_aoa_longi)
            trim_mach_longi_list.append(trim_mach_longi)
            trim_legend_longi_list.append('Alt = ' + str(alt) + '[m]')
            trim_alt_longi_list.append(trim_alt_longi)
            trim_aos_longi_list.append(trim_aos_longi)

        # Add trim conditions for the given altitude (direcanalysis)
        if trim_aos_direc:
            trim_aos_direc_list.append(trim_aos_direc)
            trim_mach_direc_list.append(trim_mach_direc)
            trim_legend_direc_list.append('Alt = ' + str(alt) + '[m]')
            trim_alt_direc_list.append(trim_alt_direc)
            trim_aoa_direc_list.append(trim_aoa_direc)

        # Plot cms vs aoa for const alt and aos and different mach
        for aos in aos_unic:
            idx_aos = [k for k in range(len(aos_list)) if aos_list[k] == aos]
            plot_cms = []
            plot_aoa = []
            plot_legend= []
            plot_title = 'cms vs aoa @ atl = ' + str(alt) + ' m and aos = ' + str(aos)
            xlabel= 'Angle of attack [deg]'
            ylabel= 'cms'
            # Init for determinig if it is an unstability case
            longitudinaly_stable = True

            for mach in mach_unic:

                find_idx = get_index(mach_list,mach,idx_alt,idx_aos)

                # If there is only one value in Find_idx
                # An error message has been already printed through the first part of the code
                # Check if it is an unstability case detected previously
                for combination in longi_unstable_cases :
                    if combination[0] == alt and combination[1] == mach and combination[2] == aos :
                        longitudinaly_stable = False

                # If there is at list 2 values in find_idx :
                if len(find_idx) > 1:
                    # Find all cms_list values for index corresonding to an altitude, a mach, an aos_list=0, and different aoa_list
                    cms = []
                    aoa = []
                    for index in find_idx:
                        cms.append(cms_list[index])
                        aoa.append(aoa_list[index])

                    # Save values which will be plot
                    plot_cms.append(cms)
                    plot_aoa.append(aoa)
                    curve_legend = 'Mach = ' + str(mach)
                    plot_legend.append(curve_legend)

            if not longitudinaly_stable:
                #PLot cms VS aoa for constant Alt, aoa and different mach
                plot_multicurve(plot_cms, plot_aoa, plot_legend, plot_title, xlabel, ylabel, show_plots, save_plots)

        # Plot cml vs aos for const alt and aoa and different mach
        for aoa in aoa_unic:
            idx_aoa = [k for k in range(len(aoa_list)) if aoa_list[k] == aoa]
            plot_cml = []
            plot_aos = []
            plot_legend = []
            plot_title  = 'cml vs aos @ atl = ' + str(alt) + ' m and aoa = ' + str(aoa)
            xlabel = 'Angle of sideslip [deg]'
            ylabel = 'cml'
            # Init for determinig if it is an unstability case
            dirrectionaly_stable = True

            for mach in mach_unic:

                find_idx = get_index(mach_list,mach,idx_alt,idx_aoa)

                #If there is only one valur in find_idx
                # An error message has been already printed through the first part of the code

                # Check if it is an unstability case detected previously
                for combination in direc_unstable_cases :
                    if combination[0] == alt and combination[1] == mach and combination[2] == aoa :
                        dirrectionaly_stable = False

                # If there is at list 2 values in find_idx :
                if len(find_idx) > 1:
                    # Find all cml_list values for index corresonding to an altitude, a mach, an aos_list=0, and different aoa_list
                    cml = []
                    aos = []
                    for index in find_idx:
                        cml.append(cml_list[index])
                        aos.append(aos_list[index])

                    # Save values which will be plot
                    plot_cml.append(cml)
                    plot_aos.append(aos)
                    curve_legend = 'Mach = ' + str(mach)
                    plot_legend.append(curve_legend)

            if not dirrectionaly_stable:
                # Plot cml VS aos for constant Alt, aoa and different mach
                plot_multicurve(plot_cml, plot_aos, plot_legend, plot_title, xlabel, ylabel, show_plots, save_plots)

    # Plot trim_aoa VS mach for different alt
    # If there is at least 1 element in list of trim conditions then, plot them

    if trim_aoa_longi_list:
        log.info('graph : cruising aoa vs mach genrated')
        plot_multicurve(trim_aoa_longi_list, trim_mach_longi_list, trim_legend_longi_list, 'trim_aoa vs mach', 'mach', 'Angle of attack [deg]', show_plots, save_plots)

    # plot cms VS aoa for constant mach, aos_list and different altitudes:
    for aos in aos_unic:
        # Find index of altitude which have the same value
        idx_aos = [i for i in range(len(aos_list)) if aos_list[i] == aos]
        for mach in mach_unic:
            # Find index of mach which have the same value
            idx_mach = [j for j in range(len(mach_list)) if mach_list[j] == mach]
            # Prepare variables for plots
            plot_cms = []
            plot_aoa = []
            plot_legend = []
            plot_title = 'cms vs aoa @ Mach = ' + str(mach) + ' and aos = '+ str(aos)
            xlabel = 'Angle of attack [deg]'
            ylabel = 'cms'

            longitudinaly_stable = True

            # Find index of slip angle which have the same value
            for alt in alt_unic:

                find_idx = get_index(alt_list,alt,idx_aos,idx_mach)

                # If find_idx is empty an APM function would have corrected before
                # If there is only one value  in  find_idx for a given Alt, Mach, aos_list, no analyse can be performed
                # An error message has been already printed through the first part of the code

                # Check if it is an unstability case detected previously
                for combination in longi_unstable_cases :
                    if combination[0] == alt and combination[1] == mach and combination[2] == aos :
                        longitudinaly_stable = False

                # If there is at list 2 values in find_idx :
                if len(find_idx) > 1:
                    # Find all cms_list values for index corresonding to an altitude, a mach, an aos_list=0, and different aoa_list
                    cms = []
                    aoa = []
                    for index in find_idx:
                        cms.append(cms_list[index])
                        aoa.append(aoa_list[index])

                    # Save values which will be plot
                    plot_cms.append(cms)
                    plot_aoa.append(aoa)
                    curve_legend = 'Altitude = ' + str(alt)
                    plot_legend.append(curve_legend)

            if not longitudinaly_stable:
                # PLot cms VS aoa for constant  Mach, aos and different Alt
                plot_multicurve(plot_cms, plot_aoa, plot_legend, plot_title, xlabel, ylabel, show_plots, save_plots)

    # plot cml VS aos for constant mach, aoa_list and different altitudes:
    for aoa in aoa_unic:
        # Find index of altitude which have the same value
        idx_aoa = [i for i in range(len(aoa_list)) if aoa_list[i] == aoa]
        for mach in mach_unic:
            # Find index of mach which have the same value
            idx_mach = [j for j in range(len(mach_list)) if mach_list[j] == mach]
            # Prepare variables for plots
            plot_cml = []
            plot_aos = []
            plot_legend = []
            plot_title = 'cml vs aos @ Mach = ' + str(mach) + ' and aoa = ' + str(aoa)
            xlabel= 'Angle of sideslip [deg]'
            ylabel= 'cml'

            dirrectionaly_stable = True

            # Find index of slip angle which have the same value
            for alt in alt_unic:

                find_idx = get_index(alt_list,alt,idx_aoa,idx_mach)

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
                    cml = []
                    aos = []
                    for index in find_idx:
                        cml.append(cml_list[index])
                        aos.append(aos_list[index])

                    # Save values which will be plot
                    plot_cml.append(cml)
                    plot_aos.append(aos)
                    curve_legend = 'Altitude = ' + str(alt)
                    plot_legend.append(curve_legend)

            if not dirrectionaly_stable:
            # PLot cml VS aos for constant  Mach, aoa and different alt
                plot_multicurve(plot_cml, plot_aos, plot_legend, plot_title, xlabel, ylabel, show_plots, save_plots)

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
    static_analysis_xpath = '/cpacs/toolspecific/CEASIOMpy/stability/static'

    aeromap_uid_xpath =   static_analysis_xpath + '/aeroMapUid'
    longi_xpath = static_analysis_xpath + '/results/longitudinalStaticStable'
    direc_xpath = static_analysis_xpath + '/results/directionnalStaticStable'

    # If branch does not exist
    if not tixi.checkElement(aeromap_uid_xpath):
        create_branch(tixi,aeromap_uid_xpath, False)
        add_string_vector(tixi, aeromap_uid_xpath, [aeromap_uid])

    if not tixi.checkElement(longi_xpath) :
        create_branch(tixi, longi_xpath,False)
    if not tixi.checkElement(direc_xpath) :
        create_branch(tixi, direc_xpath,False)

    # Store in the CPCS the stability results
    add_string_vector(tixi, longi_xpath, [cpacs_stability_longi])
    add_string_vector(tixi, direc_xpath, [cpacs_stability_direc])

    longi_trim_xpath = static_analysis_xpath +'/trimconditions/longitudinal'
    direc_trim_xpath = static_analysis_xpath +'/trimconditions/directional'

    create_branch(tixi,longi_trim_xpath,False)
    create_branch(tixi,direc_trim_xpath,False)

    print(trim_alt_longi_list)
    add_float_vector(tixi,longi_trim_xpath+'/altitude',trim_alt_longi_list)
    add_float_vector(tixi,longi_trim_xpath+'/machNumber',trim_mach_longi_list)
    add_float_vector(tixi,longi_trim_xpath+'/angleOfAttack',trim_aoa_longi_list)
    add_float_vector(tixi,longi_trim_xpath+'/angleOfSideslip',trim_aos_longi_list)

    add_float_vector(tixi,direc_trim_xpath+'/altitude',trim_alt_longi_list)
    add_float_vector(tixi,direc_trim_xpath+'/machNumber',trim_mach_longi_list)
    add_float_vector(tixi,direc_trim_xpath+'/angleOfAttack',trim_aoa_longi_list)
    add_float_vector(tixi,direc_trim_xpath+'/angleOfSideslip',trim_aos_longi_list)

    close_tixi(tixi, cpacs_out_path)

#==============================================================================
#    MAIN
#==============================================================================


if __name__ == '__main__':

    log.info('----- Start of ' + MODULE_NAME + ' -----')

    cpacs_path = get_toolinput_file_path(MODULE_NAME)
    cpacs_out_path = get_tooloutput_file_path(MODULE_NAME)

    # Call the function which check if imputs are well define
    check_cpacs_input_requirements(cpacs_path)

    # Call the main function for static stability analysis
    static_stability_analysis(cpacs_path, cpacs_out_path)

    log.info('----- End of ' + MODULE_NAME + ' -----')
