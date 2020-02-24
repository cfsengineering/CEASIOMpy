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
from numpy import linalg as la # For eigen values and aigen voectors
import matplotlib as mpl, cycler
import matplotlib.patheffects
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
from scipy import signal # For transfert function

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
from ceasiompy.StabilityDynamic.func import get_unic, interpolation, get_index,  trim_derivative, find_max_min, \
                                            plot_multicurve, speed_derivative_at_trim, adimensionalise, \
                                            speed_derivative_at_trim_lat
                                            # short_period, phugoid, roll, spiral, dutch_roll,
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
    flight_qualities_case_xpath = model_xpath + '/analyses/flyingQualities/fqCase'
    aircraft_class_xpath = flight_qualities_case_xpath + '/class' # Classes 1 2 3 4 small, heavy ...
    aircraft_cathegory_xpath = flight_qualities_case_xpath + '/cathegory' # flight phase A B C
    # Xpath of longitudinal transfter function polynoms
    num_tf_elev_theta_xpath = flight_qualities_case_xpath + '/longitudinal/numThe'# numerator of TF pitch angle theta due to elevator deflection
    den_tf_longi_xpath = flight_qualities_case_xpath + '/longitudinal/denLon' # denominator of longitudinal motion
    # Xpath of lateral-directional transfter function polynoms of 5th order system
    num_tf_ail_phi_xpath = flight_qualities_case_xpath +'lateral/numPhiDas'  # numerator of TF of aileron impact to  bank angle, roll angle phi
    num_tf_ail_r_xpath = flight_qualities_case_xpath +'lateral/numRDas'  # numerator of TF of aileron impact to  yaw rate : r
    num_tf_ail_beta_xpath = flight_qualities_case_xpath +'lateral/numBetaDas'  # numerator of TF of aileron impact to sideslip angle : beta
    num_tf_rud_r_xpath = flight_qualities_case_xpath +'lateral/numRDrp'  # numerator of TF of rudder impact to yaw rate : r
    num_tf_rud_beta_xpath = flight_qualities_case_xpath +'lateral/numBetaDrp'  # numerator of TF of rudder impact to sideslip angle : beta
    den_tf_latdir_xpath = flight_qualities_case_xpath + '/lateral/denLat' # denominator of longitudinal motion
    # Xpath of modes stability paramters of reduced order system
    sp_frequency_xpath = flight_qualities_case_xpath + '/charParameters/shortPeriod/spFrequency' # short period omega [rad/s]
    sp_damping_xpath = flight_qualities_case_xpath + '/charParameters/shortPeriod/spDamping' # short period damping ratio [-]
    ph_damping_xpath = flight_qualities_case_xpath + '/charParameters/phugoid/phDamping' # short period damping ratio [-]
    ph_double_xpath = flight_qualities_case_xpath + '/charParameters/phugoid/phDoubleTime' # sphugoid time to double amplitude [s]
    roll_time_xpath = flight_qualities_case_xpath + '/charParameters/eiglat/rollTimeConstant' # roll time constant [s]
    roll_frequency_xpath = flight_qualities_case_xpath + '/charParameters/eiglat/rollFrequency' # roll natural frequency [rad/s]
    spiral_double_xpath = flight_qualities_case_xpath + '/charParameters/eiglat/spiralDoublingTime' # spiral time to double amplitude [s]
    dr_frequency_xpath = flight_qualities_case_xpath + '/charParameters/eiglat/dutchRollFrequency' # short period omega [rad/s]
    dr_damping_xpath = flight_qualities_case_xpath + '/charParameters/eiglat/dutchRollDamping' # short period damping ratio [-]
    coupling_xpath = flight_qualities_case_xpath + '/charParameters/rollSpiral' # to indicate if raoll and spiral are coupled.

    # Ask user if reference area is : Wing already
    # Ask user flight path angles : gamma_e
    flight_path_angle = [0] # [-15,-10,-5,0,5,10,15] # The user should have the choice to select them !!!!!!!!!!!!!!!!!!!!
    # user has to answer y, if after 30 sec user has not answered make claculation
    # Ask user to proceed calculations at beta = 0 for having trimm flight conditions
    tixi = open_tixi(cpacs_path)

    # Get aeromap uid
    aeromap_uid = get_value(tixi, aeromap_uid_xpath )
    log.info('The following aeroMap will be analysed: ' + aeromap_uid)
    # Mass configuration: (Maximum landing mass, Maximum ramp mass (the maximum weight authorised for the ground handling), Take off mass, Zero Fuel mass)
    mass_config = get_value(tixi, '/cpacs/toolspecific/CEASIOMpy/stability/dynamic/MassConfiguration')
    log.info('The aircraft mass configuration used for analysis is: ' + mass_config)
    # Analyses to do [Short, phug, roll, spiral, Dutch_roll]
    longitudinal_analysis = get_value(tixi, dynamic_analysis_xpath + '/instabilityModes/longitudinal')
    lateral_directional_analysis = get_value(tixi, dynamic_analysis_xpath + '/instabilityModes/lateralDirectional')

    # Plots configuration with Setting GUI
    show_plots = get_value_or_default(tixi,'/cpacs/toolspecific/CEASIOMpy/stability/dynamic/showPlots',False)
    save_plots = get_value_or_default(tixi,'/cpacs/toolspecific/CEASIOMpy/stability/dynamic/savePlots',False)

    mass_config_xpath = model_xpath + '/analyses/massBreakdown/designMasses/' + mass_config
    if tixi.checkElement(mass_config_xpath):
        mass_xpath = mass_config_xpath + '/mass'
        I_xx_xpath  = mass_config_xpath + '/massInertia/Jxx'
        I_yy_xpath  = mass_config_xpath + '/massInertia/Jyy'
        I_zz_xpath = mass_config_xpath + '/massInertia/Jzz'
        I_xz_xpath = mass_config_xpath + '/massInertia/Jxz'
    else :
        raise ValueError(' !!! The mass configuration : {} is not defined in the CPACS file !!!'.format(mass_config))

    s = get_value(tixi,ref_area_xpath)     # Wing area : s  for non-dimonsionalisation of aero data.
    mac = get_value(tixi,ref_length_xpath) # ref length for non dimensionalisation, Mean aerodynamic chord: mac,

    # if wing span not stored in cpacs, then calculate it.         # or without tigle, simply: b = ref_area / ref_length
    wing_span_xpath = dynamic_analysis_xpath + '/largestSpan'
    if tixi.checkElement(wing_span_xpath) :
        b = get_value(tixi, wing_span_xpath)
    else :
        tigl = open_tigl(tixi)
        max_area, b  = get_largest_wing_dim(tixi,tigl) # Maximum wing area,  maximum aircraft span () calulated in "Skin friction" module
    mac_calculated= s/b
    log.info('The mean aero chord calculated from wing area and span (S/b) is : {}. And ref_length is : {}'.format(mac_calculated, mac))

    m = get_value(tixi,mass_xpath) # aircraft mass dimensional
    I_xx = get_value(tixi,I_xx_xpath) # X inertia dimensional
    I_yy = get_value(tixi,I_yy_xpath) # Y inertia dimensional
    I_zz = get_value(tixi,I_zz_xpath) # Z inertia dimensional
    I_xz = get_value(tixi,I_xz_xpath) # XZ inertia dimensional

    Coeffs = get_aeromap(tixi, aeromap_uid)

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

    # Initialise variables
    longi_data= []
    lat_dir_data = []
    cpacs_stability_short = True
    cpacs_stability_phugoid = True
    cpacs_stability_roll = True
    cpacs_stability_spiral = True
    cpacs_stability_dutch = True

    # All different vallues with only one occurence
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
            u0,m_adim,i_xx,i_yy,i_zz,i_xz = adimensionalise(a,mach,rho,s,b,mac,m,I_xx,I_yy,I_zz,I_xz)

            plot_damp_longi = []
            plot_freq_longi = []
            legend_longi = []

            plot_damp_dir = []
            plot_freq_dir = []
            legend_dir = []

            # Longitudinal dynamic stability,
            # Hyp: trim condition when beta = 0 and dCm/dalpha = 0
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
                    # --------------------  Calculate trim conditions  Begin    ------------------------------
                    cms = []
                    aoa = []
                    for index in find_index:
                        cms.append(cms_list[index])
                        aoa.append(aoa_list[index])
                    trim_aoa, cms_alpha0, idx_trim_before, idx_trim_after, ratio = trim_derivative(alt, mach, cms, aoa)
                    flight_condition = [alt, mach, trim_aoa] # [alt, mach, trim_aoa], aos=0
                    # --------------------  Calculate trim conditions  END   ------------------------------

                    if longitudinal_analysis :
                        aos = []
                        cl = []
                        cd = []
                        dcldqstar = []
                        dcddqstar = []
                        dcmsdqstar = []
                        for index in find_index:
                            aos.append(aos_list[index])
                            cl.append(cl_list[index])
                            cd.append(cd_list[index])
                            dcldqstar.append(dcldqstar_list[index])
                            dcddqstar.append(dcddqstar_list[index])
                            dcmsdqstar.append(dcmsdqstar_list[index])

                        # ----------------------  Trimm variables : Begining  ---------------
                        # Lift & drag coefficient derivative with respect to AOA at trimm
                        cl_alpha = (cl[idx_trim_after] - cl[idx_trim_before]) / (aoa[idx_trim_after] - aoa[idx_trim_before])
                        cd_alpha = (cd[idx_trim_after] - cd[idx_trim_before]) / (aoa[idx_trim_after] - aoa[idx_trim_before])

                        cd0 =interpolation(cd, idx_trim_before, idx_trim_after, ratio) # Dragg coeff at trim
                        cl0 =interpolation(cl, idx_trim_before, idx_trim_after, ratio) # Lift coeff at trim
                        dcddqstar0 = interpolation(dcddqstar, idx_trim_before, idx_trim_after, ratio) # x_q
                        dcldqstar0 = interpolation(dcldqstar, idx_trim_before, idx_trim_after, ratio) # z_q
                        dcmsdqstar0 = interpolation(dcmsdqstar, idx_trim_before, idx_trim_after, ratio) # m_q
                        cm_alpha0 = cms_alpha0

                        # Speed derivatives if there is at least 2 distinct mach values
                        if len(mach_unic) >=2 :
                            dcddm0 =speed_derivative_at_trim(cd,mach,idx_alt,aoa_list,aos,aos_list,mach_unic,idx_trim_before, idx_trim_after, ratio)
                            if dcddm0 == None :
                                dcddm0 = 0
                                log.warning('Not enough data to determine dcddm or (Cd_mach) at trim condition at Alt = {}, mach = {}, aoa = {}, aos = 0. Assumption: dcddm = 0'.format(alt,mach,round(trim_aoa,2)))
                            dcldm0 =speed_derivative_at_trim(cl,mach,idx_alt,aoa_list,aos,aos_list,mach_unic,idx_trim_before, idx_trim_after, ratio)
                            if dcldm0 == None :
                                dcldm0 = 0
                                log.warning('Not enough data to determine dcldm (Cl_mach) at trim condition at Alt = {}, mach = {}, aoa = {}, aos = 0. Assumption: dcldm = 0'.format(alt,mach,round(trim_aoa,2)))
                        else :
                            dcddm0 = 0
                            dcldm0 = 0
                            log.warning('Not enough data to determine dcddm (Cd_mach) and dcldm (Cl_mach) at trim condition at Alt = {}, mach = {}, aoa = {}, aos = 0. Assumption: dcddm = dcldm = 0'.format(alt,mach,round(trim_aoa,2)))

                        # Controls Derivatives to be found in the CPACS
                        dcddeta0 = 0
                        dcldeta0 = 0
                        dcmsdeta0 = 0
                        dcddtau0 = 0
                        dcldtau0 = 0
                        dcmsdtau0 = 0
                        # ------------  Trimm condition : End   --------------

                        # -----------------  Traduction Ceasiom -> Theory   Begin   ----------------------
                        Ue = u0*np.cos(trim_aoa)    # *np.cos(aos) as aos = 0 at trim, cos(aos)=1
                        We = u0*np.sin(trim_aoa)    # *np.cos(aos) as aos = 0 at trim, cos(aos)=1
                        # Ve = u0*np.sin(trim_aos)  # Ve = 0 for symetric flight conditions

                        # Dimentionless State Space variables,
                        # In generalised body axes coordinates ,
                        # simplifications: Ue=V0, We=0, sin(Theta_e)=0 cos(Theta_e)=0
                        # TODO: Double check how they are non-dimensionalised
                        X_u = -2*cd0 - mach*dcddm0
                        Z_u =  -2*cl0 - mach*dcldm0
                        M_u =  0 # Negligible

                        X_w = cl0 - cd_alpha # D'alleurs je ne comprends pas pc'est pas cl_alpha tout court
                        Z_w = -(cl_alpha + cd0)
                        M_w = cm_alpha0

                        X_q = dcddqstar0
                        Z_q = dcldqstar0
                        M_q = dcmsdqstar0

                        X_dotw = 0 # Negligible
                        Z_dotw = 1/3 * M_q / u0  # # Thumb rule  + Combination (Thomas R. Yechout)
                        M_dotw = 1/3 * M_q / u0 # Thumb rule (Thomas R. Yechout)

                        # Controls:
                        X_eta = dcddeta0 # To be found from the cpacs file, and defined by the user!
                        Z_eta = dcldeta0 # To be found from the cpacs file, and defined by the user!
                        M_eta = dcmsdeta0 # To be found from the cpacs file, and defined by the user!

                        X_tau = dcddtau0 # To be found from the cpacs file, and defined by the user!
                        Z_tau = dcldtau0 # To be found from the cpacs file, and defined by the user!
                        M_tau = dcmsdtau0  # To be found from the cpacs file, and defined by the user!
                        # -----------------  Traduction Ceasiom -> Theory   END -----------------------------------

                        # -----------------   Concise derivatives in body axes coordinates BEGIN ----------------
                        x_u = X_u/m_adim + (mac/u0*X_dotw*Z_u)/(m_adim*(m_adim-mac/u0*Z_dotw))
                        z_u = Z_u / (m_adim -mac/u0*Z_dotw)
                        m_u = M_u / i_yy + (mac/u0*M_dotw*Z_u)/(i_yy*(m_adim-mac/u0*Z_dotw))

                        x_w = X_w/m_adim + (mac/u0*X_dotw*Z_w)/(m_adim*(m_adim - mac/u0*Z_dotw))
                        z_w = Z_w / (m_adim - mac/u0*Z_dotw)
                        m_w = M_w/ i_yy + (mac/u0*M_dotw*Z_w)/(i_yy*(m_adim-mac/u0*Z_dotw))

                        x_q = (mac*X_q - m_adim*We)/m_adim + ((mac*Z_q+m_adim*u0)*mac/u0*X_dotw)/(m_adim*(m_adim-mac/u0*Z_dotw))
                        z_q = (mac*Z_q + m_adim*u0)/ (m_adim - mac/u0*Z_dotw)
                        m_q = (mac*M_q)/i_yy + ((mac*Z_q + m_adim*Ue)*mac/u0*M_dotw)/(i_yy*(m_adim-mac/u0*Z_dotw))

                        x_eta = (u0*X_eta)/m_adim + (mac/u0*X_dotw*Z_eta)/(m_adim - mac/u0*Z_dotw)
                        z_eta = (u0*Z_eta)/(m_adim-mac/u0*Z_dotw)
                        m_eta = (u0*M_eta)/i_yy + (mac*M_dotw*Z_eta)/(i_yy*(m_adim-mac/u0*Z_dotw))

                        x_tau = (u0*X_tau)/m_adim + (mac/u0*X_dotw*Z_tau)/(m_adim - mac/u0*Z_dotw)
                        z_tau = (u0*Z_tau)/(m_adim-mac/u0*Z_dotw)
                        m_tau = (u0*M_tau)/i_yy + (mac*M_dotw*Z_tau)/(i_yy*(m_adim-mac/u0*Z_dotw))
                        # -----------------   Concise derivatives in body axes coordinates END -------------------

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
                            aos.append(aos_list[index])
                            aoa.append(aoa_list[index]) # For Ue We
                            cs.append(cs_list[index])
                            dcsdpstar.append(dcsdpstar_list[index]) # y_p
                            dcmddpstar.append(dcmddpstar_list[index]) # l_p
                            dcmldpstar.append(dcmldpstar_list[index]) # n_p
                            dcsdrstar.append(dcsdrstar_list[index]) # y_r
                            dcmldrstar.append(dcmldrstar_list[index]) # n_r
                            dcmddrstar.append(dcmddrstar_list[index]) # l_r

                        # ------------------      Trimm condition  calculation  Begin -------------
                        # speed derivatives :  y_v / l_v / n_v  /  Must be devided by speed given that the hyp v=Beta*U
                        # cs_beta0 = (cs[idx_trim_after] - cs[idx_trim_before]) / (aos[idx_trim_after] - aos[idx_trim_before]) # y_v
                        # cmd_beta0 = (cmd[idx_trim_after] - cmd[idx_trim_before]) / (aos[idx_trim_after] - aos[idx_trim_before]) # l_v
                        # cml_beta0 = (cml[idx_trim_after] - cml[idx_trim_before]) / (aos[idx_trim_after] - aos[idx_trim_before]) # n_v
                        if len(aos_unic) >=2 :
                            cs_beta0 =        speed_derivative_at_trim_lat (cs,0,idx_alt,aoa_list,mach_list,mach,aos_list,aos_unic,idx_trim_before, idx_trim_after, ratio)# y_v
                            if cs_beta0 == None :
                                cs_beta0 = 0
                                log.warning('Not enough data to determine cs_beta (Y_v) at trim condition at Alt = {}, mach = {}, aoa = {}, aos = 0. Assumption: cs_beta = 0'.format(alt,mach,round(trim_aoa,2)))
                            cmd_beta0  = speed_derivative_at_trim_lat(cmd,0,idx_alt,aoa_list,mach_list,mach,aos_list,aos_unic,idx_trim_before, idx_trim_after, ratio)# l_v
                            if cmd_beta0 ==None :
                                cmd_beta0 = 0
                                log.warning('Not enough data to determine cmd_beta (L_v) at trim condition at Alt = {}, mach = {}, aoa = {}, aos = 0. Assumption: cmd_beta = 0'.format(alt,mach,round(trim_aoa,2)))
                            cml_beta0 =    speed_derivative_at_trim_lat(cml,0,idx_alt,aoa_list,mach_list,mach,aos_list,aos_unic,idx_trim_before, idx_trim_after, ratio)# n_v
                            if cml_beta0 == None :
                                cml_beta0 = 0
                                log.warning('Not enough data to determine cml_beta (N_v) at trim condition at Alt = {}, mach = {}, aoa = {}, aos = 0. Assumption: cml_beta = 0'.format(alt,mach,round(trim_aoa,2)))
                        else :
                            cs_beta0 = 0
                            cmd_beta0 = 0
                            cml_beta0 = 0
                            log.warning('Not enough data to determine cs_beta (Y_v), cmd_beta (L_v) and cml_beta (N_v) at trim condition at Alt = {}, mach = {}, aoa = {}, aos = 0. Assumption: cs_beta = cmd_beta = cml_beta = 0'.format(alt,mach,round(trim_aoa,2)))

                        trim_aoa0 = interpolation(aoa, idx_trim_before, idx_trim_after, ratio) # For Ue We
                        dcsdpstar0 = interpolation(dcsdpstar, idx_trim_before, idx_trim_after, ratio) # y_p
                        dcmddpstar0  = interpolation(dcmddpstar, idx_trim_before, idx_trim_after, ratio) # l_p
                        dcmldpstar0 = interpolation(dcmldpstar, idx_trim_before, idx_trim_after, ratio) # n_p

                        dcsdrstar0 =interpolation(dcsdrstar, idx_trim_before, idx_trim_after, ratio) # y_r
                        dcmldrstar0 =  interpolation(dcmldrstar, idx_trim_before, idx_trim_after, ratio) # n_r
                        dcmddrstar0 =  interpolation(dcmddrstar, idx_trim_before, idx_trim_after, ratio) # l_r

                        # Controls : will have to be found in the cpacs
                        dcsdxi0 = 0
                        dcmddxi0 = 0
                        dcmldxi0 = 0
                        dcsdzeta0 = 0
                        dcmddzeta0 = 0
                        dcmldzeta0 = 0
                        # -----------------     Trim conditions END    ---------------

                        # -----------------  Traduction Ceasiom -> Theory   Begin   ----------------------
                        Y_v = cs_beta0/u0
                        L_v = cmd_beta0/u0
                        N_v = cml_beta0/u0

                        Y_p = dcsdpstar0 # TODO : - sign must be checked between conventions and ceasiom
                                                     #               - Is the value coherent ?  could be neglected
                        L_p = dcmddpstar0 # TODO : sign must be checked between conventions and ceasiom
                        N_p = dcmldpstar0

                        Y_r = dcsdrstar0
                        N_r = dcmldrstar0*mac/b
                        L_r = dcmddrstar0*mac/b

                        # Controls:
                        Y_xi = dcsdxi0 # To be found from the cpacs file, and defined by the user!
                        L_xi = dcmddxi0 # To be found from the cpacs file, and defined by the user!
                        N_xi = dcmldxi0 # To be found from the cpacs file, and defined by the user!

                        Y_zeta = dcsdzeta0 # To be found from the cpacs file, and defined by the user!
                        L_zeta = dcmddzeta0 # To be found from the cpacs file, and defined by the user!
                        N_zeta = dcmldzeta0 # To be found from the cpacs file, and defined by the user!

                        Ue = u0*np.cos(trim_aoa) # *np.cos(aos) as aos = 0 at trim, cos(aos)=1
                        We = u0*np.sin(trim_aoa) # *np.cos(aos) as aos = 0 at trim, cos(aos)=1
                        # -----------------  Traduction Ceasiom -> Theory   END   ----------------------

                        # -----------------   Concise derivatives in body axes coordinates BEGIN ----------------
                        y_v = Y_v/m_adim
                        y_p = (b*Y_p + m_adim*We)/m_adim
                        y_r =  (b*Y_r + m_adim*Ue)/m_adim

                        l_v = (i_zz*L_v + i_xz * N_v)/(i_xx*i_zz - i_xz**2)
                        l_p = (i_zz*L_r + i_xz * N_r)/(i_xx*i_zz - i_xz**2)
                        l_r = (i_zz*L_v + i_xz * N_v)/(i_xx*i_zz - i_xz**2)
                        l_phi = 0
                        l_psi = 0

                        n_v = (i_xx*N_v + i_xz*L_v)/(i_xx*i_zz-i_xz**2)
                        n_p = (i_xx*N_p + i_xz*L_p)/(i_xx*i_zz-i_xz**2)
                        n_r = (i_xx*N_r + i_xz*L_r)/(i_xx*i_zz-i_xz**2)
                        n_phi = 0
                        n_psi = 0

                        # Controls
                        y_xi = u0*Y_xi/m_adim
                        l_xi = u0*(i_zz*L_xi+i_xz*N_xi)/(i_xx*i_zz-i_xz**2)
                        n_xi = u0*(i_xx*N_xi+i_xz*L_xi)/(i_xx*i_zz-i_xz**2)

                        y_zeta = u0*Y_zeta/m_adim
                        l_zeta = u0*(i_zz*L_zeta+i_xz*L_zeta)/(i_xx*i_zz-i_xz**2)  # A mon avis il y a une faute, il ne doit surement pas il y avoir 2 fois L_zeta au numerateur et il devrait il y avoir i_xx en comparaison, les l et n_xi
                        n_zeta = u0*(i_zz*N_zeta+i_xz*L_zeta)/(i_xx*i_zz-i_xz**2)
                        # -----------------   Concise derivatives in body axes coordinates END ----------------

                    for angles in  flight_path_angle:
                        theta_e =  angles + trim_aoa

                        if longitudinal_analysis :
                            x_theta = - g*np.cos(theta_e) - (mac/u0*X_dotw*g*np.sin(theta_e))/(m_adim-mac/u0*Z_dotw)
                            z_theta = - (m_adim*g*np.sin(theta_e))/(m_adim - mac/u0*Z_dotw)
                            m_theta = - (mac/u0*M_dotw*m_adim*g*np.sin(theta_e))/(i_yy*(m_adim - mac/u0*Z_dotw))

                            # Longitudinal state and input matrix in concise form
                            A_longi = np.array([[x_u,  x_w , x_q , x_theta ],
                                                            [z_u , z_w , z_q , z_theta ] ,
                                                            [m_u ,m_w , m_q , m_theta ],
                                                            [   0   ,   0    ,    1   ,      0       ]])

                            B_longi = np.array([[x_eta ,x_tau ],
                                                            [z_eta, z_tau ],
                                                            [m_eta, m_tau],
                                                            [    0    ,      0   ]])
                            C_longi = np.identity(4)
                            D_longi = np.zeros((4,2))

                            print('-----  Longi ------') # debugg

                            eg_value_longi , eg_vector_longi = la.eig(A_longi)
                            print('\n Eigenvalues Longitudinal :')
                            print(eg_value_longi)
                            print('\n Eigenvectors Longitudinal :')
                            print(eg_vector_longi)

                        if lateral_directional_analysis:
                            y_phi = g * np.cos(theta_e)
                            y_psi = g * np.sin(theta_e)

                            # Lateral-directional state and input matrix in concise form
                            A_direc = np.array([[ y_v, y_p, y_r, y_phi, y_psi ],
                                                            [ l_v,  l_p,  l_r,   l_phi, l_psi ],
                                                            [n_v,  n_p, n_r,  n_phi, n_psi],
                                                            [  0  ,  1   ,    0 ,     0     ,    0   ],
                                                            [  0  ,  0   ,    1 ,     0     ,    0   ]])

                            B_direc = np.array([[ y_xi, y_zeta],
                                                            [l_xi  , l_zeta],
                                                            [n_xi , n_zeta],
                                                            [   0   ,      0    ],
                                                            [   0   ,      0    ]])
                            print('-----  Lat-Dir  ------')

                            C_direc = np.identity(5)
                            D_direc = np.zeros((5,2))
                            # sys_direc = signal.ZerosPolesGain(A_direc,  B_direc, C_direc, D_direc)

                            # print(sys_direc) #debugg
                            # In cincise form,   delta = aS^5 + bS^4 + cS^3+ dS^2 + eS + f ,  delta_direc =[a,b,c,d,e,f]
                            delta_direc = [1,\
                                                    -(l_p+n_r+y_v),
                                                    (l_p*n_r-l_r*n_p)+(n_r*y_v-n_v*y_r)+(l_p*y_v-l_v*y_p)-(l_phi+n_psi),\
                                                    (l_p*n_psi-l_psi*n_p)+(l_phi*n_r-l_r*n_phi)+l_v*(n_r*y_p-n_p*y_r-y_phi)+n_v*(l_p*y_r-l_r*y_p-y_psi)+y_v*(l_r*n_p-l_p*n_r+l_phi+n_psi),\
                                                    (l_phi*n_psi-l_psi*n_psi)+l_v*((n_r*y_phi-n_phi*y_r)+(n_psi*y_p-n_p*y_psi))+n_v*((l_phi*y_r-l_r*y_phi)+(l_p*y_psi-l_psi*y_p))+y_v*((l_r*n_phi-l_phi*n_r)+(l_psi*n_p-l_p*n_psi)),\
                                                    l_v*(n_psi*y_phi-n_phi*y_psi)+n_v*(l_phi*y_psi-l_psi*y_phi)+y_v*(l_psi*n_phi-l_phi*n_psi)]
                            roots_direc = np.roots(delta_direc)
                            print('\n Roots Den TF Lateral-Directional : ')
                            print(roots_direc)

                            eg_value_direc , eg_vector_direc = la.eig(A_direc)
                            print('\n Eigenvalues Lateral-Directional : ')
                            print(eg_value_direc)
                            print('\n Eigenvectors Lateral-Directional : ')
                            print(eg_vector_direc)


                            # Compute numerator TF for (Alt, mach, flight_path_angle, aoa_trim, aos=0)
                            #  TO BE DOOOOONNNNE !!!!!!!!!!!!!!!
                            # Works for a transfert function but not for a statestpace model, signal.statespace returns the temporal solution of the LTI system.
                            # zeros poles gain  = signal.ZerosPolesGain(A_longi,  B_longi , C_longi, D_longi)

                            # print(sys_longi) #debugg

                            # Compute eigenvalues and eigenvectors for (Alt, mach, flight_path_angle, aoa_trim, aos=0)
                            # delta = a S^4 + bS^3 + cS^2 + dS  + e  , delta_longi  = [a,b,c,d,e]
                            delta_longi = [1, \
                                                   -(m_q+x_u+z_w),\
                                                   (m_q*z_w - m_w*z_q) + (m_q*x_u - m_u*x_q) + (x_u*z_w - x_w*z_u) - m_theta,\
                                                   (m_theta*x_u-m_u*x_theta)+(m_theta*z_w-m_w*z_theta)+m_q*(x_w*z_u-x_u*z_w)+x_q*(m_u*z_w-m_w*z_u)+z_q*(m_w*x_u-m_u*x_w),\
                                                   m_theta*(x_w*z_u-x_u*z_w)+x_theta*(m_u*z_w-m_w*z_u)+z_theta*(m_w*x_u-m_u*x_w)]
                            roots_longi = np.roots(delta_longi)
                            print(roots_longi)

                            eg_value_longi , eg_vector_longi = la.eig(A_longi)
                            print(eg_value_longi)
                            print(eg_vector_longi)

                            # Undamped natural frequency omega, of non dimensional equations
                            w_short = np.sqrt(roots_longi[0]*roots_longi[1])
                            w_phug = np.sqrt(roots_longi[2]*roots_longi[3])

                            # Damping of equations non dimensonalised
                            damp_short = np.real(roots_longi[0])/w_short
                            damp_phug = np.real(roots_longi[2])/w_phug





                    # save parameters
                    #  coupling_xpath : "normal" # normal: roll and spiral mode are not coupled.


                #         if short_period :
                #             short_damp , short_freq = short_period(u0, qs, m, i_yy, mac, cm_alpha0,  cd0, cl_alpha, cm_q )
                #             data.append(short_damp), data.append(short_freq)
                #             if short_damp >= 0 :
                #                 log.warning('Alt = {}, Mach= {} & AOS = {}°, aircraft NOT stable in Short Period Mode'.format(alt, mach, aos))
                #                 cpacs_stability_short = False
                #             else :
                #                 log.info('Alt = {}, Mach= {} & AOS = {}°, aircraft is stable in Short Period Mode'.format(alt, mach, aos))
                #         else :
                #             short_damp , short_freq = [0, 0]
                #         if phugoid:
                #             phug_damp, phug_freq = phugoid(u0, cd0, cl0, g)
                #             data.append(phug_damp), data.append(phug_freq)
                #             if phug_damp >= 0 :
                #                 log.warning('Alt = {}, Mach= {} & AOS = {}°, aircraft NOT stable in Phugoid Mode'.format(alt, mach, aos))
                #                 cpacs_stability_phugoid = False
                #             else:
                #                 log.info('Alt = {}, Mach= {} & AOS = {}°, aircraft is stable in Phugoid Mode'.format(alt, mach, aos))
                #         else:
                #             phug_damp, phug_freq = [0, 0]
                #
                #         # For plotting :
                #         longi_data.append(data)
                #         plot_damp_longi.append([short_damp, phug_damp])
                #         plot_freq_longi.append([short_freq, phug_freq])
                #         legend_longi.append('AOS = ' + str(aos) +r', $\alpha_{trim}$ = '+ str(trim_aoa) + '°')
                # # Plots longi  for Alt Mach and different Aos  Im Vs Real    for diff
                # # @ Alt MAch in legend all the different AOS, and the trimm AOA
                # if plot_damp_longi:
                #     title_longi = 'Alt = {} , Mach = {}, and different AOS'.format(alt, mach)
                #     plot_multicurve(analysis, plot_damp_longi, plot_freq_longi,  legend_longi, title_longi, 'Re', 'Im', show_plots, save_plots)

            # Lateral-Directional stability
            # Hyp: trim condition when beta = 0 and aoa such that dCm/dalpha = 0



    #  $$$$$$$$$$$$$$$$   BEGIN  COMMENT  debugg     $$$$$$$$
    #
    #                     #Lateral Directionnal
    #                     if roll_analysis:
    #                         roll_damp, roll_freq = roll(u0, qs, i_xx, i_zz, b, cl_p, cn_p)
    #                         data.append(roll_damp), data.append(roll_freq)
    #                         if roll_damp >= 0 :
    #                             cpacs_stability_roll = False
    #                             log.warning('Alt = {}, Mach= {} & AOA = {}°, aircraft NOT stable in Roll Mode'.format(alt, mach, aoa))
    #                         else:
    #                             log.info('Alt = {}, Mach= {} & AOA = {}°, aircraft is stable in Roll Mode'.format(alt, mach, aoa))
    #                     else:
    #                         roll_damp, roll_freq = [0, 0]
    #
    #
    #
    #                     if spiral_analysis :
    #                         spiral_damp, spiral_freq = spiral(u0, qs, b, i_xx, i_yy, cn_r, cl_r, cl_beta, cn_beta)
    #                         data.append(spiral_damp), data.append(spiral_freq)
    #                         if spiral_damp >= 0 :
    #                             cpacs_stability_spiral = False
    #                             log.warning('Alt = {}, Mach= {} & AOA = {}°, aircraft NOT stable in Spiral Mode'.format(alt, mach, aoa))
    #                         else:
    #                             log.info('Alt = {}, Mach= {} & AOA = {}°, aircraft is stable in Roll Mode'.format(alt, mach, aoa))
    #                     else :
    #                         spiral_damp, spiral_freq = [0, 0]
    #
    #                     # Dutch Roll: all coefficients are already found ,  dutch roll : combination of spiral and roll
    #                     if dutch_analysis :
    #                         dutch_damp, dutch_freq =dutch_roll(u0, qs, b, i_xx, i_zz, cl_p, cl_r, cl_beta , cn_p, cn_r, cn_beta)
    #                         data.append(dutch_damp), data.append(dutch_freq)
    #                         if dutch_damp >= 0 :
    #                             log.warning('Alt = {}, Mach= {} & AOA = {}°, aircraft NOT stable in Dutch-Roll Mode'.format(alt, mach, aoa))
    #                             cpacs_stability_dutch = False
    #                         else:
    #                             log.info('Alt = {}, Mach= {} & AOA = {}°, aircraft is stable in Roll Mode'.format(alt, mach, aoa))
    #                     else:
    #                         dutch_damp, dutch_freq = [0, 0]
    #
    #                     # For plotting
    #                     lat_dir_data.append(data)
    #                     plot_damp_dir.append([roll_damp, spiral_damp, dutch_damp])
    #                     plot_freq_dir.append([roll_freq, spiral_freq, dutch_freq])
    #                     legend_dir.append('AOA = ' + str(aoa) + r'°, $\beta_{trim}$ = ' + str(trim_aos) + '°')
    #             # If there is at least one curve to plot , plot_damp_dir is not empty
    #             if plot_damp_dir:
    #                 # Plot Directionnal-Lateral for Alt Mach and different aoa
    #                 title_dir = 'Alt = {} , mach = {}, and different AOA'.format(alt, mach)
    #                 plot_multicurve(analysis, plot_damp_dir, plot_freq_dir,  legend_dir, title_dir, 'Re', 'Im', show_plots, save_plots)
    #
    # # Graphs for Alt, AOS-AOA and different mach
    # # Longi
    # if short_analysis or phugoid_analysis :
    #     for alt in alt_unic :
    #         plot_damp_longi = []
    #         plot_freq_longi = []
    #         legend_longi = []
    #         #idx_alt = [i for i in range(len(longi_data)) if longi_data[i][0] == alt]
    #         for aos in aos_unic :
    #             # idx_aos= [i for i in range(len(longi_data)) if longi_data[i][2] == aos]
    #             for mach in mach_unic :
    #                 # idx_mach= [i for i in range(len(longi_data)) if longi_data[i][1] == mach]
    #                 for data in longi_data :
    #                     if data[0] == alt and data[1] == mach and data[2] == aos :
    #                         # Get the data to plot in the element of longi_data at (alt, mach, aos)
    #                         # index = get_index(idx_alt, idx_aos,idx_mach)[0] # will return one index
    #                         # print('index' + str(index))
    #
    #                         # trim_aoa = longi_data[index][3]
    #                         # short_damp = longi_data[index][4]
    #                         # short_freq = longi_data[index][5]
    #                         # phugoid_damp = longi_data[index][6]
    #                         # phugoid_freq = aeromap_uidlongi_data[index][7]
    #                         trim_aoa = data[3]
    #                         short_damp = data[4]
    #                         short_freq = data[5]
    #                         phugoid_damp = data[6]
    #                         phugoid_freq = data[7]
    #                         # Prepare for plotting
    #                         plot_damp_longi.append([short_damp, phug_damp])
    #                         plot_freq_longi.append([short_freq, phug_freq])
    #                         legend_longi.append('mach = ' + str(mach) + r', $\alpha_{trim}$ = ' + str(trim_aoa) + '°')
    #         title_longi = 'Alt = {} , AOS= {}°, and different mach'.format(alt, aos)
    #         plot_multicurve(analysis, plot_damp_longi, plot_freq_longi,  legend_longi, title_longi, 'Re', 'Im', show_plots, save_plots)
    # # Directional-Lateral
    # if roll_analysis or spiral_analysis  or dutch_analysis :
    #     for alt in alt_unic :
    #         plot_damp_dir = []
    #         plot_freq_dir = []
    #         legend_dir = []
    #         for aoa in aoa_unic :
    #             for mach in mach_unic :
    #                 for data in lat_dir_data :
    #                     if data[0] == alt and data[1] == mach and data[2] == aoa :
    #                         # Get the data to plot in the element of lat_dir_data at (alt, mach, aos)
    #                         trim_aos = data[3]
    #                         roll_damp = data[4]
    #                         roll_freq = data[5]
    #                         spiral_damp = data[6]
    #                         spiral_freq = data[7]
    #                         dutchl_damp = data[8]
    #                         dutch_freq = data[9]
    #                         # Prepare for plotting
    #                         plot_damp_dir.append([roll_damp, spiral_damp, dutch_damp])
    #                         plot_freq_dir.append([roll_freq, spiral_freq, dutch_freq])
    #                         legend_dir.append('mach = ' + str(mach) + r', $\beta_{trim}$ = ' + str(trim_aos) + '°' )
    #         # Plot Directionnal-Lateral for Alt Mach and different aoa
    #         title_dir = 'Alt = {} , AOA = {}°, and different mach'.format(alt, aoa)
    #         plot_multicurve(analysis, plot_damp_dir, plot_freq_dir,  legend_dir, title_dir, 'Re', 'Im', show_plots, save_plots)
    #
    # # Graphs for mach, AOS-AOA and different alt
    # # Longi
    # if short_analysis or phugoid_analysis :
    #     for mach in mach_unic :
    #         plot_damp_longi = []
    #         plot_freq_longi = []
    #         legend_longi = []
    #         for aos in aos_unic :
    #             for alt in alt_unic :
    #                 for data in longi_data :
    #                     if data[0] == alt and data[1] == mach and data[2] == aos :
    #                         # Get the data to plot in the element of longi_data at (alt, mach, aos)
    #                         trim_aoa = data[3]
    #                         short_damp = data[4]
    #                         short_freq = data[5]
    #                         phugoid_damp = data[6]
    #                         phugoid_freq = data[7]
    #                         # Prepare for plotting
    #                         plot_damp_longi.append([short_damp, phug_damp])
    #                         plot_freq_longi.append([short_freq, phug_freq])
    #                         legend_longi.append('alt = ' + str(alt) + r', $\alpha_{trim}$ = ' + str(trim_aoa) + '°')
    #         title_longi = 'Mach= {} , AOS= {}°, and different AOS'.format(mach, aos)
    #         plot_multicurve(analysis, plot_damp_longi, plot_freq_longi,  legend_longi, title_longi, 'Re', 'Im', show_plots, save_plots)
    # # Directional-Lateral
    # if roll_analysis or spiral_analysis  or dutch_analysis :
    #     for mach in mach_unic :
    #         plot_damp_dir = []
    #         plot_freq_dir = []
    #         legend_dir = []
    #         for aoa in aoa_unic :
    #             for alt in alt_unic :
    #                 for data in lat_dir_data :
    #                     if data[0] == alt and data[1] == mach and data[2] == aoa :
    #                         # Get the data to plot in the element of lat_dir_data at (alt, mach, aos)
    #                         trim_aos = data[3]
    #                         roll_damp = data[4]
    #                         roll_freq = data[5]
    #                         spiral_damp = data[6]
    #                         spiral_freq = data[7]
    #                         dutchl_damp = data[8]
    #                         dutch_freq = data[9]
    #                         # Prepare for plotting
    #                         plot_damp_dir.append([roll_damp, spiral_damp, dutch_damp])
    #                         plot_freq_dir.append([roll_freq, spiral_freq, dutch_freq])
    #                         legend_dir.append('mach = ' + str(mach) + r', $\beta_{trim}$ = ' + str(trim_aos) + '°')
    #         # Plot Directionnal-Lateral for Alt Mach and different aoa
    #         title_dir = 'mach= {} , AOA = {}°, and different alt'.format(mach, aoa)
    #         plot_multicurve(analysis, plot_damp_dir, plot_freq_dir,  legend_dir, title_dir, 'Re', 'Im', show_plots, save_plots)
    # # Save results:
    # # xpath definition for saving results
    # short_xpath = aeromap_uid_xpath + '/results/shortPeriodStable'
    # phugoid_xpath = aeromap_uid_xpath + '/results/phugoidStable'
    # roll_xpath = aeromap_uid_xpath + '/results/rollStable'
    # spiral_xpath = aeromap_uid_xpath + '/results/spiralPeriodStable'
    # dutch_xpath = aeromap_uid_xpath + '/results/dutchRollStable'
    # # CPACS brench
    # create_branch(tixi, short_xpath )
    # create_branch(tixi, phugoid_xpath)
    # create_branch(tixi, roll_xpath)
    # create_branch(tixi, spiral_xpath )
    # create_branch(tixi, dutch_xpath )
    # # Store results in CPACS
    # if short_analysis :
    #     tixi.updateTextElement(short_xpath, str(cpacs_stability_short))
    # else:
    #     tixi.updateTextElement(short_xpath, str('notAnalysed'))
    # if phugoid_analysis :
    #     tixi.updateTextElement(phugoid_xpath, str(cpacs_stability_phugoid))
    # else:
    #     tixi.updateTextElement(phugoid_xpath, str('notAnalysed'))
    # if roll_analysis:
    #     tixi.updateTextElement(roll_xpath, str(cpacs_stability_roll))
    # else:
    #     tixi.updateTextElement(roll_xpath, str('notAnalysed'))
    # if spiral_analysis:
    #     tixi.updateTextElement(spiral_xpath, str(cpacs_stability_spiral))
    # else:
    #     tixi.updateTextElement(spiral_xpath, str('notAnalysed'))
    # if dutch_analysis:
    #     tixi.updateTextElement(dutch_xpath, str(cpacs_stability_dutch))
    # else:
    #     tixi.updateTextElement(dutch_xpath, str('notAnalysed'))
    #
    # close_tixi(tixi, cpacs_out_path)

    #  $$$$$$$$$$$$$$$$   END COMMENT  debugg     $$$$$$$$


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


############## Main #########
MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
cpacs_path = MODULE_DIR  + '/toolInput/toolInput.xml'
cpacs_out_path = MODULE_DIR  + '/toolOuput/toolOutput.xml'
dynamic_stability_analysis(cpacs_path, cpacs_out_path)
