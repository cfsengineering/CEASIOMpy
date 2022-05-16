"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Extract results from SU2 calculations

Python version: >=3.7

| Author: Aidan Jungo
| Creation: 2019-10-02

TODO:

    * Saving for Control surface deflections
    * Solve other small issues (see TODO)

"""

# =================================================================================================
#   IMPORTS
# =================================================================================================

import os
from pathlib import Path

from ceasiompy.SU2Run.func.extractloads import extract_loads
from ceasiompy.SU2Run.func.su2utils import get_su2_forces
from ceasiompy.utils.ceasiomlogger import get_logger
from ceasiompy.utils.commonnames import SU2_FORCES_BREAKDOWN_NAME
from ceasiompy.utils.commonxpath import (
    SU2_AEROMAP_UID_XPATH,
    SU2_EXTRACT_LOAD_XPATH,
    SU2_FIXED_CL_XPATH,
    SU2_ROTATION_RATE_XPATH,
    WETTED_AREA_XPATH,
)
from cpacspy.cpacsfunctions import create_branch, get_value, get_value_or_default
from cpacspy.cpacspy import CPACS
from cpacspy.utils import COEFS

log = get_logger()


# =================================================================================================
#   CLASSES
# =================================================================================================


# =================================================================================================
#   FUNCTIONS
# =================================================================================================


def get_wetted_area(wkdir):
    """Function get the wetted area calculated by SU2

    Function 'get_wetted_area' finds the SU2 logfile and returns the wetted
    area value previously calculated by SU2.

    Args:
        wkdir (str): Path to the working directory

    Returns:
        wetted_area (float): Wetted area calculated by SU2 [m^2]

    """

    wetted_area = None
    su2_logfile_path = None

    # Find a logfile in wkdir
    for (root, _, files) in os.walk(wkdir):
        for file in files:
            if file == "logfile_SU2_CFD.log":
                su2_logfile_path = Path(root, file)
                break

    if su2_logfile_path is None:
        log.warning("No logfile has been found for working directory!")

    # Read the logfile
    with open(su2_logfile_path) as f:
        for line in f.readlines():
            if "Wetted area =" in line:
                wetted_area = float(line.split(" ")[3])
                break

    if wetted_area is None:
        # raise ValueError('No value has been found for the wetted area!')
        log.warning("No value has been found for the wetted area!")
        return 0

    else:
        log.info("Wetted area value has been found and is equal to " + str(wetted_area) + " [m^2]")
        return wetted_area


# This function should be modified maybe merge with get_aoa
def get_efficiency_and_aoa(force_path):
    """Function to get efficiency (CL/CD) and angle of attack (AoA)

    Function 'get_efficiency_and_aoa' search fot the efficiency (CL/CD) and
    the Angle of Attack (AoA) in the results file (forces_breakdown.dat)

    Args:
        force_path (str): Path to the Force Breakdown result file

    Returns:
        cl_cd (float):  CL/CD ratio [-]
        aoa (float):    Angle of Attack [deg]

    """

    cl_cd = None
    aoa = None

    with open(force_path) as f:
        for line in f.readlines():
            if "CL/CD" in line:
                cl_cd = float(line.split(":")[1].split("|")[0])
                continue

            if "Angle of attack (AoA):" in line:
                aoa = float(line.split("Angle of attack (AoA):")[1].split("deg,")[0].strip())
                continue

            if cl_cd and aoa:
                break

    if cl_cd is None or aoa is None:
        raise ValueError("No value has been found for the CL/CD ratio or AoA!")
    else:
        log.info("CL/CD ratio has been found and is equal to: " + str(cl_cd) + "[-]")
        log.info("AoA has been found and is equal to: " + str(aoa) + "[-]")

        return cl_cd, aoa


def get_su2_results(cpacs_path, cpacs_out_path, wkdir):
    """Function to write SU2 results in a CPACS file.

    Function 'get_su2_results' get available results from the latest SU2
    calculation and put it at the correct place in the CPACS file.

    '/cpacs/vehicles/aircraft/model/analyses/aeroPerformance/aerpMap[n]/aeroPerformanceMap'

    Args:
        cpacs_path (Path): Path to input CPACS file
        cpacs_out_path (Path): Path to output CPACS file
        wkdir (Path): Path to the working directory

    """

    cpacs = CPACS(str(cpacs_path))

    if not wkdir.exists():
        raise OSError(f"The working directory : {wkdir} does not exit!")

    # Get and save Wetted area
    wetted_area = get_wetted_area(wkdir)
    create_branch(cpacs.tixi, WETTED_AREA_XPATH)
    cpacs.tixi.updateDoubleElement(WETTED_AREA_XPATH, wetted_area, "%g")

    # Get fixed_cl option
    fixed_cl = get_value_or_default(cpacs.tixi, SU2_FIXED_CL_XPATH, "NO")

    # Get aeroMap uid
    if fixed_cl == "YES":
        aeromap_uid = "aeroMap_fixedCL_SU2"
    elif fixed_cl == "NO":
        aeromap_uid = get_value(cpacs.tixi, SU2_AEROMAP_UID_XPATH)
    else:
        raise ValueError("The value for fixed_cl is not valid! Should be YES or NO")

    aeromap = cpacs.get_aeromap_by_uid(aeromap_uid)

    alt_list = aeromap.get("altitude").tolist()
    mach_list = aeromap.get("machNumber").tolist()
    aoa_list = aeromap.get("angleOfAttack").tolist()
    aos_list = aeromap.get("angleOfSideslip").tolist()

    case_dir_list = [case_dir for case_dir in wkdir.iterdir() if "Case" in case_dir.name]

    for config_dir in sorted(case_dir_list):

        if not config_dir.is_dir():
            continue

        baseline_coef = True

        case_nb = int(config_dir.name.split("_")[0].split("Case")[1])

        aoa = aoa_list[case_nb]
        aos = aos_list[case_nb]
        mach = mach_list[case_nb]
        alt = alt_list[case_nb]

        force_file_path = Path(config_dir, SU2_FORCES_BREAKDOWN_NAME)
        if not force_file_path.exists():
            raise OSError("No result force file have been found!")

        if fixed_cl == "YES":
            cl_cd, aoa = get_efficiency_and_aoa(force_file_path)

            # Replace aoa with the with the value from fixed cl calculation
            aeromap.df.loc[0, ["angleOfAttack"]] = aoa

            # Save cl/cd found during the fixed CL calculation
            # TODO: maybe save cl/cd somewhere else
            lDRatio_xpath = "/cpacs/toolspecific/CEASIOMpy/ranges/lDRatio"
            create_branch(cpacs.tixi, lDRatio_xpath)
            cpacs.tixi.updateDoubleElement(lDRatio_xpath, cl_cd, "%g")

        cl, cd, cs, cmd, cms, cml, velocity = get_su2_forces(force_file_path)

        # Damping derivatives
        rotation_rate = get_value_or_default(cpacs.tixi, SU2_ROTATION_RATE_XPATH, -1.0)
        ref_len = cpacs.aircraft.ref_lenght
        adim_rot_rate = rotation_rate * ref_len / velocity

        coefs = {"cl": cl, "cd": cd, "cs": cs, "cmd": cmd, "cms": cms, "cml": cml}

        for axis in ["dp, dq, dr"]:

            if not f"_{axis}" in config_dir.name:
                continue

            baseline_coef = False

            for coef in COEFS:
                coef_baseline = aeromap.get(coef, alt=alt, mach=mach, aoa=aoa, aos=aos)
                dcoef = (coefs[coef] - coef_baseline) / adim_rot_rate
                aeromap.add_damping_derivatives(
                    alt=alt,
                    mach=mach,
                    aos=aos,
                    aoa=aoa,
                    coef=coef,
                    axis=axis,
                    value=dcoef,
                    rate=rotation_rate,
                )

        if "_TED_" in config_dir.name:

            # TODO: convert when it is possible to save TED in cpacspy
            raise NotImplementedError("TED not implemented yet")

            # baseline_coef = False

            # config_dir_split = config_dir.split('_')
            # ted_idx = config_dir_split.index('TED')
            # ted_uid = config_dir_split[ted_idx+1]
            # defl_angle = float(config_dir.split('_defl')[1])

            # try:
            #     print(Coef.IncrMap.dcl)
            # except AttributeError:
            #     Coef.IncrMap = a.p.m.f.IncrementMap(ted_uid)

            # dcl = (cl-Coef.cl[-1])
            # dcd = (cd-Coef.cd[-1])
            # dcs = (cs-Coef.cs[-1])
            # dcml = (cml-Coef.cml[-1])
            # dcmd = (cmd-Coef.cmd[-1])
            # dcms = (cms-Coef.cms[-1])

            # control_parameter = -1

            # Coef.IncrMap.add_cs_coef(dcl,dcd,dcs,dcml,dcmd,dcms,ted_uid,control_parameter)

        # Baseline coefficients (no damping derivative or control surfaces case)
        if baseline_coef:
            aeromap.add_coefficients(
                alt=alt,
                mach=mach,
                aos=aos,
                aoa=aoa,
                cd=cd,
                cl=cl,
                cs=cs,
                cml=cml,
                cmd=cmd,
                cms=cms,
            )

        if get_value_or_default(cpacs.tixi, SU2_EXTRACT_LOAD_XPATH, False):
            extract_loads(config_dir)

    aeromap.save()
    cpacs.save_cpacs(str(cpacs_out_path), overwrite=True)


# =================================================================================================
#    MAIN
# =================================================================================================

if __name__ == "__main__":

    log.info("Nothing to execute!")
