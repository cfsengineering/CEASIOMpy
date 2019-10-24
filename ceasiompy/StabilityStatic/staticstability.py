"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Static stability modu

Python version: >=3.6

| Author: Name
| Creation: YEAR-MONTH-DAY
| Last modifiction: YEAR-MONTH-DAY

TODO:

    * Things to improve ...
    * Things to add ...
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
#   CLASSES
#==============================================================================

# class MyClass:
#     """
#     Description of the class
#
#     Attributes:
#         var_a (float): Argument a [unit]
#         var_b (float): Argument b [unit]
#
#     .. seealso::
#
#         See some other source
#
#     """
#
#     def __init__(self, a=1.1, b=2.2):
#         self.var_a = a
#         self.var_b = b
#         self.var_c = 0.0
#
#     def add_my_var(self):
#         """This methode will sum up var_a and var_b in var_c"""
#
#         self.var_c = self.var_a + self.var_b


#==============================================================================
#   FUNCTIONS
#==============================================================================

def Find_Unic(vector, vector_unic=[]):
    """Function to get all the different values in a vector if tha values are repeated
    Args:
        avector of number
    Returns:
        veccror_unic; a vector with only one occurence of all the different values of "vector"
    """
    for element in vector :
        if element not in vector_unic :
            vector_unic.append(element)
    return vector_unic

    
def myplot(x_axis, y_axis, list_legend, plot_title, xlabel, ylabel):
    """Function to plot graph with different curves for a varying parameter

    Function 'myplot' can plot few curves

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
    # Move left y-axis and bottim x-axis to centre, passing through (0,0)
    ax = plt.gca()
    # Set the axis's spines to be centered at the given point
    # (Setting all 4 spines so that the tick marks go in both directions)
    centerx = 0
    centery = 0
    ax.spines['left'].set_position(('data', centerx))
    ax.spines['bottom'].set_position(('data', centery))
    # ax.spines['right'].set_position(('data', centerx - 1))
    # ax.spines['top'].set_position(('data', centery - 1))
    # Hide the line (but not ticks) for "extra" spines
    for side in ['right', 'top']:
        ax.spines[side].set_color('none')

    for n in range(len(x_axis)):
        plt.plot(x_axis[n], y_axis[n], marker='o', markersize=4, linewidth=1)

    ax.legend(list_legend, loc='upper right')

    plt.show()

def staticStabilityAnalysis(cpacs_path, aeromap_uid):
    """Function to analyse a full Aeromap

    Function 'myplot' can plot few curves
    Longitudinal static staticStabilityAnalysis
    Directionnal static analysis

    Args:
        Cpacs file paths
        Aeromap uid

    Returns:
        Adrvertisements certifying if the aircraft is stable or Not
        Make the following tests:

        Plot CML VS angle of list_attack
        Plot CMS VS angle of list_slip
        Plot the cruising angle of attack for different mach and altitudes

    """

    #Open tixi handles
    tixi = open_tixi(cpacs_path)
    # Coeffs lists
    Coeffs = get_aeromap(tixi, aeromap_uid)


    ALT = Coeffs.alt
    MACH = Coeffs.mach

    AOA = Coeffs.aoa
    CML = Coeffs.cml

    AOS = Coeffs.aos
    CMS = Coeffs.cms

    # Fill the lists of unique different values
    alt_unic = Find_Unic(ALT)
    mach_unic = Find_Unic(MACH)
    aos_unic = Find_Unic(AOS)
    aoa_unic = Find_Unic(AOA)

    # Plot : trim Aoa for gien alt and different mach
    #           trim Aoa for gien Mach and different alt
    # Gather trim AOA for different Alt & mach , for AOS  = 0

    trim_aoa_list = []
    trim_mach_list = []
    longiUnstableCases = []
    direcUnstableCases = []

    # Aero analyses for all given Altitude, Mach and AOS, over different
    for alt in alt_unic:
        print("*****Alt : " + str(alt))
        # Find index of altitude which have the same value
        idx_alt = [i for i in range(len(ALT)) if ALT[i] == alt]

        # Prepar trim condition lists
        trim_aoa =[]
        trim_mach = []
        trim_legend = []

        for mach in mach_unic:
            print("***MACH : " + str(mach))
            # Find index of mach which have the same value
            idx_mach = [j for j in range(len(MACH)) if MACH[j] == mach]

    # Longitudinal stability
            count_aos = 0
        # Analyse in function of  the angle of attack for given, Alt, Mach and AOS
            # Prepare variables for plots
            list_cml = []
            list_aoa = []
            list_legend = []
            plot_title = "Cml vs aoa, @Atl = " + str(alt) + " and Mach = " + str(mach)
            xlabel= "aoa"
            ylabel= "Cml"
            # Init for determining if it's an unstable case
            LongitudinalyStable = True
            # Find index of slip angle which have the same value

            for aos in aos_unic:
                # by default, don't  cross 0 line
                crossed = False
                print("**AOS: " + str(count_aos))
                count_aos += 1
                idx_aos = [k for k in range(len(AOS)) if AOS[k] == aos]
                # List of index of elements which have the same index  in vectors ALT, MACH, AOS
                find_idx = []
                # Fill   the liste find_index
                for idx1 in idx_alt:
                    for idx2 in idx_mach:
                        for idx3 in idx_aos:
                            if idx1 == idx2 == idx3:
                                find_idx.append(idx1)

                #print("At alt = " + str(alt) + " , mach = " + str(mach) + " and aos = " + str(aos) + " , find_list : " + str(find_idx))

                # If find_idx is empty an APM function would have corrected before
                # If there there is only one value  in  find_idx for a given Alt, Mach, AOS, no analyse can be performed
                if len(find_idx) == 1:
                    log.info("Only one data, one AOA("+str(AOA[idx1])+"), for Altitude = " + str(alt) +
                             " , Mach = " + str(mach) + " and AOS = " + str(aos) + " no stability analyse performed")
                # If there is at least 2 values in find_idx :
                if len(find_idx) > 1:
                    # Find all CML values for index corresonding to an altitude, a mach, an AOS=0, and different AOA
                    cml = []
                    aoa = []
                    for index in find_idx:
                        cml.append(CML[index])
                        aoa.append(AOA[index])

                    curve_legend = "aos = " + str(aos) + "°"

                    # Store  Cml values in cml_list
                    list_cml.append(cml)
                    # Store list_attack in list_list_attack
                    list_aoa.append(aoa)
                    # Store the legend in list_legend
                    list_legend.append(curve_legend)

                    # If all aoa values are the same while the calculating the derivative, a division by zero will be prevented.
                    aoaGood = True
                    for jj in range(len(aoa)-1) :
                        if  aoa[jj] == aoa[jj+1] and  aoaGood == True :
                            aoaGood = False
                            log.warning("At least 2 aoa values are equal in aoa list: {} at Alt = {}, Mach= {}, aos = {}".format(aoa, alt, mach, aos))
                    # retrieve the index in of element in cml just before crossing 0,
                    # np.argwher returns an array as [[idx]], that'a why there is [0][0] at the end
                    # If cml curve does not cross the 0
                    if len(np.argwhere(np.diff(np.sign(cml)))) == 0  :
                        # If all Cml values are 0:
                        LongitudinalyStable = False
                        longiUnstableCases.append([alt,mach,aos])
                        if cml.count(0) == len(cml):
                            log.info("Cml list is composed of 0 only.")
                        else:
                            log.info("The aircraft has a cruising AOA at which Cml is not 0.")
                    # If cml Curve crosses the 0 line more than once no stability analysis can be performed
                    if len(np.argwhere(np.diff(np.sign(cml)))) > 2 or cml.count(0) > 1:
                        log.info("The Cml curves crosses more than once the 0 line, no stability analysis performed")
                        LongitudinalyStable = False
                        longiUnstableCases.append([alt,mach,aos])
                    # If cml Curve crosses the 0 line twice
                    if 0 not in np.sign(cml) and len(np.argwhere(np.diff(np.sign(cml)))) == 2:
                        log.info("The Cml curves crosses the 0 line twice, no stability analysis performed")
                        LongitudinalyStable = False
                        longiUnstableCases.append([alt,mach,aos])
                    # If Cml = 0 is in Cml list  only once
                    if 0 in np.sign(cml) and cml.count(0) == 1 and aoaGood == True:
                        idx_cml_0 = [i for i in range(len(cml)) if cml[i] == 0][0]

                        # If Cml = 0 is the first element in cml list, take the derivative at right
                        if idx_cml_0 == 0:
                            # Angles and coeffs before and after crossing the 0 line
                            aoa_before = AOA[find_idx[idx_cml_0]]
                            aoa_after = AOA[find_idx[idx_cml_0+1]]
                            cml_before = CML[find_idx[idx_cml_0]]
                            cml_after = CML[find_idx[idx_cml_0+1]]

                            cruise_aoa = aoa_before
                            pitch_moment_derivative = (cml_after-cml_before)/(aoa_after-aoa_before)

                        # If cml = 0 is the last element of cml list, take the derivative at left
                        if idx_cml_0 == len(cml)-1:
                            # Angles and coeffs before and after crossing the 0 line
                            aoa_before = AOA[find_idx[idx_cml_0-1]]
                            aoa_after = AOA[find_idx[idx_cml_0]]
                            cml_before = CML[find_idx[idx_cml_0-1]]
                            cml_after = CML[find_idx[idx_cml_0]]

                            cruise_aoa = aoa_after
                            pitch_moment_derivative = (cml_after-cml_before)/(aoa_after-aoa_before)

                        # If cml = 0 is nor the first nor the last element in cml list, take the centered derivative
                        if 0 < idx_cml_0 < len(cml)-1:
                            # Angles and coeffs before and after crossing the 0 line
                            aoa_before = AOA[find_idx[idx_cml_0-1]]
                            aoa_after = AOA[find_idx[idx_cml_0+1]]
                            cml_before = CML[find_idx[idx_cml_0-1]]
                            cml_after = CML[find_idx[idx_cml_0+1]]

                            cruise_aoa = AOA[find_idx[idx_cml_0]]
                            pitch_moment_derivative = (cml_after-cml_before)/(aoa_after-aoa_before)
                    # If Cml crosses the 0 line once and Cml=0 is not in cml list
                    if  len(np.argwhere(np.diff(np.sign(cml)))) == 1 and 0 not in np.sign(cml) and aoaGood == True:
                        # Make the linear equation btween the 2 point before and after crossing lthe 0 ine y=ax+b
                        crossed = True
                        idx_cml_0 = np.argwhere(np.diff(np.sign(cml)))[0][0]

                        # Angles and coeffs before and after crossing the 0 line
                        aoa_before = AOA[find_idx[idx_cml_0]]
                        aoa_after = AOA[find_idx[idx_cml_0+1]]

                        cml_before = CML[find_idx[idx_cml_0]]
                        cml_after = CML[find_idx[idx_cml_0+1]]

                        fit = np.polyfit([aoa_before, aoa_after], [cml_before, cml_after], 1)  # returns [a,b] of y=ax+b
                        cruise_aoa = -fit[1]/fit[0]    # Cml = 0 for y = 0  hence cruise agngle = -b/a
                        pitch_moment_derivative = fit[0]

                    if aos == 0 and crossed == True and aoaGood == True:
                        trim_mach.append(mach)
                        trim_aoa.append(cruise_aoa)

                    if crossed== True and aoaGood == True:
                        if pitch_moment_derivative < 0 :
                            log.info("Vehicle longitudinaly staticaly stable  :) ")
                        if pitch_moment_derivative == 0 :
                            LongitudinalyStable = False
                            longiUnstableCases.append([alt,mach,aos])
                            log.info("Vehicle longitudinaly staticaly neutral stable  :| ")
                        if pitch_moment_derivative > 0 :
                            LongitudinalyStable = False
                            longiUnstableCases.append([alt,mach,aos])
                            log.info("Vehicle *NOT* longitudinaly staticaly stable :( ")
                    #print( LongitudinalyStable)
            if  LongitudinalyStable == False:
                # PLot Cml VS aoa for constant Alt, Mach and different aos
                myplot(list_aoa, list_cml, list_legend, plot_title, xlabel, ylabel)

    # Dirrectional Stability analysis
            count_aoa = 0

            list_cms = []
            list_aos = []
            list_legend = []
            plot_title = "Cms vs aos, @Atl = " + str(alt) + " and Mach = " + str(mach)
            xlabel= "aos"
            ylabel= "Cms"
            # Init for determinig if it is an unstability case
            DirrectionalyStable = True
            # Find INDEX
            for aoa in aoa_unic:
                # by default, don't  cross 0 line
                crossed = False
                print("**AOA: " + str(count_aoa))
                count_aoa += 1
                idx_aoa = [jj for jj in range(len(AOA)) if AOA[jj] == aoa]
                # List of index of elements which have the same index  in vectors ALT, MACH, AOS
                find_idx = []
                # Fill   the liste find_index
                for idx1 in idx_alt:
                    for idx2 in idx_mach:
                        for idx3 in idx_aoa:
                            if idx1 == idx2 == idx3:
                                find_idx.append(idx1)

                # print("At alt = " + str(altitude) + " , mach = " + str(mach_number) + " and aoa = " + str(attack) + " , find_idx : " + str(find_idx))

                # If find_idx is empty an APM function would have corrected before
                # If there there is only one value  in  find_idx for a given Alt, Mach, AOS, no analyse can be performed
                if len(find_idx) == 1:
                    log.info("Only one data, one AOS("+str(AOS[idx1])+"), for Altitude = " + str(alt) +
                             " , Mach = " + str(mach) + " and AOA = " + str(aoa) + " no stability analyse performed")
                # If there is at list 2 values in find_idx :
                if len(find_idx) > 1:
                    cms = []
                    aos = []
                    for index in find_idx:
                        cms.append(CMS[index])
                        aos.append(AOS[index])

                    # print("cml : " + str(cms))
                    # retrieve the index in of element in cml just before crossing 0,
                    # np.argwher returns an array as [[idx]], that'a why there is [0][0] at the end
                    #  If cms Curve crosses th 0 line more than once na stability analysis can be performed
                    curve_legend = "aoa = " + str(aoa) + "°"
                    # Store  Cms values in cml_list
                    list_cms.append(cms)
                    # Store the list of aos  in list_aos
                    list_aos.append(aos)
                    # Store the legend in list_legend
                    list_legend.append(curve_legend)

                    # If all aoa values are the same while the calculating the derivative, a division by zero will be prevented.
                    aosGood = True
                    for jj in range(len(aos)-1) :
                        if  aos[jj] == aos[jj+1] and  aosGood == True :
                            aosGood = False
                            log.warning("At least 2 values are equal in aos list: {} at Alt = {}, Mach= {}, aoa = {}".format(aos, alt, mach, aoa))
                    # If cml curve does not cross the 0
                    if len(np.argwhere(np.diff(np.sign(cms)))) == 0  :
                        DirrectionalyStable = False
                        direcUnstableCases.append([alt, mach, aoa])
                        # If all Cms values are 0:
                        if cms.count(0) == len(cms):
                            log.info("Cms list is composed of 0 only.")
                        else:
                            log.info("The aircraft has a cruising AOS at which Cms is not 0.")
                    # If cms Curve crosses the 0 line more than once no stability analysis can be performed
                    if len(np.argwhere(np.diff(np.sign(cms)))) > 2 or cms.count(0) > 1:
                        DirrectionalyStable = False
                        direcUnstableCases.append([alt, mach, aoa])
                        log.info("The Cms curves crosses more than once the 0 line, no stability analysis performed")
                    # If cms Curve crosses the 0 line twice
                    if 0 not in np.sign(cms) and len(np.argwhere(np.diff(np.sign(cms)))) == 2:
                        DirrectionalyStable = False
                        direcUnstableCases.append([alt, mach, aoa])
                        log.info("The Cms curves crosses the 0 line twice, no stability analysis performed")
                    # If Cms = 0 is in Cml list
                    if 0 in np.sign(cms) and cms.count(0) == 1 and aosGood == True:
                        crossed = True
                        idx_cms_0 = [i for i in range(len(cms)) if cms[i] == 0][0]
                        # If Cml = 0 is the first element in cml list, take the derivative at right
                        if idx_cms_0 == 0:
                            # Angles and coeffs before and after crossing the 0 line
                            aos_before = AOS[find_idx[idx_cms_0]]
                            aos_after = AOS[find_idx[idx_cms_0+1]]
                            cms_before = CMS[find_idx[idx_cms_0]]
                            cms_after = CMS[find_idx[idx_cms_0+1]]

                            cruise_aos = aos_before
                            side_moment_derivative = (cms_after-cms_before)/(aos_after-aos_before)

                        # If cml = 0 is the last element of cml list, take the derivative at left
                        if idx_cms_0 == len(cms) - 1:
                            # Angles and coeffs before and after crossing the 0 line
                            aos_before = AOS[find_idx[idx_cms_0-1]]
                            aos_after = AOS[find_idx[idx_cms_0]]
                            cms_before = CMS[find_idx[idx_cms_0-1]]
                            cms_after = CMS[find_idx[idx_cms_0]]

                            cruise_aos = aos_after
                            side_moment_derivative = (cms_after-cms_before)/(aos_after-aos_before)

                        # If cml = 0 is nor the first nor the last element in cml list, take the centered derivative
                        if 0 < idx_cms_0 < len(cms)-1:
                            # Angles and coeffs before and after crossing the 0 line
                            aos_before = AOS[find_idx[idx_cms_0-1]]
                            aos_after = AOS[find_idx[idx_cms_0+1]]
                            cms_before = CMS[find_idx[idx_cms_0-1]]
                            cms_after = CMS[find_idx[idx_cms_0+1]]

                            cruise_aos = AOS[find_idx[idx_cms_0]]
                            side_moment_derivative = (cms_after - cms_before)/(aos_after - aos_before)
                    # If Cms crosses the 0 line once and Cms=0 is not in cml list
                    if  len(np.argwhere(np.diff(np.sign(cms)))) == 1 and 0 not in np.sign(cms) and aosGood == True:
                        # Make the linear equation btween the 2 point before and after crossing the 0 ine y=ax+b
                        crossed = True
                        idx_cms_0 = np.argwhere(np.diff(np.sign(cms)))[0][0]

                        # Angles and coeffs before and after crossing the 0 line
                        aos_before = AOS[find_idx[idx_cms_0]]
                        aos_after = AOS[find_idx[idx_cms_0+1]]

                        cms_before = CMS[find_idx[idx_cms_0]]
                        cms_after = CMS[find_idx[idx_cms_0+1]]

                        fit = np.polyfit([aos_before, aos_after], [cms_before, cms_after], 1)  # returns [a,b] of y=ax+b
                        cruise_aos = -fit[1]/fit[0]    # Cms = 0 for y = 0  hence cruise agngle = -b/a
                        side_moment_derivative = fit[0]

                    if crossed== True and aosGood == True:
                        if side_moment_derivative > 0 :
                            log.info("Vehicle directionnaly staticaly stable  :) ")
                        if side_moment_derivative == 0 :
                            DirrectionalyStable = False
                            direcUnstableCases.append([alt, mach, aoa])
                            log.info("Vehicle directionnaly staticaly neutral stable  :| ")
                        if side_moment_derivative < 0 :
                            DirrectionalyStable = False
                            direcUnstableCases.append([alt, mach, aoa])
                            log.info("Vehicle *NOT* directionnaly staticaly stable :( ")

            if DirrectionalyStable == False :
                # PLot Cms VS aos for constant Alt, Mach and different aoa
                myplot(list_aos, list_cms, list_legend, plot_title, xlabel, ylabel)

        # Plot cml vs aoa for const alt and aos and different mach
        for aos in aos_unic:
            idx_aos = [k for k in range(len(AOS)) if AOS[k] == aos]
            list_cml = []
            list_aoa = []
            list_legend= []
            plot_title = "Cml vs aoa, @Atl = " + str(alt) + " and aos = " + str(aos)
            xlabel= "aoa"
            ylabel= "Cml"
            # Init for determinig if it is an unstability case
            LongitudinalyStable = True

            for mach in mach_unic:
                idx_mach = [k for k in range(len(MACH)) if MACH[k] == mach]
                # List of index of elements which have the same index  in vectors ALT, MACH, AOS
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
                for combination in longiUnstableCases :
                    if combination[0] == alt and combination[1] == mach and combination[2] == aos :
                        LongitudinalyStable = False

                # If there is at list 2 values in find_idx :
                if len(find_idx) > 1:
                    # Find all CML values for index corresonding to an altitude, a mach, an AOS=0, and different AOA
                    cml = []
                    aoa = []
                    for index in find_idx:
                        cml.append(CML[index])
                        aoa.append(AOA[index])

                    curve_legend = "Mach = " + str(mach)

                    # Store  Cml values in cml_list
                    list_cml.append(cml)
                    # Store list_attack in list_list_attack
                    list_aoa.append(aoa)
                    # Store the legend in list_legend
                    list_legend.append(curve_legend)
            if LongitudinalyStable == False :
                #PLot Cml VS aoa for constant Alt, aoa and different mach
                myplot(list_aoa, list_cml, list_legend, plot_title, xlabel, ylabel)

        # Plot cms vs aos for const alt and aoa and different mach
        for aoa in aoa_unic:
            idx_aoa = [k for k in range(len(AOA)) if AOA[k] == aoa]
            list_cms = []
            list_aos = []
            list_legend = []
            plot_title  = "Cms vs aos, @Atl = " + str(alt) + " and aoa = " + str(aoa)
            xlabel = "aos"
            ylabel = "Cms"
            # Init for determinig if it is an unstability case
            DirrectionalyStable = True

            for mach in mach_unic:
                idx_mach = [k for k in range(len(MACH)) if MACH[k] == mach]
                # List of index of elements which have the same index  in vectors ALT, MACH, AOS
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
                for combination in direcUnstableCases :
                    if combination[0] == alt and combination[1] == mach and combination[2] == aoa :
                        DirrectionalyStable = False

                # If there is at list 2 values in find_idx :
                if len(find_idx) > 1:
                    # Find all CML values for index corresonding to an altitude, a mach, an AOS=0, and different AOA
                    cms = []
                    aos= []
                    for index in find_idx:
                        cms.append(CMS[index])
                        aos.append(AOS[index])

                    curve_legend = "Mach = " + str(mach)

                    # Store  Cml values in cml_list
                    list_cms.append(cms)
                    # Store list_attack in list_list_attack
                    list_aos.append(aos)
                    # Store the legend in list_legend
                    list_legend.append(curve_legend)

            if DirrectionalyStable == False :
                # Plot Cms VS aos for constant Alt, aoa and different mach
                myplot(list_aos, list_cms, list_legend, plot_title, xlabel, ylabel)

        # Add trim conditions for the given altitude
        trim_aoa_list.append(trim_aoa)
        trim_mach_list.append(trim_mach)
        trim_legend.append("Alt = " + str(alt))

    # Plot trim_aoa VS mach for different alt
    # If there is at least 1 element in list of trim conditions then, plot them
    if len(trim_aoa_list) >= 1:
        myplot(trim_mach_list, trim_aoa_list, trim_legend, "trim_aoa VS mach", "aoa","mach")

    # plot Cml VS aoa for constant mach, AOS and different altitudes:
    for aos in aos_unic:
        # Find index of altitude which have the same value
        idx_aos = [i for i in range(len(AOS)) if AOS[i] == aos]
        for mach in mach_unic:
            # Find index of mach which have the same value
            idx_mach = [j for j in range(len(MACH)) if MACH[j] == mach]
            # Prepare variables for plots
            list_cml = []
            list_aoa = []
            list_legend = []
            plot_title = "Cml vs aoa, @ Mach = " + str(mach) + " and aos = " + str(aos)
            xlabel = "aoa"
            ylabel = "Cml"

            LongitudinalyStable == True

            # Find index of slip angle which have the same value
            for alt in alt_unic:
                idx_alt = [k for k in range(len(ALT)) if ALT[k] == alt]
                # List of index of elements which have the same index  in vectors ALT, MACH, AOS
                find_idx = []
                # Fill   the liste find_index
                for idx3 in idx_aos:
                    for idx2 in idx_mach:
                        for idx1 in idx_alt:
                            if idx1 == idx2 == idx3:
                                find_idx.append(idx1)

                # print("At alt = " + str(altitude) + " , mach = " + str(mach_number) + " and aos = " + str(slip) + " , find_list : " + str(find_idx))

                # If find_idx is empty an APM function would have corrected before
                # If there there is only one value  in  find_idx for a given Alt, Mach, AOS, no analyse can be performed
                # An error message has been already printed through the first part of the code

                # Check if it is an unstability case detected previously
                for combination in longiUnstableCases :
                    if combination[0] == alt and combination[1] == mach and combination[2] == aos :
                        LongitudinalyStable = False

                # If there is at list 2 values in find_idx :
                if len(find_idx) > 1:
                    # Find all CML values for index corresonding to an altitude, a mach, an AOS=0, and different AOA
                    cml = []
                    aoa = []
                    for index in find_idx:
                        cml.append(CML[index])
                        aoa.append(AOA[index])

                    curve_legend = "Altitude = " + str(alt)

                    # Store  Cml values in cml_list
                    list_cml.append(cml)
                    # Store list_attack in list_list_attack
                    list_aoa.append(aoa)
                    # Store the legend in list_legend
                    list_legend.append(curve_legend)

            if LongitudinalyStable == False :
                # PLot Cml VS aoa for constant  Mach, aos and different Alt
                myplot(list_aoa, list_cml, list_legend, plot_title, xlabel, ylabel)

    # plot Cms VS aos for constant mach, AOA and different altitudes:
    for aoa in aoa_unic:
        # Find index of altitude which have the same value
        idx_aoa = [i for i in range(len(AOA)) if AOA[i] == aoa]
        for mach in mach_unic:
            # Find index of mach which have the same value
            idx_mach = [j for j in range(len(MACH)) if MACH[j] == mach]
            # Prepare variables for plots
            list_cms = []
            list_aos = []
            list_legend = []
            plot_title = "Cms vs aos, @ Mach = " + str(mach) + " and aoa= " + str(aoa)
            xlabel= "aos"
            ylabel= "Cms"

            DirrectionalyStable == True

            # Find index of slip angle which have the same value
            for alt in alt_unic:
                idx_alt = [k for k in range(len(ALT)) if ALT[k] == alt]
                # List of index of elements which have the same index  in vectors ALT, MACH, AOS
                find_idx = []
                # Fill   the liste find_index
                for idx3 in idx_aoa:
                    for idx2 in idx_mach:
                        for idx1 in idx_alt:
                            if idx1 == idx2 == idx3:
                                find_idx.append(idx1)
                # If find_idx is empty an APM function would have corrected before
                # If there there is only one value  in  find_idx for a given Alt, Mach, AOS, no analyse can be performed
                # An error message has been already printed through the first part of the code

                # Check if it is an unstability case detected previously
                for combination in direcUnstableCases :
                    if combination[0] == alt and combination[1] == mach and combination[2] == aoa :
                        DirrectionalyStable = False

                # If there is at list 2 values in find_idx :
                if len(find_idx) > 1:
                    # Find all CML values for index corresonding to an altitude, a mach, an AOS=0, and different AOA
                    cms = []
                    aos = []
                    for index in find_idx:
                        cms.append(CMS[index])
                        aos.append(AOS[index])

                    curve_legend = "Altitude = " + str(alt)

                    # Store  Cml values in cml_list
                    list_cms.append(cms)
                    # Store list_attack in list_list_attack
                    list_aos.append(aos)
                    # Store the legend in list_legend
                    list_legend.append(curve_legend)

            if DirrectionalyStable == False :
                # PLot Cms VS aos for constant  Mach, aoa and different alt
                myplot(list_aos, list_cms, list_legend, plot_title, xlabel, ylabel)


#==============================================================================
#    MAIN
#==============================================================================


if __name__ == '__main__':

    log.info('----- Start of ' + os.path.basename(__file__) + ' -----')

    MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
    cpacs_path = os.path.join(MODULE_DIR,'ToolInput','cpacs_test_file.xml')

    # Call the function which check if imputs are well define
    check_cpacs_input_requirements(cpacs_path)

#For tests:
    cpacs_out_path = os.path.join(MODULE_DIR,'ToolInput','cpacs_test_file.xml')
    csv_path = "/Users/Loic/github/CEASIOMpy/ceasiompy/StabilityStatic/ToolInput/testlolo.csv"
    # Open tixi Handle
    tixi = open_tixi(cpacs_path)
    # Get Aeromap UID list
    uid_list = get_aeromap_uid_list(tixi)
    aeromap_uid = uid_list[0]
    # Import aeromap from the CSV to the xml
    aeromap_from_csv( tixi, aeromap_uid, csv_path)
    # Save the xml file
    close_tixi(tixi, cpacs_out_path)
#End part for tests


    # Make the static stability analysis, on the modified xml file
    staticStabilityAnalysis(cpacs_path, aeromap_uid)


    log.info('----- End of ' + os.path.basename(__file__) + ' -----')
