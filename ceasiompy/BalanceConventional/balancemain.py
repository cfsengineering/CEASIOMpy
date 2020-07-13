"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed for CFS ENGINEERING, 1015 Lausanne, Switzerland

Balance main module for preliminary design on conventional
aircraft, it evaluates:

 * The centre of gravity;
 * The Ixx, Iyy, Izz moments of inertia.

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
import matplotlib.pyplot as plt

from ceasiompy.utils.InputClasses.Conventional import balanceconvclass

from ceasiompy.BalanceConventional.func.Cog.centerofgravity import center_of_gravity_evaluation
from ceasiompy.BalanceConventional.func.Inertia import lumpedmassesinertia
from ceasiompy.BalanceConventional.func.AoutFunc import outputbalancegen
from ceasiompy.BalanceConventional.func.AoutFunc import cpacsbalanceupdate
from ceasiompy.BalanceConventional.func.AinFunc import getdatafromcpacs


from ceasiompy.utils.cpacsfunctions import aircraft_name
from ceasiompy.utils.WB.ConvGeometry import geometry
import ceasiompy.utils.moduleinterfaces as mi

from ceasiompy.utils.ceasiomlogger import get_logger

log = get_logger(__file__.split('.')[0])

MODULE_DIR = os.path.dirname(os.path.abspath(__file__))

#=============================================================================
#   CLASSES
#=============================================================================

"""All classes are defined inside the InputClasses/Conventional"""


#=============================================================================
#   FUNCTIONS
#=============================================================================

def check_rounding(I, I2):
    """Evaluation of the rounding digit for the inertia evaluation

       ARGUMENTS
       (float) I --Arg.: Yaw moment of inertia with Max Payload.
       (float) I --Arg.: Ixy moment of inertia with Max Payload.

       RETURN
       (int) rd  --Out.: Number of rounded digits.
    """
    ex = False
    rd = 0
    rd2 = 0
    while not ex:
        if round(I,rd) == 0:
            ex = True
        else:
            rd -= 1
        if round(I2,rd2) != 0:
            rd2 -= 1
    rd += 5
    if rd2 > rd:
        rd = rd2

    return(rd)


def get_balance_estimations(cpacs_path, cpacs_out_path):
    """Function to estimate inertia value and CoF of an conventional aircraft.

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

    # BALANCE ANALSIS INPUTS
    bi = balanceconvclass.BalanceInputs()
    out = balanceconvclass.BalanceOutputs()
    mw = balanceconvclass.MassesWeights()
    (mw, bi) = getdatafromcpacs.get_data(mw, bi, cpacs_out_path)

    # BALANCE ANALYSIS

    log.info('------- Starting the balance analysis -------')
    log.info('---------- Aircraft: ' + name + ' -----------')
    F_PERC_MAXPASS = (mw.mass_fuel_maxpass/mw.mass_fuel_max) * 100

    # CENTER OF GRAVITY---------------------------------------------------------
    ag = geometry.geometry_eval(cpacs_out_path, name)

    log.info('------- Center of Gravity coordinates -------')
    log.info('--------- Max Payload configuration ---------')
    (out.center_of_gravity, mass_seg_i, airplane_centers_segs)\
            = center_of_gravity_evaluation(F_PERC_MAXPASS, 100, ag.cabin_seg,\
                                           ag, mw, bi.WING_MOUNTED)
    log.info('[x, y, z] = ' + str(out.center_of_gravity))
    log.info('---------- Zero Fuel configuration ----------')
    (out.cg_zfm, ms_zfm, airplane_centers_segs)\
            = center_of_gravity_evaluation(0, 100, ag.cabin_seg,\
                                           ag, mw, bi.WING_MOUNTED)
    log.info('[x, y, z] = ' + str(out.cg_zfm))
    log.info('-------- Zero Payload configuration ---------')
    (out.cg_zpm, ms_zpm, airplane_centers_segs)\
            = center_of_gravity_evaluation(100, 0, ag.cabin_seg,\
                                           ag, mw, bi.WING_MOUNTED)
    log.info('[x, y, z] = ' + str(out.cg_zpm))
    log.info('------------- OEM configuration -------------')
    (out.cg_oem, ms_oem, airplane_centers_segs)\
            = center_of_gravity_evaluation(0, 0, ag.cabin_seg,\
                                           ag, mw, bi.WING_MOUNTED)
    log.info('[x, y, z] = ' + str(out.cg_oem))
    if bi.USER_CASE == True:
        if bi.P_PERC < 0 or bi.F_PERC < 0:
            raise Exception('Error, F_PERC and P_PERC can'\
                            + ' not be zero or negative.')
        if (mw.mass_fuel_maxpass*(bi.F_PERC/100.0)\
            + mw.mass_payload*(bi.P_PERC/100.0))\
            > mw.mass_fuel_maxpass + mw.mass_payload:
            log.warning('Exceeding maximum fuel amount with the'\
                        + 'chosen payload mass,'\
                        + 'fuel mass automatically reduced')
            bi.F_PERC = 1 + ((mw.mass_payload/mw.mass_fuel_maxpass)\
                   * (1-(bi.P_PERC/100.0)))
            log.warning('FUEL percentage: ' + str(bi.F_PERC))
        log.info('------------- User configuration ------------')
        (out.cg_user, ms_user, airplane_centers_segs)\
                 = center_of_gravity_evaluation(bi.F_PERC*100, bi.P_PERC,\
                         ag.cabin_seg, ag, mw, bi.WING_MOUNTED)

    # MOMENT OF INERTIA
    center_of_gravity_seg=[]
    mass_component=[]
    log.info('------------- Inertia Evaluation ------------')
    log.info('------------ Lumped mass Inertia ------------')
    log.info('--------- Max Payload configuration ---------')
    (fx, fy, fz, Ixxf, Iyyf, Izzf, Ixyf, Iyzf, Ixzf)\
            = lumpedmassesinertia.fuselage_inertia(\
                bi.SPACING_FUSE, out.center_of_gravity, mass_seg_i,\
                ag, cpacs_out_path)
    (wx, wy, wz, Ixxw, Iyyw, Izzw, Ixyw, Iyzw, Ixzw)\
            = lumpedmassesinertia.wing_inertia(\
                bi.WPP, bi.SPACING_WING, out.center_of_gravity,\
                mass_seg_i, ag, cpacs_out_path)

    rd = check_rounding(Ixxf + Ixxw, Iyzf + Iyzw)
    out.Ixx_lump = round(Ixxf + Ixxw,rd)
    out.Iyy_lump = round(Iyyf + Iyyw,rd)
    out.Izz_lump = round(Izzf + Izzw,rd)
    out.Ixy_lump = round(Ixyf + Ixyw,rd)
    out.Iyz_lump = round(Iyzf + Iyzw,rd)
    out.Ixz_lump = round(Ixzf + Ixzw,rd)

    log.info('---------- Zero Fuel configuration ----------')
    (fx, fy, fz, Ixxf2, Iyyf2, Izzf2, Ixyf2, Iyzf2, Ixzf2)\
            = lumpedmassesinertia.fuselage_inertia(bi.SPACING_FUSE,\
                out.cg_zfm, ms_zfm, ag, cpacs_out_path)
    (wx, wy, wz, Ixxw2, Iyyw2, Izzw2, Ixyw2, Iyzw2, Ixzw2)\
            = lumpedmassesinertia.wing_inertia(bi.WPP, bi.SPACING_WING,\
                out.cg_zfm, ms_zfm, ag, cpacs_out_path)

    out.Ixx_lump_zfm = round(Ixxf2 + Ixxw2,rd)
    out.Iyy_lump_zfm = round(Iyyf2 + Iyyw2,rd)
    out.Izz_lump_zfm = round(Izzf2 + Izzw2,rd)
    out.Ixy_lump_zfm = round(Ixyf2 + Ixyw2,rd)
    out.Iyz_lump_zfm = round(Iyzf2 + Iyzw2,rd)
    out.Ixz_lump_zfm = round(Ixzf2 + Ixzw2,rd)

    log.info('--------- Zero Payload configuration --------')
    (fx, fy, fz, Ixxf3, Iyyf3, Izzf3, Ixyf3, Iyzf3, Ixzf3)\
            = lumpedmassesinertia.fuselage_inertia(bi.SPACING_FUSE,\
                out.cg_zpm, ms_zpm, ag, cpacs_out_path)
    (wx, wy, wz, Ixxw3, Iyyw3, Izzw3, Ixyw3, Iyzw3, Ixzw3)\
            = lumpedmassesinertia.wing_inertia(bi.WPP, bi.SPACING_WING,\
                out.cg_zpm, ms_zpm, ag, cpacs_out_path)

    out.Ixx_lump_zpm = round(Ixxf3 + Ixxw3,rd)
    out.Iyy_lump_zpm = round(Iyyf3 + Iyyw3,rd)
    out.Izz_lump_zpm = round(Izzf3 + Izzw3,rd)
    out.Ixy_lump_zpm = round(Ixyf3 + Ixyw3,rd)
    out.Iyz_lump_zpm = round(Iyzf3 + Iyzw3,rd)
    out.Ixz_lump_zpm = round(Ixzf3 + Ixzw3,rd)

    log.info('------------- OEM configuration -------------')
    (fx, fy, fz, Ixxf4, Iyyf4, Izzf4, Ixyf4, Iyzf4, Ixzf4)\
            = lumpedmassesinertia.fuselage_inertia(bi.SPACING_FUSE,\
                out.cg_oem, ms_oem, ag, cpacs_out_path)
    (wx, wy, wz, Ixxw4, Iyyw4, Izzw4, Ixyw4, Iyzw4, Ixzw4)\
            = lumpedmassesinertia.wing_inertia(bi.WPP, bi.SPACING_WING,\
                out.cg_oem, ms_oem, ag, cpacs_out_path)

    out.Ixx_lump_oem = round(Ixxf4 + Ixxw4,rd)
    out.Iyy_lump_oem = round(Iyyf4 + Iyyw4,rd)
    out.Izz_lump_oem = round(Izzf4 + Izzw4,rd)
    out.Ixy_lump_oem = round(Ixyf4 + Ixyw4,rd)
    out.Iyz_lump_oem = round(Iyzf4 + Iyzw4,rd)
    out.Ixz_lump_oem = round(Ixzf4 + Ixzw4,rd)

    if bi.USER_CASE:
        log.info('------------- User configuration ------------')
        (fx, fy, fz, Ixxfu, Iyyfu, Izzfu, Ixyfu, Iyzfu, Ixzfu)\
                = lumpedmassesinertia.fuselage_inertia(bi.SPACING_FUSE,\
                    out.cg_user, ms_user, ag, cpacs_out_path)
        (wx, wy, wz, Ixxwu, Iyywu, Izzwu, Ixywu, Iyzwu, Ixzwu)\
                = lumpedmassesinertia.wing_inertia(bi.WPP, bi.SPACING_WING,\
                    out.cg_user, ms_user, ag, cpacs_out_path)

        out.Ixx_lump_user = round(Ixxfu + Ixxwu,rd)
        out.Iyy_lump_user = round(Iyyfu + Iyywu,rd)
        out.Izz_lump_user = round(Izzfu + Izzwu,rd)
        out.Ixy_lump_user = round(Ixyfu + Ixywu,rd)
        out.Iyz_lump_user = round(Iyzfu + Iyzwu,rd)
        out.Ixz_lump_user = round(Ixzfu + Ixzwu,rd)


    # OUTPUT WRITING

    log.info('-------- Generating output text file --------')
    outputbalancegen.output_txt(out, mw, bi, name)

    # CPACS WRITING
    cpacsbalanceupdate.cpacs_mbd_update(out, mw, bi, np.sum(ms_zpm), cpacs_out_path)


    # PLOTS
    # Aircraft Cog Plot
    log.info('--- Generating aircraft center of gravity plot (.png) ---')
    outputbalancegen.aircraft_cog_plot(out.center_of_gravity, ag, name)

    # Aircraft Nodes
    # Uncomment to plot aircraft nodes.
    #log.info('--- Generating aircraft nodes plot (.png) ---')
    #outputbalancegen.aircraft_nodes_plot(fx, fy, fz, wx, wy, wz, name)

    # Show plots
    plt.show()

    # LOG WRITING
    log.info('---- Center of Gravity coordinates ----')
    log.info('------ Max Payload configuration ------')
    log.info('[x, y, z]: ' + str(out.center_of_gravity))
    log.info('---------------------------------------')
    log.info('------- Zero Fuel configuration -------')
    log.info('[x, y, z]: ' + str(out.cg_zfm))
    log.info('---------------------------------------')
    log.info('----- Zero Payload configuration ------')
    log.info('[x, y, z]: ' + str(out.cg_zpm))
    log.info('---------------------------------------')
    log.info('---------- OEM configuration ----------')
    log.info('[x, y, z]: ' + str(out.cg_oem))
    log.info('---------------------------------------')
    if bi.USER_CASE:
        log.info('---------- User configuration ---------')
        log.info('Chosen Fuel Percentage: ' + str(bi.F_PERC))
        log.info('Chosen Payload Percentage: ' + str(bi.P_PERC))
        log.info('[x, y, z]: ' + str(out.cg_user))
    log.info('---------------------------------------')
    log.info('---------- Inertia Evaluation ---------')
    log.info('--------- Lumped mass Inertia ---------')
    log.info('------ Max Payload configuration ------')
    log.info('Roll moment, Ixx [kgm^2]: ' + str(out.Ixx_lump))
    log.info('Pitch moment, Iyy [kgm^2]: ' + str(out.Iyy_lump))
    log.info('Yaw moment, Izz [kgm^2]: ' + str(out.Izz_lump))
    log.info('Ixy moment [kgm^2]: ' + str(out.Ixy_lump))
    log.info('Iyz moment [kgm^2]: ' + str(out.Iyz_lump))
    log.info('Ixz moment [kgm^2]: ' + str(out.Ixz_lump))
    log.info('---------------------------------------')
    log.info('------- Zero Fuel configuration -------')
    log.info('Roll moment, Ixx [kgm^2]: ' + str(out.Ixx_lump_zfm))
    log.info('Pitch moment, Iyy [kgm^2]: ' + str(out.Iyy_lump_zfm))
    log.info('Yaw moment, Izz [kgm^2]: ' + str(out.Izz_lump_zfm))
    log.info('Ixy moment [kgm^2]: ' + str(out.Ixy_lump_zfm))
    log.info('Iyz moment [kgm^2]: ' + str(out.Iyz_lump_zfm))
    log.info('Ixz moment [kgm^2]: ' + str(out.Ixz_lump_zfm))
    log.info('---------------------------------------')
    log.info('------ Zero Payload configuration -----')
    log.info('Roll moment, Ixx [kgm^2]: ' + str(out.Ixx_lump_zpm))
    log.info('Pitch moment, Iyy [kgm^2]: ' + str(out.Iyy_lump_zpm))
    log.info('Yaw moment, Izz [kgm^2]: ' + str(out.Izz_lump_zpm))
    log.info('Ixy moment [kgm^2]: ' + str(out.Ixy_lump_zpm))
    log.info('Iyz moment [kgm^2]: ' + str(out.Iyz_lump_zpm))
    log.info('Ixz moment [kgm^2]: ' + str(out.Ixz_lump_zpm))
    log.info('---------------------------------------')
    log.info('---------- OEM configuration ----------')
    log.info('Roll moment, Ixx [kgm^2]: ' + str(out.Ixx_lump_oem))
    log.info('Pitch moment, Iyy [kgm^2]: ' + str(out.Iyy_lump_oem))
    log.info('Yaw moment, Izz [kgm^2]: ' + str(out.Izz_lump_oem))
    log.info('Ixy moment [kgm^2]: ' + str(out.Ixy_lump_oem))
    log.info('Iyz moment [kgm^2]: ' + str(out.Iyz_lump_oem))
    log.info('Ixz moment [kgm^2]: ' + str(out.Ixz_lump_oem))
    log.info('---------------------------------------')
    if bi.USER_CASE:
        log.info('---------- User configuration ---------')
        log.info('Roll moment, Ixx [kgm^2]: ' + str(out.Ixx_lump_user))
        log.info('Pitch moment, Iyy [kgm^2]: ' + str(out.Iyy_lump_user))
        log.info('Yaw moment, Izz [kgm^2]: ' + str(out.Izz_lump_user))
        log.info('Ixy moment [kgm^2]: ' + str(out.Ixy_lump_user))
        log.info('Iyz moment [kgm^2]: ' + str(out.Iyz_lump_user))
        log.info('Ixz moment [kgm^2]: ' + str(out.Ixz_lump_user))
        log.info('---------------------------------------')

    log.info('############## Balance estimation completed ##############')



#=============================================================================
#    MAIN
#=============================================================================

if __name__ == '__main__':

    log.info('----- Start of ' + os.path.basename(__file__) + ' -----')

    cpacs_path = os.path.join(MODULE_DIR,'ToolInput','ToolInput.xml')
    cpacs_out_path = os.path.join(MODULE_DIR,'ToolOutput','ToolOutput.xml')

    mi.check_cpacs_input_requirements(cpacs_path)

    get_balance_estimations(cpacs_path,cpacs_out_path)

    log.info('----- End of ' + os.path.basename(__file__) + ' -----')
