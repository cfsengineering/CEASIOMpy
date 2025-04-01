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
from ceasiompy import log

from ceasiompy.utils.ceasiompyutils import call_main, get_results_directory

from ceasiompy.PyAVL.pyavl import main as run_avl
from ceasiompy.utils.ceasiompyutils import get_aeromap_conditions
from cpacspy.cpacsfunctions import (
    get_value_or_default,
    create_branch,
)
from ceasiompy.PyAVL.func.plot import convert_ps_to_pdf
from ceasiompy.AeroFrame_new.func.aeroframe_config import (
    read_AVL_fe_file,
    create_framat_model,
    get_material_properties,
    get_section_properties,
    create_wing_centerline,
    compute_cross_section,
    write_deformed_geometry,
    write_deformed_command
)

from ceasiompy.AeroFrame_new.func.aeroframe_results import (
    compute_deformations,
    plot_translations_rotations,
    plot_convergence
)

from ceasiompy.AeroFrame_new.func.aeroframe_debbug import (
    plot_fem_mesh,
    plot_deformed_wing
)

from ceasiompy.utils.commonxpath import (
    AVL_PLOT_XPATH,
    AVL_AEROMAP_UID_XPATH,
    FRAMAT_RESULTS_XPATH,
    FRAMAT_MESH_XPATH,
    AEROFRAME_SETTINGS
)
from cpacspy.cpacspy import CPACS

from pathlib import Path
from ambiance import Atmosphere
import numpy as np
from scipy import interpolate
import subprocess
import pandas as pd
import shutil

MODULE_DIR = Path(__file__).parent
MODULE_NAME = MODULE_DIR.name


# =================================================================================================
#   CLASSES
# =================================================================================================


# =================================================================================================
#   FUNCTIONS
# =================================================================================================

def aeroelastic_loop(cpacs_path, CASE_PATH, q, xyz, fxyz):
    """Function to execute the aeroelastic-loop.

    Function 'aeroelastic_loop' executes the aeroelastic-loop,
    iterating between AVL aerodynamic computations and structural
    calculations made with FramAT.

    Args:
        cpacs_path (Path): path to the CPACS input file.
        CASE_PATH (path): path to the flight case directory.
        q (float): dynamic pressure 0.5*rho*U^2 [Pa].
        xyz (list): list of the coordinates of each VLM panel [m].
        fxyz (list): list of the components of aero forces of each VLM panel [N].

    Returns:
        delta_tip (list): deflections of the mid-chord wing tip for each iteration [m].
        res (list): residual of the mid-chord wing tip deflection.
    """

    cpacs = CPACS(cpacs_path)

    AVL_ITER1_PATH = Path(CASE_PATH, "Iteration_1", "AVL")

    # Get the path to the undeformed/initial AVL geometry
    for path in get_results_directory("PyAVL").glob('*.avl'):
        AVL_UNDEFORMED_PATH = path

    AVL_UNDEFORMED_COMMAND = Path(AVL_ITER1_PATH, "avl_commands.txt")

    # Get the properties of each cross-section of the wing
    (
        wing_origin,
        wg_twist_list,
        area_list,
        Ix_list,
        Iy_list,
        wg_center_x_list,
        wg_center_y_list,
        wg_center_z_list,
        wg_chord_list,
        wg_scaling
    ) = compute_cross_section(cpacs_path)

    # Get the properties of the wing material and the number of beam nodes to use
    young_modulus, shear_modulus, material_density = get_material_properties(cpacs_path)
    N_beam = get_value_or_default(cpacs.tixi, FRAMAT_MESH_XPATH + "/NumberNodes", 8)

    # Define the coordinates of the wing root and tip
    xyz_root = np.array([wg_center_x_list[0] + wing_origin[0] + wg_chord_list[0] / 2,
                         wg_center_y_list[0] + wing_origin[1],
                         wg_center_z_list[0] + wing_origin[2]])
    fxyz_root = np.zeros(3)

    # xyz_tip = np.array([wg_center_x_list[-1] + wing_origin[0] + wg_chord_list[-1] / 2,
    #                     wg_center_y_list[-1] + wing_origin[1],
    #                     wg_center_z_list[-1] + wing_origin[2]])

    Xle_list = []
    Yle_list = []
    Zle_list = []
    surface_count = 0
    with open(AVL_UNDEFORMED_PATH, "r") as f:
        lines = f.readlines()
        for i, line in enumerate(lines):
            if "SURFACE" in line:
                surface_count += 1
                if surface_count > 1:
                    break

            if "Xle" in line:
                next_line = lines[i + 1].strip()
                parts = next_line.split()
                Xle_list.append(float(parts[0]) + wing_origin[0])
                Yle_list.append(float(parts[1]) + wing_origin[1])
                Zle_list.append(float(parts[2]) + wing_origin[2])

    Xle_array = np.array(Xle_list)
    Yle_array = np.array(Yle_list)
    Zle_array = np.array(Zle_list)

    xyz_tip = np.array([Xle_array[-1] + wg_chord_list[-1] / 2,
                        Yle_array[-1],
                        Zle_array[-1]])

    # Get cross-section properties from CPACS file (if constants)
    area_const, Ix_const, Iy_const = get_section_properties(cpacs_path)

    if area_const > 0:
        area_list = area_const * np.ones(len(wg_center_y_list))
    if Ix_const > 0:
        Ix_list = Ix_const * np.ones(len(wg_center_y_list))
    if Iy_const > 0:
        Iy_list = Iy_const * np.ones(len(wg_center_y_list))

    # Interpolation of the cross-section properties along the span
    area_profile = interpolate.interp1d(wg_center_y_list, area_list, fill_value="extrapolate")
    Ix_profile = interpolate.interp1d(wg_center_y_list, Ix_list, fill_value="extrapolate")
    Iy_profile = interpolate.interp1d(wg_center_y_list, Iy_list, fill_value="extrapolate")
    chord_profile = interpolate.interp1d(wg_center_y_list, wg_chord_list, fill_value="extrapolate")
    twist_profile = interpolate.interp1d(wg_center_y_list, wg_twist_list, fill_value="extrapolate")

    # Convergence settings
    n_iter_max = get_value_or_default(cpacs.tixi, AEROFRAME_SETTINGS + "/MaxNumberIterations", 8)
    tol = get_value_or_default(cpacs.tixi, AEROFRAME_SETTINGS + "/Tolerance", 1e-3)

    # Initialize variables for the loop
    wing_df = pd.DataFrame()
    centerline_df = pd.DataFrame()
    delta_tip = []
    n_iter = 0
    res = [1]
    tip_def_points = None

    # Start of the loop, until convergence or max number of iterations
    while res[-1] > tol and n_iter < n_iter_max:
        n_iter += 1
        log.info("")
        log.info(f"----- FramAT: Deformation {n_iter} -----")

        Path(CASE_PATH, f"Iteration_{n_iter + 1}", "AVL").mkdir(parents=True, exist_ok=True)
        Path(CASE_PATH, f"Iteration_{n_iter}", "FramAT").mkdir(parents=True, exist_ok=True)
        AVL_ITER_PATH = Path(CASE_PATH, f"Iteration_{n_iter + 1}", "AVL")
        FRAMAT_ITER_PATH = Path(CASE_PATH, f"Iteration_{n_iter}", "FramAT")
        AVL_DEFORMED_PATH = Path(AVL_ITER_PATH, "deformed.avl")
        AVL_DEFORMED_COMMAND = Path(AVL_ITER_PATH, "avl_commands.txt")

        xyz_tot = np.vstack((xyz_root, xyz))
        fxyz_tot = np.vstack((fxyz_root, fxyz))

        (
            wing_df_new,
            centerline_df_new,
            internal_load_df
        ) = create_wing_centerline(wing_df,
                                   centerline_df,
                                   N_beam,
                                   wing_origin,
                                   xyz_tot,
                                   fxyz_tot,
                                   n_iter,
                                   xyz_tip,
                                   tip_def_points,
                                   area_profile,
                                   Ix_profile,
                                   Iy_profile,
                                   chord_profile,
                                   twist_profile,
                                   CASE_PATH,
                                   AVL_UNDEFORMED_PATH,
                                   wg_scaling)

        if n_iter == 1:
            undeformed_df = centerline_df_new.copy(deep=True)
            semi_span = centerline_df_new["y"].max()

        plot_fem_mesh(wing_df_new, centerline_df_new, wkdir=FRAMAT_ITER_PATH)
        plot_deformed_wing(centerline_df_new, undeformed_df, wkdir=FRAMAT_ITER_PATH)
        undeformed_df.to_csv(Path(FRAMAT_ITER_PATH, "undeformed.csv"), index=False)
        centerline_df_new.to_csv(Path(FRAMAT_ITER_PATH, "deformed.csv"), index=False)

        model = create_framat_model(young_modulus,
                                    shear_modulus,
                                    material_density,
                                    centerline_df_new,
                                    internal_load_df)

        # Run the beam analysis
        framat_results = model.run()

        # Post-processing tasks
        centerline_df, deformed_df, tip_def_points = compute_deformations(framat_results,
                                                                          wing_df_new,
                                                                          centerline_df_new)

        plot_translations_rotations(centerline_df, wkdir=FRAMAT_ITER_PATH)

        # Compute tip deflection
        tip_deflection = centerline_df["z_new"].loc[centerline_df["y_new"].idxmax()] - xyz_tip[2]
        tip_twist = centerline_df["thy_new"].loc[centerline_df["y_new"].idxmax()]
        delta_tip.append(tip_deflection)

        if n_iter > 1:
            res.append(np.abs((delta_tip[-1] - delta_tip[-2]) / delta_tip[-2]))

        deflection = delta_tip[-1]
        percentage = deflection / semi_span

        log.info(f"Iteration {n_iter} done!")
        log.info(
            f"Wing tip deflection:     {deflection:.3e} m "
            f"({percentage:.2%} of the semi-span length)."
        )
        log.info(f"Residual:                {res[-1]:.3e}")

        # Run AVL with the new deformed geometry
        write_deformed_geometry(AVL_UNDEFORMED_PATH, AVL_DEFORMED_PATH, centerline_df, deformed_df)
        write_deformed_command(AVL_UNDEFORMED_COMMAND, AVL_DEFORMED_COMMAND)
        subprocess.run(["xvfb-run", "avl"],
                       stdin=open(str(AVL_DEFORMED_COMMAND), "r"),
                       cwd=AVL_ITER_PATH)

        save_avl_plot = get_value_or_default(cpacs.tixi, AVL_PLOT_XPATH, False)
        if save_avl_plot:
            convert_ps_to_pdf(wkdir=AVL_ITER_PATH)

        # Read the new forces file to extract the loads
        FE_PATH = Path(AVL_ITER_PATH, "fe.txt")
        _, _, _, xyz_list, p_xyz_list, _ = read_AVL_fe_file(FE_PATH, plot=False)

        xyz = xyz_list[0]
        fxyz = np.array(p_xyz_list[0]) * q

        wing_df = wing_df_new
        centerline_df = centerline_df_new

        # Work conservation validation
        def compute_aero_work(row):
            force = np.array([row['Fx'], row['Fy'], row['Fz']])
            displacement = np.array(row['delta_A'])
            work = np.dot(force, displacement)
            return work

        wing_df['aero_work'] = wing_df.apply(compute_aero_work, axis=1)
        total_aero_work = wing_df['aero_work'].sum()

        def compute_structural_work(row):
            force = np.array([row['Fx'], row['Fy'], row['Fz']])
            moment = np.array([row['Mx'], row['My'], row['Mz']])
            displacement = np.array(row['delta_S'])
            rotation = np.array(row['omega_S'])
            work = np.dot(force, displacement) + np.dot(moment, rotation)
            return work

        centerline_df['structural_work'] = centerline_df.apply(compute_structural_work, axis=1)
        total_structural_work = centerline_df['structural_work'].sum()

        log.info(f"Total aerodynamic work:  {total_aero_work:.3e} J.")
        log.info(f"Total structural work:   {total_structural_work:.3e} J.")
        log.info(
            f"Work variation:          "
            f"{((total_aero_work - total_structural_work) / total_aero_work):.2%}."
        )
    log.info("")
    log.info("----- Final results -----")
    if res[-1] <= tol:
        log.info("Convergence of wing tip deflection achieved.")
    else:
        log.warning("Maximum number of iterations reached, convergence not achieved.")

    deflection = delta_tip[-1]
    percentage = deflection / semi_span

    log.info(
        f"Wing tip deflection:     {deflection:.3e} m ({percentage:.2%} of the semi-span length).")
    log.info(f"Wing tip twist:          {tip_twist:.3e} degrees.")
    log.info(f"Total aerodynamic work:  {total_aero_work:.3e} J.")
    log.info(f"Total structural work:   {total_structural_work:.3e} J.")
    log.info(
        "Work variation:          "
        f"{((total_aero_work - total_structural_work) / total_aero_work):.2%}."
    )

    return delta_tip, res


def main(cpacs: CPACS, wkdir: Path) -> None:
    """Function to run aeroelastic calculations.

    Function 'aeroframe_run' runs aeroelastic calculations
    coupling AVL and FramAT, using a CPACS file
    as input.

    Args:
        cpacs_path (Path): path to the CPACS input file.
        cpacs_out_path (Path): path to the CPACS output file.
        wkdir (Path): path to the working directory.
    """
    cpacs_path = cpacs.cpacs_file
    tixi = cpacs.tixi
    alt_list, mach_list, aoa_list, aos_list = get_aeromap_conditions(
        cpacs_path,
        AVL_AEROMAP_UID_XPATH
    )

    # First AVL run
    run_avl(cpacs, wkdir)

    for i_case, _ in enumerate(alt_list):
        alt = alt_list[i_case]
        mach = mach_list[i_case]
        aoa = aoa_list[i_case]
        aos = aos_list[i_case]

        Atm = Atmosphere(alt)
        fluid_density = Atm.density[0]
        fluid_velocity = Atm.speed_of_sound[0] * mach
        q = 0.5 * fluid_density * fluid_velocity**2

        case_dir_name = (
            f"Case{str(i_case).zfill(2)}_alt{alt}_mach{round(mach, 2)}"
            f"_aoa{round(aoa, 1)}_aos{round(aos, 1)}"
        )

        CASE_PATH = Path(wkdir, case_dir_name)
        Path(CASE_PATH, "Iteration_1", "AVL").mkdir(parents=True, exist_ok=True)
        AVL_ITER_PATH = Path(CASE_PATH, "Iteration_1", "AVL")

        for file_path in CASE_PATH.iterdir():
            if file_path.is_file():
                shutil.move(str(file_path), str(AVL_ITER_PATH / file_path.name))

        FE_PATH = Path(AVL_ITER_PATH, "fe.txt")
        _, _, _, xyz_list, p_xyz_list, _ = read_AVL_fe_file(FE_PATH, plot=False)

        f_xyz_array = np.array(p_xyz_list) * q

        # Start the aeroelastic loop
        tip_deflection, residuals = aeroelastic_loop(cpacs_path,
                                                     CASE_PATH,
                                                     q,
                                                     xyz_list[0],
                                                     f_xyz_array[0])

        # Write results in CPACS out
        create_branch(tixi, FRAMAT_RESULTS_XPATH + "/TipDeflection")
        tixi.updateDoubleElement(FRAMAT_RESULTS_XPATH + "/TipDeflection", tip_deflection[-1], "%g")

        plot_convergence(tip_deflection, residuals, wkdir=CASE_PATH)


# =================================================================================================
#    MAIN
# =================================================================================================

if __name__ == "__main__":
    call_main(main, MODULE_NAME)
