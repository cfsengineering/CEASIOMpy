"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Script to run aeroelastic computations using AVL to compute
aerodynamic loads and FramAT for structural calculations.

| Author: Romain Gauthier
| Creation: 2024-06-17

"""

# Imports

import shutil
import numpy as np

from pathlib import Path
from ambiance import Atmosphere
from cpacspy.cpacspy import CPACS

from cpacspy.cpacsfunctions import create_branch
from ceasiompy.PyAVL.func.utils import create_case_dir
from ceasiompy.AeroFrame.func.config import read_avl_fe_file
from ceasiompy.AeroFrame.func.plot import plot_convergence
from ceasiompy.AeroFrame.func.aeroelastic import aeroelastic_loop
from ceasiompy.AeroFrame.func.firstavliteration import run_first_avl_iteration
from ceasiompy.utils.ceasiompyutils import (
    call_main,
    get_selected_aeromap_values,
)

from ceasiompy import log
from ceasiompy.utils.commonxpaths import SELECTED_AEROMAP_XPATH
from ceasiompy.AeroFrame import (
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

    # 1. Get conditions
    tixi = cpacs.tixi
    alt_list, mach_list, aoa_list, aos_list = get_selected_aeromap_values(cpacs)
    log.info("FLIGHT CONDITIONS:")
    log.info(f"\tAltitude          : {', '.join(str(a) for a in alt_list)} meters")
    log.info(f"\tMach number       : {', '.join(str(m) for m in mach_list)}")
    log.info(f"\tAngle of attack   : {', '.join(str(a) for a in aoa_list)} degrees")
    log.info(f"\tAngle of sideslip : {', '.join(str(a) for a in aos_list)} degrees\n")

    # 2. First AVL run
    run_first_avl_iteration(cpacs, results_dir)

    # 3. Aeroelastic loop
    for i_case, _ in enumerate(alt_list):
        alt = alt_list[i_case]
        mach = mach_list[i_case]
        aoa = aoa_list[i_case]
        aos = aos_list[i_case]

        Atm = Atmosphere(alt)
        rho = Atm.density[0]

        case_dir_path = create_case_dir(
            results_dir,
            i_case,
            alt,
            mach=mach,
            aoa=aoa,
            aos=aos,
            q=0.0,
            p=0.0,
            r=0.0,
        )
        avl_iter_path = Path(case_dir_path, "Iteration_1", "AVL")
        avl_iter_path.mkdir(parents=True, exist_ok=True)

        for file_path in case_dir_path.iterdir():
            if file_path.is_file():
                shutil.move(str(file_path), str(avl_iter_path / file_path.name))

        fe_path = Path(avl_iter_path, "fe.txt")
        _, _, _, xyz_list, p_xyz_list, _ = read_avl_fe_file(fe_path, plot=False)

        f_xyz_array = np.array(p_xyz_list) * rho

        # Start the aeroelastic loop
        tip_deflection, residuals = aeroelastic_loop(
            cpacs,
            results_dir,
            case_dir_path,
            rho,
            xyz_list[0],
            f_xyz_array[0],
        )

        # Write results in CPACS out
        create_branch(tixi, FRAMAT_TIP_DEFLECTION_XPATH)
        tixi.updateDoubleElement(FRAMAT_TIP_DEFLECTION_XPATH, tip_deflection[-1], "%g")

        plot_convergence(tip_deflection, residuals, wkdir=case_dir_path)


# Main
if __name__ == "__main__":
    call_main(main, MODULE_NAME)
