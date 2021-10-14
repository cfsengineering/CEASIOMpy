"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

dynamic stability module

Python version: >=3.6

| Author: Verdier Loïc
| Creation: 2019-10-24
| Last modifiction: 2021-10-14 (AJ)

TODO:
    * Modify the code where there are "TODO"
    * If only one aos angle -> dirrectionaly_stable  ???     - LV : Laterl and directional static stability can not be tested
    * If only one aos angle -> longitudinaly_stable  ???    - LV : If only one aos and aos == 0: Longitudinal Static stability can be tested.
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
from numpy import log as ln
from numpy import linalg # For eigen values and aigen voectors

import matplotlib as mpl, cycler
import matplotlib.patheffects
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Patch

from scipy import signal # For transfert function

from cpacspy.cpacsfunctions import (create_branch, get_string_vector,
                                    get_value, get_value_or_default, 
                                    open_tixi)

import ceasiompy.utils.apmfunctions as apmf
import ceasiompy.utils.moduleinterfaces as mi

from ceasiompy.StabilityDynamic.func_dynamic import plot_sp_level_a, plot_sp_level_b, plot_sp_level_c,\
                                            get_unic, interpolation, get_index,  trim_derivative,\
                                            speed_derivative_at_trim, adimensionalise,\
                                            speed_derivative_at_trim_lat, concise_derivative_longi, concise_derivative_lat,\
                                            longi_root_identification, direc_root_identification,\
                                            check_sign_longi, check_sign_lat,\
                                            short_period_damping_rating, short_period_frequency_rating, cap_rating, \
                                            phugoid_rating, roll_rating, spiral_rating, dutch_roll_rating, plot_splane,\
                                            longi_mode_characteristic, direc_mode_characteristic, trim_condition

from ceasiompy.utils.standardatmosphere import get_atmosphere, plot_atmosphere
from ceasiompy.SkinFriction.skinfriction import get_largest_wing_dim
from ceasiompy.utils.ceasiomlogger import get_logger

log = get_logger(__file__.split('.')[0])

MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
MODULE_NAME = os.path.basename(os.getcwd())

DYNAMIC_ANALYSIS_XPATH = '/cpacs/toolspecific/CEASIOMpy/stability/dynamic'

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

    Returns:  (#TODO put that in the documentation)
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

    Make the following tests:
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

    # XPATH definition
    aeromap_uid_xpath =   DYNAMIC_ANALYSIS_XPATH + '/aeroMapUid'
    aircraft_class_xpath = DYNAMIC_ANALYSIS_XPATH + '/class' # Classes 1 2 3 4 small, heavy ...
    aircraft_cathegory_xpath = DYNAMIC_ANALYSIS_XPATH  + '/category' # flight phase A B C
    selected_mass_config_xpath  = DYNAMIC_ANALYSIS_XPATH + '/massConfiguration'
    longi_analysis_xpath = DYNAMIC_ANALYSIS_XPATH + '/instabilityModes/longitudinal'
    direc_analysis_xpath = DYNAMIC_ANALYSIS_XPATH + '/instabilityModes/lateralDirectional'
    show_plot_xpath = DYNAMIC_ANALYSIS_XPATH + '/showPlots'
    save_plot_xpath =  DYNAMIC_ANALYSIS_XPATH + '/savePlots'

    model_xpath = '/cpacs/vehicles/aircraft/model'
    ref_area_xpath = model_xpath + '/reference/area'
    ref_length_xpath = model_xpath + '/reference/length'
    flight_qualities_case_xpath = model_xpath + '/analyses/flyingQualities/fqCase'
    masses_location_xpath =  model_xpath + '/analyses/massBreakdown/designMasses'
    # aircraft_class_xpath = flight_qualities_case_xpath + '/class' # Classes 1 2 3 4 small, heavy ...
    # aircraft_cathegory_xpath = flight_qualities_case_xpath + '/cathegory' # flight phase A B C

    # Ask user flight path angles : gamma_e
    thrust_available = None # Thrust data are not available
    flight_path_angle_deg = [0] # [-15,-10,-5,0,5,10,15] # The user should have the choice to select them !!!!!!!!!!!!!!!!!!!!
    flight_path_angle = [angle *(np.pi/180) for angle  in flight_path_angle_deg]  # flight_path_angle in [rad]

    tixi = open_tixi(cpacs_path)
    # Get aeromap uid
    aeromap_uid = get_value(tixi, aeromap_uid_xpath )
    log.info('The following aeroMap will be analysed: ' + aeromap_uid)

    # Mass configuration: (Maximum landing mass, Maximum ramp mass (the maximum weight authorised for the ground handling), Take off mass, Zero Fuel mass)
    mass_config = get_value(tixi, selected_mass_config_xpath)
    log.info('The aircraft mass configuration used for analysis is: ' + mass_config)

    # Analyses to do : longitudinal / Lateral-Directional
    longitudinal_analysis = get_value(tixi,longi_analysis_xpath)
    lateral_directional_analysis = False
    # lateral_directional_analysis = get_value(tixi, direc_analysis_xpath )
    # Plots configuration with Setting GUI
    show_plots = get_value_or_default(tixi,show_plot_xpath,False)
    save_plots = get_value_or_default(tixi,save_plot_xpath,False)

    mass_config_xpath = masses_location_xpath + '/' + mass_config
    if tixi.checkElement(mass_config_xpath):
        mass_xpath = mass_config_xpath + '/mass'
        I_xx_xpath  = mass_config_xpath + '/massInertia/Jxx'
        I_yy_xpath  = mass_config_xpath + '/massInertia/Jyy'
        I_zz_xpath = mass_config_xpath + '/massInertia/Jzz'
        I_xz_xpath = mass_config_xpath + '/massInertia/Jxz'
    else :
        raise ValueError('The mass configuration : {} is not defined in the CPACS file !!!'.format(mass_config))

    s = get_value(tixi,ref_area_xpath)     # Wing area : s  for non-dimonsionalisation of aero data.
    mac = get_value(tixi,ref_length_xpath) # ref length for non dimensionalisation, Mean aerodynamic chord: mac,
    # TODO: check that
    b= s/mac

    # TODO: find a way to get that
    xh = 10 # distance Aircaft cg-ac_horizontal-tail-plane.

    m = get_value(tixi,mass_xpath) # aircraft mass dimensional
    I_xx = get_value(tixi,I_xx_xpath) # X inertia dimensional
    I_yy = get_value(tixi,I_yy_xpath) # Y inertia dimensional
    I_zz = get_value(tixi,I_zz_xpath) # Z inertia dimensional
    I_xz = get_value(tixi,I_xz_xpath) # XZ inertia dimensional

    aircraft_class = get_value(tixi,aircraft_class_xpath ) # aircraft class 1 2 3 4
    flight_phase = get_string_vector(tixi, aircraft_cathegory_xpath)[0] # Flight phase A B C

    Coeffs = apmf.get_aeromap(tixi,aeromap_uid)    # Warning: Empty uID found! This might lead to unknown errors!

    alt_list = Coeffs.alt
    mach_list = Coeffs.mach
    aoa_list = Coeffs.aoa
    aos_list = Coeffs.aos
    cl_list = Coeffs.cl
    cd_list = Coeffs.cd
    cs_list = Coeffs.cs
    cml_list = Coeffs.cml
    cms_list = Coeffs.cms
    cmd_list = Coeffs.cmd
    dcsdrstar_list = Coeffs.dcsdrstar
    dcsdpstar_list = Coeffs.dcsdpstar
    dcldqstar_list = Coeffs.dcldqstar
    dcmsdqstar_list = Coeffs.dcmsdqstar
    dcddqstar_list = Coeffs.dcddqstar
    dcmldqstar_list = Coeffs.dcmldqstar
    dcmddpstar_list = Coeffs.dcmddpstar
    dcmldpstar_list = Coeffs.dcmldpstar
    dcmldrstar_list = Coeffs.dcmldrstar
    dcmddrstar_list = Coeffs.dcmddrstar


    # All different vallues with only one occurence
    alt_unic = get_unic(alt_list)
    mach_unic = get_unic(mach_list)
    aos_unic = get_unic(aos_list)
    aoa_unic = get_unic(aoa_list)

    # TODO get from CPACS
    incrementalMap = False

    for alt in alt_unic:
        idx_alt = [i for i in range(len(alt_list)) if alt_list[i] == alt]
        Atm = get_atmosphere(alt)
        g = Atm.grav
        a = Atm.sos
        rho = Atm.dens

        for mach in mach_unic:
            print('Mach : ' , mach)
            idx_mach = [i for i in range(len(mach_list)) if mach_list[i] == mach]
            u0,m_adim,i_xx,i_yy,i_zz,i_xz = adimensionalise(a,mach,rho,s,b,mac,m,I_xx,I_yy,I_zz,I_xz) # u0 is V0 in Cook

            # Hyp: trim condition when: ( beta = 0 and dCm/dalpha = 0)  OR  ( aos=0 and dcms/daoa = 0 )
            if 0 not in aos_unic :
                log.warning('The aircraft can not be trimmed (requiring symetric flight condition) as beta never equal to 0 for Alt = {}, mach = {}'.format(alt,mach))
            else:
                idx_aos = [i for i in range(len(aos_list)) if aos_list[i] == 0]
                find_index = get_index(idx_alt, idx_mach, idx_aos)
                # If there is only one data at (alt, mach, aos) then dont make stability anlysis
                if len(find_index) <= 1:
                    log.warning('Not enough data at : Alt = {} , mach = {}, aos = 0, can not perform stability analysis'.format(alt,mach))
                # If there is at leat 2 data at (alt, mach, aos) then, make stability anlysis
                else:
                    # Calculate trim conditions
                    cms = []
                    aoa = []
                    cl = []
                    for index in find_index:
                        cms.append(cms_list[index])
                        aoa.append(aoa_list[index]*np.pi/180)
                        cl.append(cl_list[index])

                    cl_required = (m*g)/(0.5*rho*u0**2*s)
                    (trim_aoa , idx_trim_before, idx_trim_after, ratio) = trim_condition(alt, mach, cl_required, cl, aoa,)

                    if trim_aoa:
                        trim_aoa_deg = trim_aoa *180/np.pi
                        trim_cms = interpolation(cms, idx_trim_before, idx_trim_after, ratio)
                        pitch_moment_derivative_rad = (cms[idx_trim_after] - cms[idx_trim_before]) / (aoa[idx_trim_after] - aoa[idx_trim_before])
                        pitch_moment_derivative_deg = pitch_moment_derivative_rad / (180/np.pi)
                        # Find incremental cms
                        if incrementalMap :
                            for index, mach_number in enumerate(mach_unic,0):
                                if mach_number == mach :
                                    mach_index = index
                            dcms_before = dcms_list[ mach_index*len(aoa_unic) + idx_trim_before]
                            dcms_after = dcms_list[ mach_index*len(aoa_unic) + idx_trim_after]
                            dcms = dcms_before + ratio*(dcms_after - dcms_before)
                            trim_elevator = - trim_cms / dcms # Trim elevator deflection in [°]
                        else:
                            dcms  = None
                            trim_elevator =  None

                    else:
                        trim_aoa_deg = None
                        trim_cms = None
                        pitch_moment_derivative_deg = None
                        dcms = None
                        trim_elevator =  None


                    # Longitudinal dynamic stability,
                    # Stability analysis
                    if longitudinal_analysis and trim_cms:
                        cl = []
                        cd = []
                        dcldqstar = []
                        dcddqstar = []
                        dcmsdqstar = []
                        for index in find_index:
                            cl.append(cl_list[index])
                            cd.append(cd_list[index])
                            dcldqstar.append(dcldqstar_list[index])
                            dcddqstar.append(dcddqstar_list[index])
                            dcmsdqstar.append(dcmsdqstar_list[index])

                        # Trimm variables
                        cd0 =interpolation(cd, idx_trim_before, idx_trim_after, ratio) # Dragg coeff at trim
                        cl0 =interpolation(cl, idx_trim_before, idx_trim_after, ratio)   # Lift coeff at trim
                        cl_dividedby_cd_trim = cl0/cd0  #  cl/cd ratio at trim, at trim aoa

                        # Lift & drag coefficient derivative with respect to AOA at trimm
                        cl_alpha0 = (cl[idx_trim_after] - cl[idx_trim_before]) / (aoa[idx_trim_after] - aoa[idx_trim_before])
                        cd_alpha0 = (cd[idx_trim_after] - cd[idx_trim_before]) / (aoa[idx_trim_after] - aoa[idx_trim_before])
                        print(idx_trim_before, idx_trim_after, ratio)

                        dcddqstar0 = interpolation(dcddqstar, idx_trim_before, idx_trim_after, ratio) # x_q
                        dcldqstar0 = interpolation(dcldqstar, idx_trim_before, idx_trim_after, ratio) # z_q
                        dcmsdqstar0 = interpolation(dcmsdqstar, idx_trim_before, idx_trim_after, ratio) # m_q
                        cm_alpha0 = trim_cms

                        # Speed derivatives if there is at least 2 distinct mach values
                        if len(mach_unic) >=2 :
                            dcddm0 =speed_derivative_at_trim(cd_list, mach, mach_list, mach_unic, idx_alt, aoa_list, aos_list, idx_trim_before, idx_trim_after, ratio)

                            if dcddm0 == None :
                                dcddm0 = 0
                                log.warning('Not enough data to determine dcddm or (Cd_mach) at trim condition at Alt = {}, mach = {}, aoa = {}, aos = 0. Assumption: dcddm = 0'.format(alt,mach,round(trim_aoa_deg,2)))
                            dcldm0 =speed_derivative_at_trim (cl_list, mach, mach_list, mach_unic, idx_alt, aoa_list, aos_list, idx_trim_before, idx_trim_after, ratio)
                            if dcldm0 == None :
                                dcldm0 = 0
                                log.warning('Not enough data to determine dcldm (Cl_mach) at trim condition at Alt = {}, mach = {}, aoa = {}, aos = 0. Assumption: dcldm = 0'.format(alt,mach,round(trim_aoa_deg,2)))
                        else :
                            dcddm0 = 0
                            dcldm0 = 0
                            log.warning('Not enough data to determine dcddm (Cd_mach) and dcldm (Cl_mach) at trim condition at Alt = {}, mach = {}, aoa = {}, aos = 0. Assumption: dcddm = dcldm = 0'.format(alt,mach,round(trim_aoa_deg,2)))

                        # Controls Derivatives to be found in the CPACS (To be calculated)
                        dcddeta0 = 0
                        dcldeta0 = 0
                        dcmsdeta0 = 0
                        dcddtau0 = 0
                        dcldtau0 = 0
                        dcmsdtau0 = 0

                        # Traduction Ceasiom -> Theory
                        Ue = u0*np.cos(trim_aoa)    # *np.cos(aos) as aos = 0 at trim, cos(aos)=1
                        We = u0*np.sin(trim_aoa)    # *np.cos(aos) as aos = 0 at trim, cos(aos)=1

                        # Dimentionless State Space variables,
                        # In generalised body axes coordinates ,
                        # simplifications: Ue=V0, We=0, sin(Theta_e)=0 cos(Theta_e)=0
                        if thrust_available:    #   If power data
                            X_u = -(2*cd0 + mach*dcddm0) + 1/(0.5*rho*s*a^2) * dtaudm0  # dtaudm dimensional Thrust derivative at trim conditions, P340 Michael V. Cook
                        else:     #   Glider Mode
                            X_u = -(2*cd0 + mach*dcddm0)

                        Z_u = -(2*cl0 + mach*dcldm0)
                        M_u = 0 # Negligible for subsonic conditions  or better with P289 Yechout (cm_u+2cm0)

                        X_w = (cl0 - cd_alpha0 )
                        Z_w = -(cl_alpha0 + cd0)
                        M_w = cm_alpha0

                        X_q =   dcddqstar0 # Normally almost = 0
                        Z_q =  dcldqstar0
                        M_q = - dcmsdqstar0

                        X_dotw = 0 # Negligible
                        Z_dotw = 1/3 * M_q/u0 / (xh/mac) # Thumb rule : M_alpha_dot = 1/3 Mq , ( not true for 747 :caughey P83,M_alpha_dot = 1/6Mq )
                        M_dotw = 1/3 * M_q /u0 # Thumb rule : M_alpha_dot = 1/3 Mq

                        # Controls:
                        X_eta = dcddeta0 # To be found from the cpacs file, and defined by the user!
                        Z_eta = dcldeta0 # To be found from the cpacs file, and defined by the user!
                        M_eta = dcmsdeta0 # To be found from the cpacs file, and defined by the user!

                        X_tau = dcddtau0 # To be found from the cpacs file, and defined by the user!
                        Z_tau = dcldtau0 # To be found from the cpacs file, and defined by the user!
                        M_tau = dcmsdtau0  # To be found from the cpacs file, and defined by the user!
                        # -----------------  Traduction Ceasiom -> Theory   END -----------------------------------

                        # Sign check  (Ref: Thomas Yechout Book, P304)
                        check_sign_longi(cd_alpha0,M_w,cl_alpha0,M_dotw,Z_dotw,M_q,Z_q,M_eta,Z_eta)

                    # Laterl-Directional
                    if lateral_directional_analysis:
                        cml = [] # N
                        cmd = [] # L
                        aos = []
                        aoa = [] # For Ue We
                        cs = [] # For y_v
                        dcsdpstar = [] # y_p
                        dcmddpstar = []  # l_p
                        dcmldpstar = []  # n_p
                        dcsdrstar = [] # y_r
                        dcmldrstar = []  # n_r
                        dcmddrstar = []  # l_r

                        for index in find_index:
                            cml.append(cml_list[index]) # N , N_v
                            cmd.append(cmd_list[index]) # L ,  L_v
                            aos.append(aos_list[index]*np.pi/180)
                            aoa.append(aoa_list[index]) # For Ue We
                            cs.append(cs_list[index])
                            dcsdpstar.append(dcsdpstar_list[index]) # y_p
                            dcmddpstar.append(dcmddpstar_list[index]) # l_p
                            dcmldpstar.append(dcmldpstar_list[index]) # n_p
                            dcsdrstar.append(dcsdrstar_list[index]) # y_r
                            dcmldrstar.append(dcmldrstar_list[index]) # n_r
                            dcmddrstar.append(dcmddrstar_list[index]) # l_r

                        #Trimm condition calculation
                        # speed derivatives :  y_v / l_v / n_v  /  Must be devided by speed given that the hyp v=Beta*U
                        if len(aos_unic) >=2 :
                            print('Mach : ', mach, '   and idx_mach : ', idx_mach)
                            cs_beta0 = speed_derivative_at_trim_lat(cs_list , aos_list, aos_unic, idx_alt, idx_mach, aoa_list, idx_trim_before, idx_trim_after, ratio)# y_v
                            if cs_beta0 == None :
                                cs_beta0 = 0
                                log.warning('Not enough data to determine cs_beta (Y_v) at trim condition at Alt = {}, mach = {}, aoa = {}, aos = 0. Assumption: cs_beta = 0'.format(alt,mach,round(trim_aoa_deg,2)))
                            cmd_beta0  = speed_derivative_at_trim_lat(cmd_list , aos_list, aos_unic, idx_alt, idx_mach, aoa_list, idx_trim_before, idx_trim_after, ratio)# l_v
                            if cmd_beta0 ==None :
                                cmd_beta0 = 0
                                log.warning('Not enough data to determine cmd_beta (L_v) at trim condition at Alt = {}, mach = {}, aoa = {}, aos = 0. Assumption: cmd_beta = 0'.format(alt,mach,round(trim_aoa_deg,2)))
                            cml_beta0 = speed_derivative_at_trim_lat(cml_list , aos_list, aos_unic, idx_alt, idx_mach, aoa_list, idx_trim_before, idx_trim_after, ratio)# n_v
                            if cml_beta0 == None :
                                cml_beta0 = 0
                                log.warning('Not enough data to determine cml_beta (N_v) at trim condition at Alt = {}, mach = {}, aoa = {}, aos = 0. Assumption: cml_beta = 0'.format(alt,mach,round(trim_aoa_deg,2)))
                        else :
                            cs_beta0 = 0
                            cmd_beta0 = 0
                            cml_beta0 = 0
                            log.warning('Not enough data to determine cs_beta (Y_v), cmd_beta (L_v) and cml_beta (N_v) at trim condition at Alt = {}, mach = {}, aoa = {}, aos = 0. Assumption: cs_beta = cmd_beta = cml_beta = 0'.format(alt,mach,round(trim_aoa_deg,2)))

                        dcsdpstar0 = interpolation(dcsdpstar, idx_trim_before, idx_trim_after, ratio) # y_p
                        dcmddpstar0  = interpolation(dcmddpstar, idx_trim_before, idx_trim_after, ratio) # l_p
                        dcmldpstar0 = interpolation(dcmldpstar, idx_trim_before, idx_trim_after, ratio) # n_p

                        dcsdrstar0 =interpolation(dcsdrstar, idx_trim_before, idx_trim_after, ratio) # y_r
                        dcmldrstar0 =  interpolation(dcmldrstar, idx_trim_before, idx_trim_after, ratio) # n_r
                        dcmddrstar0 =  interpolation(dcmddrstar, idx_trim_before, idx_trim_after, ratio) # l_r

                        # TODO: calculate that and find in the cpacs
                        dcsdxi0 = 0
                        dcmddxi0 = 0
                        dcmldxi0 = 0
                        dcsdzeta0 = 0
                        dcmddzeta0 = 0
                        dcmldzeta0 = 0


                        # Traduction Ceasiom -> Theory
                        Y_v = cs_beta0
                        L_v = cmd_beta0
                        N_v = cml_beta0

                        Y_p = -dcsdpstar0*mac/b
                        L_p = -dcmddpstar0*mac/b
                        N_p = dcmldpstar0*mac/b

                        Y_r = dcsdrstar0*mac/b
                        N_r = -dcmldrstar0*mac/b # mac/b :Because coefficients in ceasiom are nondimensionalised by the mac instead of the span
                        L_r = dcmddrstar0*mac/b

                        # Controls:
                        # Ailerons
                        Y_xi = dcsdxi0 # To be found from the cpacs file, and defined by the user!
                        L_xi = dcmddxi0 # To be found from the cpacs file, and defined by the user!
                        N_xi = dcmldxi0 # To be found from the cpacs file, and defined by the user!
                        # Rudder
                        Y_zeta = dcsdzeta0 # To be found from the cpacs file, and defined by the user!
                        L_zeta = dcmddzeta0 # To be found from the cpacs file, and defined by the user!
                        N_zeta = dcmldzeta0 # To be found from the cpacs file, and defined by the user!

                        Ue = u0*np.cos(trim_aoa) # *np.cos(aos) as aos = 0 at trim, cos(aos)=1
                        We = u0*np.sin(trim_aoa) # *np.cos(aos) as aos = 0 at trim, cos(aos)=1

                        # Sign check  (Ref: Thomas Yechout Book, P304)
                        check_sign_lat(Y_v,L_v,N_v,Y_p,L_p,Y_r,L_r,N_r,L_xi,Y_zeta,L_zeta,N_zeta)

                    if trim_aoa :
                        for angles in flight_path_angle:
                            theta_e =  angles + trim_aoa

                            if longitudinal_analysis :
                                (A_longi, B_longi, x_u,z_u,m_u,x_w,z_w,m_w, x_q,z_q,m_q,x_theta,z_theta,m_theta,x_eta,z_eta,m_eta, x_tau,z_tau,m_tau)\
                                                                    = concise_derivative_longi(X_u,Z_u,M_u,X_w,Z_w,M_w,\
                                                                    X_q,Z_q,M_q,X_dotw,Z_dotw,M_dotw,X_eta,Z_eta,M_eta,\
                                                                    X_tau,Z_tau,M_tau, g, theta_e, u0,We,Ue,mac,m_adim,i_yy)

                                C_longi = np.identity(4)
                                D_longi = np.zeros((4,2))
                                # Identify longitudinal roots
                                if  longi_root_identification(A_longi)[0] == None : # If longitudinal root not complex conjugate raise warning and plot roots
                                    eg_value_longi = longi_root_identification(A_longi)[1]
                                    log.warning('Longi : charcateristic equation  roots are not complex conjugate : {}'.format(eg_value_longi))
                                    legend = ['Root1', 'Root2', 'Root3', 'Root4']
                                    plot_title = 'S-plane longitudinal characteristic equation roots at (Alt = {}, Mach= {}, trimed at aoa = {}°)'.format(alt,mach,trim_aoa)
                                    plot_splane(eg_value_longi, plot_title,legend,show_plots,save_plots)
                                else:                                                                                     # Longitudinal roots are complex conjugate
                                    (sp1, sp2, ph1, ph2, eg_value_longi , eg_vector_longi, eg_vector_longi_magnitude)\
                                            = longi_root_identification(A_longi)
                                    legend = ['sp1', 'sp2', 'ph1', 'ph2']
                                    plot_title = 'S-plane longitudinal characteristic equation roots at (Alt = {}, Mach= {}, trimed at aoa = {}°)'.format(alt,mach,trim_aoa)
                                    plot_splane(eg_value_longi, plot_title,legend,show_plots,save_plots)

                                    # Modes parameters : damping ratio, frequence, CAP, time tou double amplitude
                                    Z_w_dimensional = Z_w*(0.5*rho*s*u0**2)   # Z_w* (0.5*rho*s*u0**2)  is the dimensional form of Z_w,   Z_w = -(cl_alpha0 + cd0) P312 Yechout
                                    z_alpha =  Z_w_dimensional * u0  /m # alpha = w/u0 hence,   z_alpha =  Z_w_dimensional * u0      [Newton/rad/Kg :   m/s^2 /rad]
                                    load_factor = - z_alpha/g #  number of g's/rad (1g/rad 2g/rad  3g/rad)
                                    (sp_freq, sp_damp, sp_cap, ph_freq, ph_damp, ph_t2)\
                                            =  longi_mode_characteristic(sp1,sp2,ph1,ph2,load_factor)

                                    # Rating
                                    sp_damp_rate = short_period_damping_rating(aircraft_class,sp_damp)
                                    sp_freq_rate = short_period_frequency_rating(flight_phase,aircraft_class,sp_freq, load_factor)
                                    # Plot SP freq vs Load factor
                                    legend = 'Alt = {}, Mach= {}, trim aoa = {}°'.format(alt,mach,trim_aoa)
                                    if flight_phase == 'A' :
                                        plot_sp_level_a([load_factor], [sp_freq], legend, show_plots,save_plots)
                                    elif flight_phase == 'B' :
                                        plot_sp_level_b(x_axis, y_axis, legend, show_plots,save_plots)
                                    else:
                                        plot_sp_level_c(x_axis, y_axis, legend, show_plots,save_plots)
                                    sp_cap_rate = cap_rating(flight_phase, sp_cap, sp_damp)
                                    ph_rate = phugoid_rating(ph_damp, ph_t2)
                                    # Raise warning if unstable mode in the log file
                                    if sp_damp_rate == None :
                                        log.warning('ShortPeriod UNstable at Alt = {}, Mach = {} , due to DampRatio = {} '.format(alt,mach,round(sp_damp, 4)))
                                    if sp_freq_rate == None :
                                        log.warning('ShortPeriod UNstable at Alt = {}, Mach = {} , due to UnDampedFreq = {} rad/s '.format(alt,mach,round(sp_freq, 4)))
                                    if sp_cap_rate == None :
                                        log.warning('ShortPeriod UNstable at Alt = {}, Mach = {} , with CAP evaluation, DampRatio = {} , CAP = {} '.format(alt,mach,round(sp_damp, 4),round(sp_cap, 4)))
                                    if ph_rate == None :
                                        log.warning('Phugoid UNstable at Alt = {}, Mach = {} , DampRatio = {} , UnDampedFreq = {} rad/s'.format(alt,mach,round(ph_damp, 4),round(ph_freq, 4)))

                                    # TODO
                                    # Compute numerator TF for (Alt, mach, flight_path_angle, aoa_trim, aos=0

                            if lateral_directional_analysis:
                                (A_direc, B_direc,y_v,l_v,n_v,y_p,y_phi,y_psi,l_p,l_phi,l_psi,n_p,y_r,l_r,n_r,n_phi,n_psi, y_xi,l_xi,n_xi, y_zeta,l_zeta,n_zeta)\
                                    = concise_derivative_lat(Y_v,L_v,N_v,Y_p,L_p,N_p,Y_r,L_r,N_r,\
                                                                            Y_xi,L_xi,N_xi, Y_zeta,L_zeta,N_zeta,\
                                                                            g, b, theta_e, u0,We,Ue,m_adim,i_xx,i_zz,i_xz )

                                C_direc = np.identity(5)
                                D_direc = np.zeros((5,2))

                                if  direc_root_identification(A_direc)[0] == None: # Lateral-directional roots are correctly identified
                                    eg_value_direc = direc_root_identification(A_direc)[1]
                                    print('Lat-Dir : charcateristic equation  roots are not complex conjugate : {}'.format(eg_value_direc))
                                    legend = ['Root1', 'Root2', 'Root3', 'Root4']
                                    plot_title = 'S-plane lateral characteristic equation roots at (Alt = {}, Mach= {}, trimed at aoa = {}°)'.format(alt,mach,trim_aoa)
                                    plot_splane(eg_value_direc, plot_title,legend,show_plots,save_plots)
                                else:                                                                                     # Lateral-directional roots are correctly identified
                                    (roll, spiral, dr1, dr2, eg_value_direc, eg_vector_direc, eg_vector_direc_magnitude)\
                                        = direc_root_identification(A_direc)
                                    legend = ['roll', 'spiral', 'dr1', 'dr2']
                                    plot_title = 'S-plane lateralcharacteristic equation roots at (Alt = {}, Mach= {}, trimed at aoa = {}°)'.format(alt,mach,trim_aoa)
                                    plot_splane(eg_value_direc, plot_title,legend,show_plots,save_plots)
                                    (roll_timecst, spiral_timecst, spiral_t2, dr_freq, dr_damp, dr_damp_freq) = direc_mode_characteristic(roll,spiral,dr1,dr2)

                                    # Rating
                                    roll_rate = roll_rating(flight_phase, aircraft_class, roll_timecst)
                                    spiral_rate = spiral_rating(flight_phase, spiral_timecst, spiral_t2)
                                    dr_rate = dutch_roll_rating(flight_phase, aircraft_class, dr_damp, dr_freq, dr_damp_freq)

                                    # Raise warning in the log file if unstable mode
                                    if roll_rate == None :
                                        log.warning('Roll mode UNstable at Alt = {}, Mach = {} , due to roll root = {}, roll time contatant = {} s'.format(alt,mach,round(roll_root, 4), round(roll_timecst, 4)))
                                    if spiral_rate == None :
                                        log.warning('Spiral mode UNstable at Alt = {}, Mach = {} , spiral root = {}, time_double_ampl = {}'.format(alt,mach,round(spiral_root, 4), round(spiral_t2, 4)))
                                    if dr_rate == None :
                                        log.warning('Dutch Roll UNstable at Alt = {}, Mach = {} , Damping Ratio = {} , frequency = {} rad/s '.format(alt,mach,round(dr_damp, 4),round(dr_freq, 4)))


                        # TODO: Save those value if code works
                        # Save Parameters for the flight conditions

                        # # xpath definition
                        # flight_case_uid = 'alt= mach= aoa= flightPathAngle'
                        # flight_case_xpath = model_xpath + '/analyses/flightDynamics/flightCases/flightCase'
                        # flight_case_uid_xpath = flight_case_xpath + '/flightCaseUID'
                        # trim_result_xpath = flight_case_uid_xpath + '/trimResult'
                        # linear_model_xpath = flight_case_uid_xpath + '/linearModel'
                        #
                        # flying_qality_uid_xpath = model_xpath + '/analyses/flyingQualities/fqCase'
                        # tf_longi_xpath = flying_qality_uid_xpath +'/longitudinal'    # TF longi path
                        # tf_lat_xpath = flying_qality_uid_xpath + '/lateral'                 # TF lateral path
                        # parameters_xpath = flying_qality_uid_xpath + '/charParameters' # stability parameters dmaping etc..
                        # ratings_xpath = flying_qality_uid_xpath + '/ratings'
                        #
                        # # Flight case branche and UID
                        # create_branch(tixi, flight_case_uid_xpath )
                        # tixi.updateTextElement(flight_case_uid_xpath, flight_case_uid )
                        # # Save trim results  (alt, mach, aoa_trim)
                        # create_branch(tixi,trim_result_xpath)
                        # tixi.updateDoubleElement(trim_result_xpath + '/altitude', mach, '%g')
                        # tixi.updateDoubleElement(trim_result_xpath + '/mach', mach, '%g')
                        # tixi.updateDoubleElement(trim_result_xpath + '/alpha', mach, '%g')
                        # # Save linerarisation matrixes
                        # create_branch(tixi,linear_model_xpath )
                        # tixi.addFloatVector(linear_model_xpath + '/aLon', A_longi, '%g')  # SHould be an arrayy!!!!!!
                        # tixi.addFloatVector(linear_model_xpath + '/bLon', B_longi, '%g')
                        # tixi.addFloatVector(linear_model_xpath + '/cLon', C_longi, '%g')
                        # tixi.addFloatVector(linear_model_xpath + '/dLon', D_longi, '%g')
                        # tixi.addFloatVector(linear_model_xpath + '/aLat', A_direc, '%g')
                        # tixi.addFloatVector(linear_model_xpath + '/bLat', B_direc, '%g')
                        # tixi.addFloatVector(linear_model_xpath + '/cLat', C_direc, '%g')
                        # tixi.addFloatVector(linear_model_xpath + '/dLat', D_direc, '%g')
                        # # Flying qualities branche and UID
                        # create_branch(tixi, flying_qality_uid_xpath  )
                        # tixi.updateTextElement(flying_qality_uid_xpath , flight_case_uid ) # Set UID
                        # tixi.updateIntegerElement(flying_qality_uid_xpath + '/class', aircraft_class, '%i') # Aircraft calss : 1 2 3
                        # tixi.updateTextElement(flying_qality_uid_xpath + '/category', flight_phase) # Aircraft calss : A B C
                        # # TF longi
                        # create_branch(tixi, tf_longi_xpath )
                        # tixi.addFloatVector(tf_longi_xpath+'/denLon', delta_longi, '%g') # DEN Longi TF
                        # # TF lateral
                        # create_branch(tixi, tf_lat_xpath )
                        # tixi.addFloatVector(tf_lat_xpath+'/denLat', delta_direc, '%g') # DEN Lateral-direction TF
                        # # Parameters
                        # create_branch(tixi, parameters_xpath)
                        # tixi.updateDoubleElement(parameters_xpath + '/shortPeriod/nAlpha', load_factor, '%g') # Short period load factor
                        # tixi.updateDoubleElement(parameters_xpath + '/shortPeriod/spFrequency', sp_freq, '%g') # Short period frequency
                        # tixi.updateDoubleElement(parameters_xpath + '/shortPeriod/spDamping', sp_damp, '%g') # Short period dmaping
                        # tixi.updateDoubleElement(parameters_xpath + '/shortPeriod/cap', sp_cap, '%g')               # Short period CAP
                        # tixi.updateDoubleElement(parameters_xpath + '/phugoid/phDamping', ph_damp, '%g')    # Phugoid Damping
                        # tixi.updateDoubleElement(parameters_xpath + '/phugoid/phDoublingTime', ph_t2, '%g') #Phugoid Time to double amplitudes
                        # tixi.updateTextElement(parameters_xpath + '/rollSpiral', 'normal') # No coupling between roll and spiral mode
                        # tixi.updateDoubleElement(parameters_xpath + '/eiglat/dutchRollFrequency', dr_freq, '%g')
                        # tixi.updateDoubleElement(parameters_xpath + '/eiglat/dutchRollDamping', dr_damp, '%g')
                        # tixi.updateDoubleElement(parameters_xpath + '/eiglat/rollTimeConstant', roll_timecst, '%g')
                        # tixi.updateDoubleElement(parameters_xpath + '/eiglat/spiralDoublingTime', spiral_t2, '%g')
                        # # Parameters' rate
                        # create_branch(tixi, ratings_xpath)
                        # tixi.updateIntegerElement(ratings_xpath + '/shortPeriod/spFrequency', sp_freq_rate, '%i') # Short period frequency
                        # tixi.updateIntegerElement(ratings_xpath + '/shortPeriod/spDamping', sp_damp_rate, '%i') # Short period dmaping
                        # tixi.updateIntegerElement(ratings_xpath + '/shortPeriod/cap', sp_cap_rate, '%i')               # Short period CAP
                        # tixi.updateIntegerElement(ratings_xpath + '/phugoid/phDamping', ph_rate, '%i')    # Phugoid Damping
                        # tixi.updateIntegerElement(ratings_xpath + '/phugoid/phDoublingTime', ph_rate, '%i') #Phugoid Time to double amplitudes
                        # tixi.updateTextElement(ratings_xpath + '/rollSpiral', 'normal') # No coubling between roll and spiral mode
                        # tixi.updateIntegerElement(ratings_xpath + '/eiglat/dutchRollFrequency', dr_rate, '%i')
                        # tixi.updateIntegerElement(ratings_xpath + '/eiglat/dutchRollDamping', dr_rate, '%i')
                        # tixi.updateIntegerElement(ratings_xpath + '/eiglat/rollTimeConstant', roll_rate, '%i')
                        # tixi.updateIntegerElement(ratings_xpath + '/eiglat/spiralDoublingTime', spiral_rate, '%i')

                        # TODO : compute TF polynoms from Cook  (P 423 424) and save them using the following x_path
                        # # Xpath of longitudinal transfter function polynoms
                        # num_tf_elev_theta_xpath = flight_qualities_case_xpath + '/longitudinal/numThe'# numerator of TF pitch angle theta due to elevator deflection
                        # den_tf_longi_xpath = flight_qualities_case_xpath + '/longitudinal/denLon' # denominator of longitudinal motion
                        # # Xpath of lateral-directional transfter function polynoms of 5th order system
                        # num_tf_ail_phi_xpath = flight_qualities_case_xpath +'lateral/numPhiDas'  # numerator of TF of aileron impact to  bank angle, roll angle phi
                        # num_tf_ail_r_xpath = flight_qualities_case_xpath +'lateral/numRDas'  # numerator of TF of aileron impact to  yaw rate : r
                        # num_tf_ail_beta_xpath = flight_qualities_case_xpath +'lateral/numBetaDas'  # numerator of TF of aileron impact to sideslip angle : beta
                        # num_tf_rud_r_xpath = flight_qualities_case_xpath +'lateral/numRDrp'  # numerator of TF of rudder impact to yaw rate : r
                        # num_tf_rud_beta_xpath = flight_qualities_case_xpath +'lateral/numBetaDrp'  # numerator of TF of rudder impact to sideslip angle : beta
                        # den_tf_latdir_xpath = flight_qualities_case_xpath + '/lateral/denLat' # denominator of longitudinal motion


if __name__ == '__main__':

    log.info('----- Start of ' + MODULE_NAME + ' -----')

    cpacs_path = mi.get_toolinput_file_path(MODULE_NAME)
    cpacs_out_path = mi.get_tooloutput_file_path(MODULE_NAME)

    # Call the function which check if imputs are well define
    mi.check_cpacs_input_requirements(cpacs_path)

    # Call the main function for static stability analysis
    dynamic_stability_analysis(cpacs_path, cpacs_out_path)

    log.info('----- End of ' + MODULE_NAME + ' -----')
