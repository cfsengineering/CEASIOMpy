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

| Author : Stefano Piccini
| Date of creation: 2018-09-27

TODO:
    * Use Pathlib and asolute path when refactor this module

"""

# =================================================================================================
#   IMPORTS
# =================================================================================================

import os
import shutil

import matplotlib.pyplot as plt
import numpy as np
from ceasiompy.BalanceConventional.func.AinFunc import getdatafromcpacs
from ceasiompy.BalanceConventional.func.AoutFunc import (
    cpacsbalanceupdate,
    outputbalancegen,
)
from ceasiompy.BalanceConventional.func.Cog.centerofgravity import (
    center_of_gravity_evaluation,
)
from ceasiompy.BalanceConventional.func.Inertia import lumpedmassesinertia
from ceasiompy.utils.ceasiompyutils import aircraft_name, call_main
from ceasiompy.utils.InputClasses.Conventional import balanceconvclass
from ceasiompy.utils.WB.ConvGeometry import geometry
from cpacspy.cpacspy import CPACS

from ceasiompy import log
from ceasiompy.BalanceConventional import MODULE_NAME

# =================================================================================================
#   FUNCTIONS
# =================================================================================================


def check_rounding(I1, I2):
    """Evaluation of the rounding digit for the inertia evaluation

    ARGUMENTS
    (float) I1 --Arg.: Yaw moment of inertia with Max Payload.
    (float) I2 --Arg.: Ixy moment of inertia with Max Payload.

    RETURN
    (int) rd  --Out.: Number of rounded digits.
    """
    ex = False
    rd = 0
    rd2 = 0
    while not ex:
        if round(I1, rd) == 0:
            ex = True
        else:
            rd -= 1
        if round(I2, rd2) != 0:
            rd2 -= 1
    rd += 5
    if rd2 > rd:
        rd = rd2

    return rd


# =================================================================================================
#    MAIN
# =================================================================================================


def main(cpacs: CPACS) -> None:
    """Function to estimate inertia value and CoF of an conventional aircraft.

    Function 'get_balance_unc_estimations' ...

    Source:
        * Reference paper or book, with author and date, see ...

    Args:
        cpacs_path (str): Path to CPACS file
        cpacs_path (str):Path to CPACS output file

    """
    cpacs_path = cpacs.cpacs_file

    # TODO: when refactor, use Pathlib and absolute path
    # Removing and recreating the ToolOutput folder.
    if os.path.exists("ToolOutput"):
        shutil.rmtree("ToolOutput")
    os.makedirs("ToolOutput")

    if not os.path.exists(cpacs_path):
        raise ValueError('No "ToolInput.xml" file in the ToolInput folder.')

    name = aircraft_name(cpacs_path)

    # shutil.copyfile(cpacs_path, cpacs_path)  # TODO: shoud not be like that
    newpath = "ToolOutput/" + name
    if not os.path.exists(newpath):
        os.makedirs(newpath)

    # BALANCE ANALSIS INPUTS
    bi = balanceconvclass.BalanceInputs()
    out = balanceconvclass.BalanceOutputs()
    mw = balanceconvclass.MassesWeights()
    (mw, bi) = getdatafromcpacs.get_data(mw, bi, cpacs_path)

    # BALANCE ANALYSIS

    log.info("------- Starting the balance analysis -------")
    log.info("---------- Aircraft: " + name + " -----------")
    F_PERC_MAXPASS = (mw.mass_fuel_maxpass / mw.mass_fuel_max) * 100

    # CENTER OF GRAVITY---------------------------------------------------------
    # ag = geometry.geometry_eval(cpacs_path, name)
    # TODO: get CPACS object
    ag = geometry.AircraftGeometry()
    ag.fuse_geom_eval(cpacs)
    ag.wing_geom_eval(cpacs)
    ag.produce_output_txt()

    log.info("------- Center of Gravity coordinates -------")
    log.info("--------- Max Payload configuration ---------")
    (out.center_of_gravity, mass_seg_i, _) = center_of_gravity_evaluation(
        F_PERC_MAXPASS, 100, ag.cabin_seg, ag, mw, bi.WING_MOUNTED
    )
    log.info("[x, y, z] = " + str(out.center_of_gravity))
    log.info("---------- Zero Fuel configuration ----------")
    (out.cg_zfm, ms_zfm, _) = center_of_gravity_evaluation(
        0, 100, ag.cabin_seg, ag, mw, bi.WING_MOUNTED
    )
    log.info("[x, y, z] = " + str(out.cg_zfm))
    log.info("-------- Zero Payload configuration ---------")
    (out.cg_zpm, ms_zpm, _) = center_of_gravity_evaluation(
        100, 0, ag.cabin_seg, ag, mw, bi.WING_MOUNTED
    )
    log.info("[x, y, z] = " + str(out.cg_zpm))
    log.info("------------- OEM configuration -------------")
    (out.cg_oem, ms_oem, _) = center_of_gravity_evaluation(
        0, 0, ag.cabin_seg, ag, mw, bi.WING_MOUNTED
    )
    log.info("[x, y, z] = " + str(out.cg_oem))
    if bi.USER_CASE:
        if bi.P_PERC < 0 or bi.F_PERC < 0:
            raise Exception("Error, F_PERC and P_PERC can" + " not be zero or negative.")
        if (
            mw.mass_fuel_maxpass * (bi.F_PERC / 100.0) + mw.mass_payload * (bi.P_PERC / 100.0)
        ) > mw.mass_fuel_maxpass + mw.mass_payload:
            log.warning(
                "Exceeding maximum fuel amount with the"
                + "chosen payload mass,"
                + "fuel mass automatically reduced"
            )
            bi.F_PERC = 1 + ((mw.mass_payload / mw.mass_fuel_maxpass) * (1 - (bi.P_PERC / 100.0)))
            log.warning("FUEL percentage: " + str(bi.F_PERC))
        log.info("------------- User configuration ------------")
        (out.cg_user, ms_user, _) = center_of_gravity_evaluation(
            bi.F_PERC * 100, bi.P_PERC, ag.cabin_seg, ag, mw, bi.WING_MOUNTED
        )

    # MOMENT OF INERTIA
    log.info("------------- Inertia Evaluation ------------")
    log.info("------------ Lumped mass Inertia ------------")
    log.info("--------- Max Payload configuration ---------")
    (_, _, _, Ixxf, Iyyf, Izzf, Ixyf, Iyzf, Ixzf) = lumpedmassesinertia.fuselage_inertia(
        bi.SPACING_FUSE, out.center_of_gravity, mass_seg_i, ag, cpacs_path
    )
    (_, _, _, Ixxw, Iyyw, Izzw, Ixyw, Iyzw, Ixzw) = lumpedmassesinertia.wing_inertia(
        bi.WPP, bi.SPACING_WING, out.center_of_gravity, mass_seg_i, ag, cpacs_path
    )

    rd = check_rounding(Ixxf + Ixxw, Iyzf + Iyzw)
    out.Ixx_lump = round(Ixxf + Ixxw, rd)
    out.Iyy_lump = round(Iyyf + Iyyw, rd)
    out.Izz_lump = round(Izzf + Izzw, rd)
    out.Ixy_lump = round(Ixyf + Ixyw, rd)
    out.Iyz_lump = round(Iyzf + Iyzw, rd)
    out.Ixz_lump = round(Ixzf + Ixzw, rd)

    log.info("---------- Zero Fuel configuration ----------")
    (_, _, _, Ixxf2, Iyyf2, Izzf2, Ixyf2, Iyzf2, Ixzf2) = lumpedmassesinertia.fuselage_inertia(
        bi.SPACING_FUSE, out.cg_zfm, ms_zfm, ag, cpacs_path
    )
    (_, _, _, Ixxw2, Iyyw2, Izzw2, Ixyw2, Iyzw2, Ixzw2) = lumpedmassesinertia.wing_inertia(
        bi.WPP, bi.SPACING_WING, out.cg_zfm, ms_zfm, ag, cpacs_path
    )

    out.Ixx_lump_zfm = round(Ixxf2 + Ixxw2, rd)
    out.Iyy_lump_zfm = round(Iyyf2 + Iyyw2, rd)
    out.Izz_lump_zfm = round(Izzf2 + Izzw2, rd)
    out.Ixy_lump_zfm = round(Ixyf2 + Ixyw2, rd)
    out.Iyz_lump_zfm = round(Iyzf2 + Iyzw2, rd)
    out.Ixz_lump_zfm = round(Ixzf2 + Ixzw2, rd)

    log.info("--------- Zero Payload configuration --------")
    (_, _, _, Ixxf3, Iyyf3, Izzf3, Ixyf3, Iyzf3, Ixzf3) = lumpedmassesinertia.fuselage_inertia(
        bi.SPACING_FUSE, out.cg_zpm, ms_zpm, ag, cpacs_path
    )
    (_, _, _, Ixxw3, Iyyw3, Izzw3, Ixyw3, Iyzw3, Ixzw3) = lumpedmassesinertia.wing_inertia(
        bi.WPP, bi.SPACING_WING, out.cg_zpm, ms_zpm, ag, cpacs_path
    )

    out.Ixx_lump_zpm = round(Ixxf3 + Ixxw3, rd)
    out.Iyy_lump_zpm = round(Iyyf3 + Iyyw3, rd)
    out.Izz_lump_zpm = round(Izzf3 + Izzw3, rd)
    out.Ixy_lump_zpm = round(Ixyf3 + Ixyw3, rd)
    out.Iyz_lump_zpm = round(Iyzf3 + Iyzw3, rd)
    out.Ixz_lump_zpm = round(Ixzf3 + Ixzw3, rd)

    log.info("------------- OEM configuration -------------")
    (_, _, _, Ixxf4, Iyyf4, Izzf4, Ixyf4, Iyzf4, Ixzf4) = lumpedmassesinertia.fuselage_inertia(
        bi.SPACING_FUSE, out.cg_oem, ms_oem, ag, cpacs_path
    )
    (_, _, _, Ixxw4, Iyyw4, Izzw4, Ixyw4, Iyzw4, Ixzw4) = lumpedmassesinertia.wing_inertia(
        bi.WPP, bi.SPACING_WING, out.cg_oem, ms_oem, ag, cpacs_path
    )

    out.Ixx_lump_oem = round(Ixxf4 + Ixxw4, rd)
    out.Iyy_lump_oem = round(Iyyf4 + Iyyw4, rd)
    out.Izz_lump_oem = round(Izzf4 + Izzw4, rd)
    out.Ixy_lump_oem = round(Ixyf4 + Ixyw4, rd)
    out.Iyz_lump_oem = round(Iyzf4 + Iyzw4, rd)
    out.Ixz_lump_oem = round(Ixzf4 + Ixzw4, rd)

    if bi.USER_CASE:
        log.info("------------- User configuration ------------")
        (
            _,
            _,
            _,
            Ixxfu,
            Iyyfu,
            Izzfu,
            Ixyfu,
            Iyzfu,
            Ixzfu,
        ) = lumpedmassesinertia.fuselage_inertia(
            bi.SPACING_FUSE, out.cg_user, ms_user, ag, cpacs_path
        )
        (_, _, _, Ixxwu, Iyywu, Izzwu, Ixywu, Iyzwu, Ixzwu) = lumpedmassesinertia.wing_inertia(
            bi.WPP, bi.SPACING_WING, out.cg_user, ms_user, ag, cpacs_path
        )

        out.Ixx_lump_user = round(Ixxfu + Ixxwu, rd)
        out.Iyy_lump_user = round(Iyyfu + Iyywu, rd)
        out.Izz_lump_user = round(Izzfu + Izzwu, rd)
        out.Ixy_lump_user = round(Ixyfu + Ixywu, rd)
        out.Iyz_lump_user = round(Iyzfu + Iyzwu, rd)
        out.Ixz_lump_user = round(Ixzfu + Ixzwu, rd)

    # OUTPUT WRITING

    log.info("Generating output text file")
    outputbalancegen.output_txt(out, mw, bi, name)

    # CPACS WRITING
    cpacsbalanceupdate.cpacs_mbd_update(out, mw, bi, np.sum(ms_zpm), cpacs_path)

    # PLOTS
    # Aircraft Cog Plot
    log.info("Generating aircraft center of gravity plot (.png)")
    outputbalancegen.aircraft_cog_plot(out.center_of_gravity, ag, name)

    # Aircraft Nodes
    # Uncomment to plot aircraft nodes.
    # log.info('--- Generating aircraft nodes plot (.png) ---')
    # outputbalancegen.aircraft_nodes_plot(fx, fy, fz, wx, wy, wz, name)

    # Show plots
    plt.show()

    # LOG WRITING
    log.info("---- Center of Gravity coordinates ----")
    log.info("------ Max Payload configuration ------")
    log.info("[x, y, z]: " + str(out.center_of_gravity))
    log.info("---------------------------------------")
    log.info("------- Zero Fuel configuration -------")
    log.info("[x, y, z]: " + str(out.cg_zfm))
    log.info("---------------------------------------")
    log.info("----- Zero Payload configuration ------")
    log.info("[x, y, z]: " + str(out.cg_zpm))
    log.info("---------------------------------------")
    log.info("---------- OEM configuration ----------")
    log.info("[x, y, z]: " + str(out.cg_oem))
    log.info("---------------------------------------")
    if bi.USER_CASE:
        log.info("---------- User configuration ---------")
        log.info("Chosen Fuel Percentage: " + str(bi.F_PERC))
        log.info("Chosen Payload Percentage: " + str(bi.P_PERC))
        log.info("[x, y, z]: " + str(out.cg_user))
    log.info("---------------------------------------")
    log.info("---------- Inertia Evaluation ---------")
    log.info("--------- Lumped mass Inertia ---------")
    log.info("------ Max Payload configuration ------")
    log.info("Roll moment, Ixx [kgm^2]: " + str(out.Ixx_lump))
    log.info("Pitch moment, Iyy [kgm^2]: " + str(out.Iyy_lump))
    log.info("Yaw moment, Izz [kgm^2]: " + str(out.Izz_lump))
    log.info("Ixy moment [kgm^2]: " + str(out.Ixy_lump))
    log.info("Iyz moment [kgm^2]: " + str(out.Iyz_lump))
    log.info("Ixz moment [kgm^2]: " + str(out.Ixz_lump))
    log.info("---------------------------------------")
    log.info("------- Zero Fuel configuration -------")
    log.info("Roll moment, Ixx [kgm^2]: " + str(out.Ixx_lump_zfm))
    log.info("Pitch moment, Iyy [kgm^2]: " + str(out.Iyy_lump_zfm))
    log.info("Yaw moment, Izz [kgm^2]: " + str(out.Izz_lump_zfm))
    log.info("Ixy moment [kgm^2]: " + str(out.Ixy_lump_zfm))
    log.info("Iyz moment [kgm^2]: " + str(out.Iyz_lump_zfm))
    log.info("Ixz moment [kgm^2]: " + str(out.Ixz_lump_zfm))
    log.info("---------------------------------------")
    log.info("------ Zero Payload configuration -----")
    log.info("Roll moment, Ixx [kgm^2]: " + str(out.Ixx_lump_zpm))
    log.info("Pitch moment, Iyy [kgm^2]: " + str(out.Iyy_lump_zpm))
    log.info("Yaw moment, Izz [kgm^2]: " + str(out.Izz_lump_zpm))
    log.info("Ixy moment [kgm^2]: " + str(out.Ixy_lump_zpm))
    log.info("Iyz moment [kgm^2]: " + str(out.Iyz_lump_zpm))
    log.info("Ixz moment [kgm^2]: " + str(out.Ixz_lump_zpm))
    log.info("---------------------------------------")
    log.info("---------- OEM configuration ----------")
    log.info("Roll moment, Ixx [kgm^2]: " + str(out.Ixx_lump_oem))
    log.info("Pitch moment, Iyy [kgm^2]: " + str(out.Iyy_lump_oem))
    log.info("Yaw moment, Izz [kgm^2]: " + str(out.Izz_lump_oem))
    log.info("Ixy moment [kgm^2]: " + str(out.Ixy_lump_oem))
    log.info("Iyz moment [kgm^2]: " + str(out.Iyz_lump_oem))
    log.info("Ixz moment [kgm^2]: " + str(out.Ixz_lump_oem))
    log.info("---------------------------------------")
    if bi.USER_CASE:
        log.info("---------- User configuration ---------")
        log.info("Roll moment, Ixx [kgm^2]: " + str(out.Ixx_lump_user))
        log.info("Pitch moment, Iyy [kgm^2]: " + str(out.Iyy_lump_user))
        log.info("Yaw moment, Izz [kgm^2]: " + str(out.Izz_lump_user))
        log.info("Ixy moment [kgm^2]: " + str(out.Ixy_lump_user))
        log.info("Iyz moment [kgm^2]: " + str(out.Iyz_lump_user))
        log.info("Ixz moment [kgm^2]: " + str(out.Ixz_lump_user))
        log.info("---------------------------------------")

    log.info("############## Balance estimation completed ##############")


if __name__ == "__main__":
    call_main(main, MODULE_NAME)
