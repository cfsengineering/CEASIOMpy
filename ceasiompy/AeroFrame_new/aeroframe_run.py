"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Script to run aeroelastic computations using AVL to compute 
aerodynamic loads and FramAT for structural calculations.

Python version: >=3.8

| Author: Romain Gauthier
| Creation: 2024-06-17

TODO:

    * Things to improve ...

"""

# ==============================================================================
#   IMPORTS
# ==============================================================================
from ceasiompy.utils.ceasiomlogger import get_logger
from ceasiompy.utils.moduleinterfaces import get_toolinput_file_path, get_tooloutput_file_path
from ceasiompy.utils.ceasiompyutils import get_results_directory
from ceasiompy.PyAVL.avlrun import run_avl
from ceasiompy.PyAVL.func.avlconfig import get_aeromap_conditions
from ceasiompy.PyAVL.func.avlresults import convert_ps_to_pdf
from ceasiompy.AeroFrame_new.func.aeroframe_config import (
    read_AVL_fe_file,
    create_framat_model,
    get_material_properties,
    create_wing_centerline,
    compute_cross_section,
    write_deformed_geometry,
    write_deformed_command
)

from ceasiompy.AeroFrame_new.func.aeroframe_results import (
    compute_deformations,
    plot_convergence
)

from ceasiompy.AeroFrame_new.func.aeroframe_debbug import plot_fem_mesh

from pathlib import Path
from ambiance import Atmosphere
import numpy as np
from scipy import interpolate
import subprocess
import pandas as pd


log = get_logger()

MODULE_DIR = Path(__file__).parent
MODULE_NAME = MODULE_DIR.name

# =================================================================================================
#   CLASSES
# =================================================================================================


# =================================================================================================
#   FUNCTIONS
# =================================================================================================

def aeroelastic_loop(cpacs_path, xyz, fxyz, area_list, Ix_list, Iy_list, chord_list, wg_center_x_list, wg_center_y_list, wg_center_z_list, wing_transl_list, wg_twist_list, CASE_PATH):

    delta_tip = []
    iter = 0
    res = [1]
    tol = 1e-6

    xyz_root = np.array([wg_center_x_list[0] + wing_transl_list[0][0],
                         wg_center_y_list[0] + wing_transl_list[0][1],
                         wg_center_z_list[0] + wing_transl_list[0][2]])
    fxyz_root = np.zeros(3)

    xyz_tip = np.array([wg_center_x_list[-1] + wing_transl_list[-1][0],
                        wg_center_y_list[-1] + wing_transl_list[-1][1],
                        wg_center_z_list[-1] + wing_transl_list[-1][2]])

    tip_points = None

    aera_profile = interpolate.interp1d(wg_center_y_list, area_list)
    Ix_profile = interpolate.interp1d(wg_center_y_list, Ix_list)
    Iy_profile = interpolate.interp1d(wg_center_y_list, Iy_list)
    chord_profile = interpolate.interp1d(wg_center_y_list, chord_list)
    twist_profile = interpolate.interp1d(wg_center_y_list, wg_twist_list)

    young_modulus, shear_modulus, material_density = get_material_properties(cpacs_path)
    wing_df = pd.DataFrame()
    centerline_df = pd.DataFrame()

    while res[-1] > tol and iter < 3:
        iter += 1

        avl_result_dir = get_results_directory("PyAVL")
        Path(CASE_PATH, f"Iteration_{iter}").mkdir(exist_ok=True)
        ITERATION_PATH = Path(CASE_PATH, f"Iteration_{iter}")
        INITIAL_PATH = avl_result_dir.glob('*.avl')
        for path in INITIAL_PATH:
            UNDEFORMED_PATH = path
        DEFORMED_PATH = Path(ITERATION_PATH, "deformed.avl")
        UNDEFORMED_COMMAND = Path(CASE_PATH, "avl_commands.txt")
        DEFORMED_COMMAND = Path(ITERATION_PATH, "avl_commands.txt")

        log.info(f"################ FramAT: Deformation {iter} ################")

        xyz_tot = np.vstack((xyz_root, xyz))
        fxyz_tot = np.vstack((fxyz_root, fxyz))

        wing_df_new, centerline_df_new, internal_load_df = create_wing_centerline(
            wing_df, centerline_df, xyz_tot, fxyz_tot, iter, xyz_tip, tip_points, aera_profile, Ix_profile, Iy_profile, chord_profile, twist_profile)

        plot_fem_mesh(wing_df_new, centerline_df_new, wkdir=ITERATION_PATH)

        model = create_framat_model(young_modulus, shear_modulus,
                                    material_density, centerline_df_new, internal_load_df)

        # Run the beam analysis
        framat_results = model.run()

        centerline_df, deformed_df, tip_points = compute_deformations(
            framat_results, wing_df_new, centerline_df_new)

        write_deformed_geometry(UNDEFORMED_PATH, DEFORMED_PATH, deformed_df)

        alpha_u = 0.3
        tip_deflection = centerline_df["z_new"].max() - xyz_tip[2]
        if iter == 1:
            delta_tip.append(tip_deflection)
        else:
            delta_tip.append(delta_tip[-1] + alpha_u
                             * (tip_deflection - delta_tip[-1]))

        if iter > 1:
            res.append(np.abs((delta_tip[-1] - delta_tip[-2]) / delta_tip[-2]))

        log.info(f"Iteration {iter} done!")
        log.info(f"Wing tip deflection: {delta_tip[-1]:.3e} m.")
        log.info(f"Residual: {res[-1]:.3e}")

        write_deformed_command(UNDEFORMED_COMMAND, DEFORMED_COMMAND)
        subprocess.run(["xvfb-run", "avl"],
                       stdin=open(str(DEFORMED_COMMAND), "r"), cwd=ITERATION_PATH)
        convert_ps_to_pdf(wkdir=ITERATION_PATH)

        wing_df = wing_df_new
        centerline_df = centerline_df_new

    if res[-1] <= tol:
        log.info("Convergence of wing tip deflection achieved.")
    else:
        log.warning("Maximum number of iterations reached, convergence not achieved.")

    log.info(f"Wing tip deflection: {delta_tip[-1]:.3e} m.")

    return delta_tip, res


def aeroframe_run(cpacs_path, wkdir):
    """Function to run aeroelastic calculations.

    Function 'aeroframe_run' runs aeroelastic calculations
    coupling AVL and FramAT, using a CPACS file
    as input.

    Args:
        cpacs_path (Path) : path to the CPACS input  file
        wkdir (Path) : path to the working directory
    """

    alt_list, mach_list, aoa_list, aos_list = get_aeromap_conditions(cpacs_path)
    run_avl(cpacs_path, wkdir)

    for i_case in range(len(alt_list)):
        alt = alt_list[i_case]
        mach = mach_list[i_case]
        aoa = aoa_list[i_case]
        aos = aos_list[i_case]

        Atm = Atmosphere(alt)
        fluid_density = Atm.density[0]
        fluid_velocity = Atm.speed_of_sound[0] * mach

        case_dir_name = (
            f"Case{str(i_case).zfill(2)}_alt{alt}_mach{round(mach, 2)}"
            f"_aoa{round(aoa, 1)}_aos{round(aos, 1)}"
        )

        CASE_PATH = Path(wkdir, case_dir_name)
        FE_PATH = Path(CASE_PATH, "fe.txt")
        surface_name_list, nspanwise_list, nchordwise_list, xyz_list, p_xyz_list, slope_list = read_AVL_fe_file(
            FE_PATH, plot=False)

        wing_transl_list, wg_twist_list, area_list, Ix_list, Iy_list, wg_center_x_list, wg_center_y_list, wg_center_z_list, wg_chord_list = compute_cross_section(
            cpacs_path)

        f_xyz_list = np.array(p_xyz_list) * 0.5 * fluid_density * fluid_velocity**2

        tip_deflection, residuals = aeroelastic_loop(cpacs_path, xyz_list[0], f_xyz_list[0], area_list, Ix_list,
                                                     Iy_list, wg_chord_list, wg_center_x_list, wg_center_y_list, wg_center_z_list, wing_transl_list, wg_twist_list, CASE_PATH)

        plot_convergence(tip_deflection, residuals, wkdir=CASE_PATH)


# =================================================================================================
#    MAIN
# =================================================================================================


def main(cpacs_path, cpacs_out_path):
    log.info("----- Start of " + MODULE_NAME + " -----")

    results_dir = get_results_directory("AeroFrame_new")
    aeroframe_run(cpacs_path, wkdir=results_dir)

    log.info("----- End of " + MODULE_NAME + " -----")


if __name__ == "__main__":
    cpacs_path = get_toolinput_file_path(MODULE_NAME)
    cpacs_out_path = get_tooloutput_file_path(MODULE_NAME)

    main(cpacs_path, cpacs_out_path)
