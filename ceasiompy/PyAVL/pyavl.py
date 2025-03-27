"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Script to run AVL calculations in CEASIOMpy.
AVL allows to perform aerodynamic analyses using
the vortex-lattice method (VLM)

Python version: >=3.8

| Author: Romain Gauthier
| Creation: 2024-03-14
| Modified: Leon Deligny
| Date: 11-Mar-2025

"""

# ==============================================================================
#   IMPORTS
# ==============================================================================

from ceasiompy.PyAVL.func.plot import convert_ps_to_pdf
from ceasiompy.PyAVL.func.results import get_avl_results
from ceasiompy.PyAVL.func.utils import duplicate_elements
from ceasiompy.PyAVL.func.config import write_command_file
from ceasiompy.PyAVL.func.utils import retrieve_gui_values

from ceasiompy.utils.ceasiompyutils import (
    call_main,
    run_software,
)

from pathlib import Path
from ambiance import Atmosphere
from cpacspy.cpacspy import CPACS

from ceasiompy import log

from ceasiompy.PyAVL import *

# =================================================================================================
#    MAIN
# =================================================================================================

def main(cpacs: CPACS, wkdir: Path) -> None:
    """
    Run AVL calculations on specified CPACS file.
        1. Load the necessary data.
        2. Run avl with p, q, r rate deflections.
        3. Run avl with control surfaces deflections.

    Args:
        cpacs_path (Path): Path to the CPACS input file.
        wkdir (Path): Path to the working directory.

    """

    # 1. Load the necessary data
    tixi = cpacs.tixi

    (
        alt_list, mach_list, aoa_list, aos_list,
        rotation_rate_list, control_surface_list,
        avl_path,
        save_fig,
        nb_cpu,

    ) = retrieve_gui_values(cpacs)

    #
    # 2. p, q, r
    new_alt_list, new_mach_list, new_aoa_list, new_aos_list, new_pitch_rate_list, new_roll_rate_list, new_yaw_rate_list = duplicate_elements(
        list(set(alt_list)),
        list(set(mach_list)),
        list(set(aoa_list)),
        list(set(aos_list)),
        list(set(rotation_rate_list)),
    )
    first_cases = len(new_alt_list)

    for i_case in range(first_cases):
        alt = new_alt_list[i_case]
        mach = new_mach_list[i_case]
        aoa = new_aoa_list[i_case]
        aos = new_aos_list[i_case]

        q = new_pitch_rate_list[i_case]
        p = new_roll_rate_list[i_case]
        r = new_yaw_rate_list[i_case]

        # Set atmosphere conditions
        Atm = Atmosphere(alt)
        density = Atm.density[0]
        g = Atm.grav_accel[0]
        velocity = Atm.speed_of_sound[0] * mach

        log.info(
            f"--- alt: {alt}, "
            f"mach: {mach}, "
            f"aoa: {aoa}, "
            f"aos: {aos}, "
            f"q: {q}, "
            f"p: {p}, "
            f"r: {r} ---"
        )

        # Name of the case directory
        case_dir_name = (
            f"Case{str(i_case).zfill(2)}"
            f"_alt{alt}"
            f"_mach{round(mach, 2)}"
            f"_aoa{round(aoa, 1)}"
            f"_aos{round(aos, 1)}"
            f"_p{round(p, 1)}"
            f"_q{round(q, 1)}"
            f"_r{round(r, 1)}"
        )

        Path(wkdir, case_dir_name).mkdir(exist_ok=True)
        case_dir_path = Path(wkdir, case_dir_name)

        command_path = write_command_file(
            tixi=tixi,
            avl_path=avl_path,
            case_dir_path=case_dir_path,
            save_plots=save_fig,
            alpha=aoa,
            beta=aos,
            pitch_rate=q,
            roll_rate=p,
            yaw_rate=r,
            mach_number=mach,
            ref_velocity=velocity,
            ref_density=density,
            aileron=0.0,
            rudder=0.0,
            elevator=0.0,
            g_acceleration=g,
        )

        run_software(
            software_name=SOFTWARE_NAME,
            arguments=[""],
            wkdir=case_dir_path,
            with_mpi=False,
            nb_cpu=nb_cpu,
            stdin=open(str(command_path), "r"),
        )

        if save_fig:
            convert_ps_to_pdf(case_dir_path)

    #
    # 3. aileron, elevator, rudder
    new_alt_list, new_mach_list, new_aoa_list, new_aileron_list, new_elevator_list, new_rudder_list = duplicate_elements(
        list(set(alt_list)),
        list(set(mach_list)),
        list(set(aoa_list)),
        list(set(control_surface_list)),
    )

    # Name of the case directory
    for i_case in range(len(new_alt_list)):
        alt = new_alt_list[i_case]
        mach = new_mach_list[i_case]
        aoa = new_aoa_list[i_case]

        aileron = new_aileron_list[i_case]
        elevator = new_elevator_list[i_case]
        rudder = new_rudder_list[i_case]

        # Set atmosphere conditions
        Atm = Atmosphere(alt)
        density = Atm.density[0]
        g = Atm.grav_accel[0]
        velocity = Atm.speed_of_sound[0] * mach

        log.info(
            f"--- alt: {alt}, "
            f"mach: {mach}, "
            f"aoa: {aoa}, "
            f"aileron: {aileron}, "
            f"elevator: {elevator}, "
            f"rudder: {rudder} ---"
        )

        case_dir_name = (
            f"Case{str(i_case+first_cases).zfill(2)}"
            f"_alt{alt}"
            f"_mach{round(mach, 2)}"
            f"_aoa{round(aoa, 1)}"
            f"_aileron{round(aileron, 1)}"
            f"_elevator{round(elevator, 1)}"
            f"_rudder{round(rudder, 1)}"
        )

        Path(wkdir, case_dir_name).mkdir(exist_ok=True)
        case_dir_path = Path(wkdir, case_dir_name)

        command_path = write_command_file(
            tixi=tixi,
            avl_path=avl_path,
            case_dir_path=case_dir_path,
            save_plots=save_fig,
            alpha=aoa,
            beta=0.0,
            pitch_rate=0.0,
            roll_rate=0.0,
            yaw_rate=0.0,
            mach_number=mach,
            ref_velocity=velocity,
            ref_density=density,
            aileron=aileron,
            rudder=rudder,
            elevator=elevator,
            g_acceleration=g,
        )

        run_software(
            software_name=SOFTWARE_NAME,
            arguments=[""],
            wkdir=case_dir_path,
            with_mpi=False,
            nb_cpu=nb_cpu,
            stdin=open(str(command_path), "r"),
        )

        if save_fig:
            convert_ps_to_pdf(case_dir_path)

    get_avl_results(cpacs, wkdir)


if __name__ == "__main__":
    call_main(main, MODULE_NAME)
