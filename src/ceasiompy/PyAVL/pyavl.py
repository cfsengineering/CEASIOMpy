"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Script to run AVL calculations in CEASIOMpy.
AVL allows to perform aerodynamic analyses using
the vortex-lattice method (VLM)

| Author: Romain Gauthier
| Creation: 2024-03-14
| Modified: Leon Deligny
| Date: 11-Mar-2025

"""

# ==============================================================================
#   IMPORTS
# ==============================================================================

from ceasiompy.utils.ceasiompyutils import run_software
from ceasiompy.PyAVL.func.plot import convert_ps_to_pdf
from ceasiompy.PyAVL.func.results import get_avl_results
from ceasiompy.PyAVL.func.utils import (
    create_case_dir,
    duplicate_elements,
)
from ceasiompy.PyAVL.func.config import (
    write_command_file,
    retrieve_gui_values,
    get_physics_conditions,
)

from pathlib import Path
from cpacspy.cpacspy import CPACS
from ceasiompy.Database.func.storing import CeasiompyDb

from ceasiompy import log
from ceasiompy.PyAVL import SOFTWARE_NAME

# =================================================================================================
#    MAIN
# =================================================================================================


def main(cpacs: CPACS, results_dir: Path) -> None:
    """
    Run AVL calculations on specified CPACS file.
        1. Load the necessary data.
        2. Run avl with p, q, r rate deflections.
        3. Run avl with control surfaces deflections.
    """

    # 1. Load the necessary data
    tixi = cpacs.tixi

    (
        alt_list,
        mach_list,
        aoa_list,
        aos_list,
        rotation_rate_list,
        control_surface_list,
        avl_path,
        save_fig,
        nb_cpu,
        expand,
    ) = retrieve_gui_values(cpacs, results_dir)

    #
    # 2. p, q, r
    (
        new_alt_list,
        new_mach_list,
        new_aoa_list,
        new_aos_list,
        new_pitch_rate_list,
        new_roll_rate_list,
        new_yaw_rate_list,
    ) = duplicate_elements(
        expand,
        alt_list,
        mach_list,
        aoa_list,
        aos_list,
        rotation_rate_list,
    )
    first_cases = len(new_alt_list)

    for i_case, alt in enumerate(new_alt_list):
        mach = new_mach_list[i_case]
        aoa = new_aoa_list[i_case]
        aos = new_aos_list[i_case]

        q = new_pitch_rate_list[i_case]
        p = new_roll_rate_list[i_case]
        r = new_yaw_rate_list[i_case]

        (
            roll_rate_star, pitch_rate_star, yaw_rate_star,
            ref_density, g_acceleration, ref_velocity,
        ) = get_physics_conditions(tixi, alt, mach, p, q, r)

        if expand:
            db = CeasiompyDb()
            tol = 1e-4
            data = db.get_data(
                table_name="avl_data",
                columns=["mach"],
                db_close=True,
                filters=[
                    f"mach = {mach}",
                    f"aircraft = '{cpacs.ac_name}'",
                    f"alt = {alt}",
                    f"alpha BETWEEN {aoa - tol} AND {aoa + tol}",
                    f"beta BETWEEN {aos - tol} AND {aos + tol}",
                    f"pb_2V BETWEEN {roll_rate_star - tol} AND {roll_rate_star + tol}",
                    f"qc_2V BETWEEN {pitch_rate_star - tol} AND {pitch_rate_star + tol}",
                    f"rb_2V BETWEEN {yaw_rate_star - tol} AND {yaw_rate_star + tol}",
                ]
            )
            if data:
                # If data is already in ceasiompy.db
                # Go to next iteration in for loop
                log.info(f"Case {alt, mach, aoa, aos} already done.")
                continue

        case_dir_path = create_case_dir(
            results_dir,
            i_case,
            alt,
            mach=mach,
            aoa=aoa,
            aos=aos,
            q=q,
            p=p,
            r=r,
        )

        command_path = write_command_file(
            avl_path=avl_path,
            case_dir_path=case_dir_path,
            save_plots=save_fig,
            ref_density=ref_density,
            g_acceleration=g_acceleration,
            ref_velocity=ref_velocity,
            alpha=aoa,
            beta=aos,
            pitch_rate_star=pitch_rate_star,
            roll_rate_star=roll_rate_star,
            yaw_rate_star=yaw_rate_star,
            mach_number=mach,
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

    if control_surface_list != [0.0]:

        #
        # 3. aileron, elevator, rudder
        (
            new_alt_list,
            new_mach_list,
            new_aoa_list,
            new_aileron_list,
            new_elevator_list,
            new_rudder_list,
        ) = duplicate_elements(
            expand,
            alt_list,
            mach_list,
            aoa_list,
            control_surface_list,
        )

        # Iterate through each case
        for i_case, alt in enumerate(new_alt_list):
            mach = new_mach_list[i_case]
            aoa = new_aoa_list[i_case]

            aileron = new_aileron_list[i_case]
            elevator = new_elevator_list[i_case]
            rudder = new_rudder_list[i_case]
            
            (
                _, _, _,
                ref_density, g_acceleration, ref_velocity,
            ) = get_physics_conditions(tixi, alt, mach, 0.0, 0.0, 0.0)

            if expand:
                db = CeasiompyDb()
                tol = 1e-4
                data = db.get_data(
                    table_name="avl_data",
                    columns=["mach"],
                    db_close=True,
                    filters=[
                        f"mach = {mach}",
                        f"aircraft = '{cpacs.ac_name}'",
                        f"alt = {alt}",
                        f"alpha BETWEEN {aoa - tol} AND {aoa + tol}",
                        f"beta = 0.0",
                        f"aileron BETWEEN {aileron - tol} AND {aileron + tol}",
                        f"elevator BETWEEN {elevator - tol} AND {elevator + tol}",
                        f"rudder BETWEEN {rudder - tol} AND {rudder + tol}",
                    ]
                )
                if data:
                    # If data is already in ceasiompy.db
                    # Go to next iteration in for loop
                    log.info(f"Case {alt, mach, aoa, aos} already done.")
                    continue
            
            case_dir_path = create_case_dir(
                results_dir,
                i_case + first_cases,
                alt,
                mach=mach,
                aoa=aoa,
                aileron=aileron,
                elevator=elevator,
                rudder=rudder,
            )

            command_path = write_command_file(
                avl_path=avl_path,
                case_dir_path=case_dir_path,
                save_plots=save_fig,
                ref_density=ref_density,
                g_acceleration=g_acceleration,
                ref_velocity=ref_velocity,
                alpha=aoa,
                mach_number=mach,
                aileron=aileron,
                rudder=rudder,
                elevator=elevator,
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

    get_avl_results(cpacs, results_dir)
