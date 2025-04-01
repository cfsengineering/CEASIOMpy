"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Test for get_su2_results function.

Python version: >=3.8

| Author : Aidan Jungo
| Creation: 2022-04-07
| Modified: Leon Deligny
| Date: 21 March 2025

"""

# =================================================================================================
#   IMPORTS
# =================================================================================================

import os
import pytest
import unittest
import itertools

import numpy as np

from cpacspy.cpacsfunctions import create_branch
from ceasiompy.SU2Run.func.results import save_screenshot
from ceasiompy.SU2Run.func.utils import get_su2_forces_moments

from ceasiompy.utils.ceasiompyutils import (
    current_workflow_dir,
    ensure_and_append_text_element,
)
from ceasiompy.SU2Run.func.dotderivatives import (
    load_parameters,
    compute_derivatives,
)

from pathlib import Path
from ambiance import Atmosphere
from cpacspy.cpacspy import CPACS
from ceasiompy.utils.ceasiompytest import CeasiompyTest

from typing import (
    List,
    Dict,
)

from ceasiompy import log
from ceasiompy.utils.commonpaths import TEST_RESULTS_FILES_PATH
from ceasiompy.utils.commonnames import SU2_FORCES_BREAKDOWN_NAME

from ceasiompy.utils.commonxpath import (
    REF_XPATH,
    SU2_DYNAMICDERIVATIVES_DATA_XPATH,
)

# =================================================================================================
#   FUNCTIONS
# =================================================================================================


class TestModuleTemplate(CeasiompyTest):
    @classmethod
    def setUpClass(cls):
        cls.test_results_path = TEST_RESULTS_FILES_PATH
        cls.config_dir = cls.test_results_path / "Case01_mach0.3_anglealpha_dynstab"
        cls.cpacs = CPACS(cls.test_results_path / "00_ToolInput.xml")
        cls.tixi = cls.cpacs.tixi
        cls.wkdir = current_workflow_dir()
        # Get the reference dimensions
        cls.s = cls.tixi.getDoubleElement(REF_XPATH + '/area')
        cls.c = cls.tixi.getDoubleElement(REF_XPATH + '/length')
        cls.b = cls.s / cls.c


@pytest.mark.skipif("DISPLAY" not in os.environ, reason="requires display")
def test_save_screenshot(self):
    """Test the function 'save_screenshot'"""

    surface_flow_file = Path(self.test_results_path, "surface_flow.vtu")
    screenshot_file = save_screenshot(surface_flow_file, "Mach")
    assert screenshot_file.exists()

    if screenshot_file.exists():
        screenshot_file.unlink()


def forces_breakdown(self):
    """alpha-dot computation"""

    # Nb of timesteps
    n = 22

    # Retrieve the directories matching the pattern
    dir_list: List[Path] = [d for d in Path(self.config_dir.parent).iterdir() if d.is_dir()]
    log.info(f"dir_list {dir_list}")

    dict_dir: List[Dict] = []

    for dir_ in dir_list:
        log.info(f"dir.name {dir_.name}")
        if dir_.name.endswith("aoa0.0_aos0.0"):
            angle = "none"
        elif dir_.name.endswith("dynstab"):
            angle = dir_.name.split("_")[3].split("angle")[1]
        else:
            log.warning(f"Skipping results of directory {dir_}.")
            continue

        dict_dir.append(
            {
                "mach": float(dir_.name.split("_")[2].split("mach")[1]),
                "alt": float(dir_.name.split("_")[1].split("alt")[1]),
                "dir": dir_,
                "angle": angle,
            },
        )

    log.info(f"dict_dir {dict_dir}")

    # Extract unique mach and alt values
    mach_values = list(set(d['mach'] for d in dict_dir))
    alt_values = list(set(d['alt'] for d in dict_dir))

    for mach, alt in itertools.product(mach_values, alt_values):

        def check_one_entry(dict_dir: List[Dict], angle: str) -> Path:
            # Check that there exists exactly one entry with "angle" == "none" in dict_dir
            one_entry = [d for d in dict_dir if d['mach']
                            == mach and d['alt'] == alt and d['angle'] == angle]
            if len(one_entry) != 1:
                raise ValueError(
                    f"Expected exactly one angle={angle}"
                    f"for mach={mach}, alt={alt}, "
                    f"but found {len(one_entry)}."
                )
            else:
                return one_entry[0]["dir"]

        none_file = check_one_entry(dict_dir, "none")
        alpha_file = check_one_entry(dict_dir, "alpha")
        # beta_file = check_one_entry(dict_dir, "beta")

        angle_file = {"alpha": alpha_file / "no_deformation", }  # "beta": beta_file

        # Retrieve forces and moments for (alpha, alpha_dot) = (0, 0)
        none_force_file_path = Path(none_file, "no_deformation", SU2_FORCES_BREAKDOWN_NAME)

        (
            cfx_0, cfy_0, cfz_0,
            cmx_0, cmy_0, cmz_0,

        ) = get_su2_forces_moments(none_force_file_path)

        log.info(
            f"cfx_0: {cfx_0}, cfy_0: {cfy_0}, cfz_0: {cfz_0}, "
            f"cmx_0: {cmx_0}, cmy_0: {cmy_0}, cmz_0: {cmz_0}"
        )

        # Force
        f_static = np.tile([
            cfx_0, cfy_0, cfz_0,
        ], (n, 1))

        # Moments
        m_static = np.tile([
            cmx_0, cmy_0, cmz_0
        ], (n, 1))

        # Retrive forces and moments for (alpha, alpha_dot) = (alpha(t), alpha_dot(t))
        for angle in ['alpha']:  # , 'beta'

            # Get results from dynstab
            force_file_paths = list(Path(angle_file[angle]).glob("forces_breakdown_*.dat"))

            if not force_file_paths:
                raise OSError("No result force file have been found!")

            forces_coef_list, moments_coef_list = [], []

            for force_file_path in force_file_paths:
                # Access coefficients
                cfx, cfy, cfz, cmx, cmy, cmz = get_su2_forces_moments(force_file_path)
                forces_coef_list.append([cfx, cfy, cfz])
                moments_coef_list.append([cmx, cmy, cmz])

            # Convert the list to a numpy array
            f_time = np.array(forces_coef_list)
            m_time = np.array(moments_coef_list)

            # Compute derivatives
            a, omega, _, t = load_parameters(self.tixi)
            fx, fy = compute_derivatives(a, omega, t, f_time, f_static)
            mx, my = compute_derivatives(a, omega, t, m_time, m_static)

            # Velocity in m/s in atmospheric environment
            Atm = Atmosphere(alt)
            velocity = Atm.speed_of_sound[0] * mach

            # Dynamic pressure
            q_dyn = Atm.density[0] * (velocity ** 2) / 2.0

            qs = q_dyn * self.s
            qsb = qs * self.b
            qsc = qs * self.c

            # Scale forces accordingly
            cfx = fx / qs
            cfy = fy / qs

            # Scale moments accordingly
            cmx = np.copy(mx)
            cmy = np.copy(my)
            cmx[[0, 2], ] /= qsb
            cmx[1, ] /= qsc
            cmy[[0, 2], ] /= qsb
            cmy[1, ] /= qsc

            # Put derivatives in CPACS at SU2 in DynamicDerivatives
            xpath = SU2_DYNAMICDERIVATIVES_DATA_XPATH

            # Ensure the path exists
            create_branch(self.tixi, xpath)

            ensure_and_append_text_element(self.tixi, xpath, "mach", str(mach))
            ensure_and_append_text_element(self.tixi, xpath, "alt", str(alt))

            log.info(f"q {q_dyn} fx {fx} mx {mx}, cfx {cfx} cmx {cmx}")

            for i, label in enumerate(['cfx', 'cfy', 'cfz']):
                ensure_and_append_text_element(
                    self.tixi, xpath, f"{label}_{angle}", str(cfx[i]))
                ensure_and_append_text_element(
                    self.tixi, xpath, f"{label}_{angle}prim", str(cfy[i]))
            for i, label in enumerate(['cmx', 'cmy', 'cmz']):
                ensure_and_append_text_element(
                    self.tixi, xpath, f"{label}_{angle}", str(cmx[i]))
                ensure_and_append_text_element(
                    self.tixi, xpath, f"{label}_{angle}prim", str(cmy[i]))

# =================================================================================================
#    MAIN
# =================================================================================================


if __name__ == "__main__":
    unittest.main(verbosity=0)
