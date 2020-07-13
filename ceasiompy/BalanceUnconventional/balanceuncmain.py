"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed for CFS ENGINEERING, 1015 Lausanne, Switzerland

Balance main module for preliminary design on conventional
aircraft, it evaluates:

 * the centre of gravity;
 * the Ixx, Iyy, Izz moments of inertia.

WARNING: The code deletes the ToolOutput folder and recreates
         it at the start of each run.
         The code also removes the toolinput file from the ToolInput
         folder after copying it into the ToolOutput folder
         as ToolOutput.xml

Python version: >=3.6

| Author : Stefano Piccini
| Date of creation: 2018-09-27
| Last modifiction: 2020-07-09 (AJ)
"""


#=============================================================================
#   IMPORTS
#=============================================================================

import os
import shutil

import numpy as np
import matplotlib
import matplotlib.pyplot as plt

from ceasiompy.utils.InputClasses.Unconventional import balanceuncclass
from ceasiompy.utils.InputClasses.Unconventional import weightuncclass
from ceasiompy.utils.InputClasses.Unconventional import engineclass

from ceasiompy.BalanceUnconventional.func.Cog.unccog import unc_center_of_gravity
from ceasiompy.BalanceUnconventional.func.Cog.unccog import bwb_center_of_gravity

from ceasiompy.BalanceUnconventional.func.Inertia import uncinertia
from ceasiompy.BalanceUnconventional.func.AoutFunc import outputbalancegen
from ceasiompy.BalanceUnconventional.func.AoutFunc import cpacsbalanceupdate
from ceasiompy.BalanceUnconventional.func.AinFunc import getdatafromcpacs

from ceasiompy.utils.cpacsfunctions import aircraft_name
from ceasiompy.utils.WB.UncGeometry import uncgeomanalysis
import ceasiompy.utils.moduleinterfaces as mi

from ceasiompy.utils.ceasiomlogger import get_logger

log = get_logger(__file__.split('.')[0])

MODULE_DIR = os.path.dirname(os.path.abspath(__file__))


#=============================================================================
#   CLASSES
#=============================================================================

"""All classes are defined inside the classes folder and into the
   InputClasses/Uconventional folder"""


#=============================================================================
#   FUNCTIONS
#=============================================================================

def get_balance_unc_estimations(cpacs_path, cpacs_out_path):
    """Function to estimate inertia value and CoF of an unconventional aircraft.

    Function 'get_balance_unc_estimations' ...

    Source:
        * Reference paper or book, with author and date, see ...

    Args:
        cpacs_path (str): Path to CPACS file
        cpacs_out_path (str):Path to CPACS output file

    """

    # Removing and recreating the ToolOutput folder.
    if os.path.exists('ToolOutput'):
        shutil.rmtree('ToolOutput')
    os.makedirs('ToolOutput')

    if not os.path.exists(cpacs_path):
        raise ValueError ('No "ToolInput.xml" file in the ToolInput folder.')

    name = aircraft_name(cpacs_path)

    shutil.copyfile(cpacs_path, cpacs_out_path) # TODO: shoud not be like that
    newpath = 'ToolOutput/' + name
    if not os.path.exists(newpath):
        os.makedirs(newpath)

    bout = balanceuncclass.BalanceOutputs()


    # BALANCE ANALSIS INPUTS

    bi = balanceuncclass.BalanceInputs()
    mw = balanceuncclass.MassesWeights()
    ui = weightuncclass.UserInputs()
    ed = engineclass.EngineData()

    adui = weightuncclass.AdvancedInputs()

    (mw, ed) = getdatafromcpacs.get_data(ui, bi, mw, ed, cpacs_out_path)


    # GEOMETRY ANALYSIS

    (fus_nb, w_nb) = uncgeomanalysis.get_number_of_parts(cpacs_path)
    if not w_nb:
        log.warning('Aircraft does not have wings')
        raise Exception('Aircraft does not have wings')
    elif not fus_nb:
        (awg, wing_nodes) =\
            uncgeomanalysis.no_fuse_geom_analysis(cpacs_path, ui.FLOORS_NB,     \
                                                  w_nb, ui.H_LIM_CABIN,   \
                                                  ui.FUEL_ON_CABIN, name, \
                                                  ed.TURBOPROP)
    else:
        log.info('Fuselage detected')
        log.info('Number of fuselage: ' + str(int(fus_nb)))
        # Minimum fuselage segment height to be a cabin segment.
        h_min = ui.FLOORS_NB * ui.H_LIM_CABIN
        (afg, awg) = uncgeomanalysis.with_fuse_geom_analysis(cpacs_path, \
                         fus_nb, w_nb, h_min, adui, ed.TURBOPROP, ui.F_FUEL, name)

    ui = getdatafromcpacs.get_user_fuel(fus_nb, ui, cpacs_out_path)

    # BALANCE ANALYSIS

    log.info('----- Generating output text file -----')
    log.info('---- Starting the balance analysis ----')
    log.info('---- Aircraft: ' + name)

    # CENTER OF GRAVITY

    if not fus_nb:
        (bout, airplane_centers_segs) =\
                bwb_center_of_gravity(awg, bout, ui, bi, mw, ed)
    else:
        (bout, airplane_centers_segs) =\
                unc_center_of_gravity(awg, afg, bout, ui, bi, mw, ed)

    # MOMENT OF INERTIA

    if not fus_nb:
        (bout, wx, wy, wz) = uncinertia.bwb_inertia_eval(awg, bout, bi, mw, ed, cpacs_out_path)
    else:
        (bout, fx, fy, fz, wx, wy, wz)\
            = uncinertia.unc_inertia_eval(awg, afg, bout, bi, mw, ed, cpacs_out_path)


    # OUTPUT WRITING

    log.info('----- Generating output text file -----')
    outputbalancegen.output_txt(bout, mw, bi, ed, name)

    # CPACS WRITING
    cpacsbalanceupdate.cpacs_mbd_update(bout, mw, bi, np.sum(mw.ms_zpm), cpacs_out_path)

    # PLOTS

    log.info('--- Generating aircraft center of gravity plot (.png) ---')
    if not fus_nb:
      outputbalancegen.aircraft_cog_bwb_plot(bout.center_of_gravity, bi, ed, awg, name)
    else:
      outputbalancegen.aircraft_cog_unc_plot(bout.center_of_gravity, bi, ed, afg, awg, name)

    # Aircraft Nodes
    #log.info('--- Generating aircraft nodes plot (.png) ---')
    #if not fus_nb:
        #outputbalancegen.aircraft_nodes_bwb_plot(wx, wy, wz, name)
    #else:
        #outputbalancegen.aircraft_nodes_unc_plot(fx, fy, fz, wx, wy, wz, name)

    # Show plots
    plt.show()

    # LOG WRITING

    log.info('---- Center of Gravity coordinates ----')
    log.info('------ Max Payload configuration ------')
    log.info('[x, y, z]: ' + str(bout.center_of_gravity))
    log.info('---------------------------------------')
    log.info('------- Zero Fuel configuration -------')
    log.info('[x, y, z]: ' + str(bout.cg_zfm))
    log.info('---------------------------------------')
    log.info('----- Zero Payload configuration ------')
    log.info('[x, y, z]: ' + str(bout.cg_zpm))
    log.info('---------------------------------------')
    log.info('---------- OEM configuration ----------')
    log.info('[x, y, z]: ' + str(bout.cg_oem))
    log.info('---------------------------------------')

    if bi.USER_CASE:
        log.info('---------- User configuration ---------')
        log.info('Chosen Fuel Percentage: ' + str(bi.F_PERC))
        log.info('Chosen Payload Percentage: ' + str(bi.P_PERC))
        log.info('[x, y, z]: ' + str(bout.cg_user))

    log.info('---------------------------------------')
    log.info('---------- Inertia Evaluation ---------')

    if bi.USER_EN_PLACEMENT:
        log.info('------------ Engine Inertia -----------')
        log.info('Roll moment, Ixx [kgm^2]: ' + str(int(round(bout.Ixxen))))
        log.info('Pitch moment, Iyy [kgm^2]: ' + str(int(round(bout.Iyyen))))
        log.info('Yaw moment, Izz [kgm^2]: ' + str(int(round(bout.Izzen))))
        log.info('Ixy moment [kgm^2]: ' + str(int(round(bout.Ixyen))))
        log.info('Iyz moment [kgm^2]: ' + str(int(round(bout.Iyzen))))
        log.info('Ixz moment [kgm^2]: ' + str(int(round(bout.Ixzen))))
        log.info('---------------------------------------')

    log.info('--------- Lumped mass Inertia ---------')
    log.info('------ Max Payload configuration ------')
    log.info('Roll moment, Ixx [kgm^2]: ' + str(bout.Ixx_lump))
    log.info('Pitch moment, Iyy [kgm^2]: ' + str(bout.Iyy_lump))
    log.info('Yaw moment, Izz [kgm^2]: ' + str(bout.Izz_lump))
    log.info('Ixy moment [kgm^2]: ' + str(bout.Ixy_lump))
    log.info('Iyz moment [kgm^2]: ' + str(bout.Iyz_lump))
    log.info('Ixz moment [kgm^2]: ' + str(bout.Ixz_lump))

    log.info('---------------------------------------')
    log.info('------- Zero Fuel configuration -------')
    log.info('Roll moment, Ixx [kgm^2]: ' + str(bout.Ixx_lump_zfm))
    log.info('Pitch moment, Iyy [kgm^2]: ' + str(bout.Iyy_lump_zfm))
    log.info('Yaw moment, Izz [kgm^2]: ' + str(bout.Izz_lump_zfm))
    log.info('Ixy moment [kgm^2]: ' + str(bout.Ixy_lump_zfm))
    log.info('Iyz moment [kgm^2]: ' + str(bout.Iyz_lump_zfm))
    log.info('Ixz moment [kgm^2]: ' + str(bout.Ixz_lump_zfm))

    log.info('---------------------------------------')
    log.info('------ Zero Payload configuration -----')
    log.info('Roll moment, Ixx [kgm^2]: ' + str(bout.Ixx_lump_zpm))
    log.info('Pitch moment, Iyy [kgm^2]: ' + str(bout.Iyy_lump_zpm))
    log.info('Yaw moment, Izz [kgm^2]: ' + str(bout.Izz_lump_zpm))
    log.info('Ixy moment [kgm^2]: ' + str(bout.Ixy_lump_zpm))
    log.info('Iyz moment [kgm^2]: ' + str(bout.Iyz_lump_zpm))
    log.info('Ixz moment [kgm^2]: ' + str(bout.Ixz_lump_zpm))

    log.info('---------------------------------------')
    log.info('---------- OEM configuration ----------')
    log.info('Roll moment, Ixx [kgm^2]: ' + str(bout.Ixx_lump_oem))
    log.info('Pitch moment, Iyy [kgm^2]: ' + str(bout.Iyy_lump_oem))
    log.info('Yaw moment, Izz [kgm^2]: ' + str(bout.Izz_lump_oem))
    log.info('Ixy moment [kgm^2]: ' + str(bout.Ixy_lump_oem))
    log.info('Iyz moment [kgm^2]: ' + str(bout.Iyz_lump_oem))
    log.info('Ixz moment [kgm^2]: ' + str(bout.Ixz_lump_oem))
    log.info('---------------------------------------')

    if bi.USER_CASE:
        log.info('---------- User configuration ---------')
        log.info('Roll moment, Ixx [kgm^2]: ' + str(bout.Ixx_lump_user))
        log.info('Pitch moment, Iyy [kgm^2]: ' + str(bout.Iyy_lump_user))
        log.info('Yaw moment, Izz [kgm^2]: ' + str(bout.Izz_lump_user))
        log.info('Ixy moment [kgm^2]: ' + str(bout.Ixy_lump_user))
        log.info('Iyz moment [kgm^2]: ' + str(bout.Iyz_lump_user))
        log.info('Ixz moment [kgm^2]: ' + str(bout.Ixz_lump_user))
        log.info('---------------------------------------')

    log.info('##  Uconventional Balance analysis succesfuly completed ##')


#=============================================================================
#    MAIN
#=============================================================================

if __name__ == '__main__':

    log.info('----- Start of ' + os.path.basename(__file__) + ' -----')

    cpacs_path = os.path.join(MODULE_DIR,'ToolInput','ToolInput.xml')
    cpacs_out_path = os.path.join(MODULE_DIR,'ToolOutput','ToolOutput.xml')

    mi.check_cpacs_input_requirements(cpacs_path)

    get_balance_unc_estimations(cpacs_path,cpacs_out_path)

    log.info('----- End of ' + os.path.basename(__file__) + ' -----')
