"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Script to run aeroelastic computations using AVL to compute
aerodynamic loads and FramAT for structural calculations.
"""

# Imports

import shutil
import numpy as np

from ceasiompy.utils.guiobjects import update_value
from ceasiompy.pyavl.func.data import create_case_dir
from ceasiompy.aeroframe.func.plot import plot_convergence
from ceasiompy.aeroframe.func.config import read_avl_fe_file
from ceasiompy.aeroframe.func.aeroelastic import aeroelastic_loop
from ceasiompy.utils.referencevalues import get_ref_values
from ceasiompy.pyavl.pyavl import main as run_avl
from ceasiompy.utils.ceasiompyutils import (
    call_main,
    get_selected_aeromap_values,
)

from pathlib import Path
from cpacspy.cpacspy import CPACS
from ceasiompy.pyavl.func.data import AVLData

from ceasiompy import log
from ceasiompy.aeroframe import (
    MODULE_NAME,
    FRAMAT_TIP_DEFLECTION_XPATH,
)


# Functions

def main(cpacs: CPACS, results_dir: Path) -> None:
    """
    Runs aeroelastic calculations coupling AVL and FramAT.

    1. Get aeromap conditions
    2. Run a first avl iteration
    3. Use a aeroelastic-loop to get the aeroelastic computations
    """

    # Define constants
    tixi = cpacs.tixi
    alt_list, mach_list, aoa_list, aos_list = get_selected_aeromap_values(cpacs)
    log.info(f"\tAltitude          : {', '.join(str(a) for a in alt_list)} meters")
    log.info(f"\tMach number       : {', '.join(str(m) for m in mach_list)}")
    log.info(f"\tAngle of attack   : {', '.join(str(a) for a in aoa_list)} degrees")
    log.info(f"\tAngle of sideslip : {', '.join(str(a) for a in aos_list)} degrees\n")

    ref_area, ref_length = get_ref_values(cpacs)

    run_avl(
        cpacs=cpacs,
        results_dir=results_dir,
    )

    # 3. Aeroelastic loop
    for i_case, altitude in enumerate(alt_list):
        avl_data = AVLData(
            ref_area=ref_area,
            ref_length=ref_length,
            altitude=altitude,
            mach=mach_list[i_case],
            alpha=aoa_list[i_case],
            beta=aos_list[i_case],
        )
        case_dir_path = create_case_dir(
            i_case=i_case,
            avl_data=avl_data,
            results_dir=results_dir,
        )
        avl_iter_path = Path(case_dir_path, "Iteration_1", "AVL")
        avl_iter_path.mkdir(parents=True, exist_ok=True)

        for file_path in case_dir_path.iterdir():
            if file_path.is_file():
                shutil.move(str(file_path), str(avl_iter_path / file_path.name))

        fe_path = Path(avl_iter_path, "fe.txt")
        _, _, _, xyz_list, p_xyz_list, _ = read_avl_fe_file(fe_path, plot=False)

        f_xyz_array = np.array(p_xyz_list) * avl_data.ref_density

        # Start the aeroelastic loop
        tip_deflection, residuals = aeroelastic_loop(
            cpacs,
            results_dir,
            case_dir_path,
            avl_data.ref_density,
            xyz_list[0],
            f_xyz_array[0],
        )

        update_value(
            tixi=tixi,
            xpath=FRAMAT_TIP_DEFLECTION_XPATH,
            value=tip_deflection[-1],
        )

        plot_convergence(tip_deflection, residuals, wkdir=case_dir_path)


# Main
if __name__ == "__main__":
    call_main(main, MODULE_NAME)
