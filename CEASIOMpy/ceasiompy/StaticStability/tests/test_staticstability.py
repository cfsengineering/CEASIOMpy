"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Test functions for StaticStability module.

Python version: >=3.8

| Author: Leon Deligny
| Creation: 21 March 2025

"""

# =================================================================================================
#   IMPORTS
# =================================================================================================

import unittest

import numpy as np

from ceasiompy.utils.decorators import log_test
from cpacspy.cpacsfunctions import create_branch
from ceasiompy.StaticStability.staticstability import generate_stab_table

from ceasiompy.utils.ceasiompyutils import (
    current_workflow_dir,
    get_results_directory,
)

from pathlib import Path
from cpacspy.cpacspy import CPACS
from ceasiompy.utils.ceasiompytest import CeasiompyTest

from ceasiompy import log
from ceasiompy.utils.commonpaths import CPACS_FILES_PATH

from ceasiompy.PyAVL import MODULE_NAME


# =================================================================================================
#   CLASSES
# =================================================================================================

class TestStaticStability(CeasiompyTest):

    @classmethod
    def setUpClass(cls):
        cls.cpacs_path = Path(CPACS_FILES_PATH, "D150_simple.xml")
        cls.cpacs = CPACS(cls.cpacs_path)
        cls.wkdir = current_workflow_dir()

        cls.aeromap_empty = cls.cpacs.get_aeromap_by_uid("aeromap_empty")
        cls.aeromap = cls.cpacs.get_aeromap_by_uid("test_apm")
        tixi = cls.cpacs.tixi
        cls.results_dir = get_results_directory(MODULE_NAME, True, cls.wkdir)

        # Test aeromap

        # Test linear regression
        # Remove previous rows
        cls.aeromap.remove_row(alt=0.0, mach=0.3, aos=0.0, aoa=0.0)
        cls.aeromap.remove_row(alt=0.0, mach=0.3, aos=10.0, aoa=0.0)
        cls.aeromap.remove_row(alt=0.0, mach=0.3, aos=0.0, aoa=10.0)
        cls.aeromap.remove_row(alt=0.0, mach=0.3, aos=10.0, aoa=10.0)

        # Add complete ones
        cls.aeromap.add_row(
            alt=0.0, mach=0.3, aos=0.0, aoa=0.0,
            cd=np.nan, cl=np.nan, cs=np.nan,
            cmd=0.002, cml=0.002, cms=0.004,
        )
        cls.aeromap.add_row(
            alt=0.0, mach=0.3, aos=0.0, aoa=10.0,
            cd=np.nan, cl=np.nan, cs=np.nan,
            cmd=0.002, cml=0.002, cms=0.002,
        )
        cls.aeromap.add_row(
            alt=0.0, mach=0.3, aos=10.0, aoa=0.0,
            cd=np.nan, cl=np.nan, cs=np.nan,
            cmd=0.004, cml=0.004, cms=0.004,
        )
        cls.aeromap.add_row(
            alt=0.0, mach=0.3, aos=10.0, aoa=10.0,
            cd=np.nan, cl=np.nan, cs=np.nan,
            cmd=0.004, cml=0.002, cms=0.002,
        )
        log.info(f"cls.aeromap {cls.aeromap}")

        # Test directly values from derivatives
        # Access correct xpath in CPACS file
        increment_map_xpath = f"{cls.aeromap.xpath}/incrementMaps/incrementMap"

        # Ensure the incrementMap elements exist
        create_branch(tixi, f"{increment_map_xpath}/dcmd")
        create_branch(tixi, f"{increment_map_xpath}/dcms")
        create_branch(tixi, f"{increment_map_xpath}/dcml")

        # Add some rows in test_apm aeromap
        tixi.updateTextElement(f"{increment_map_xpath}/dcmd", "-0.002;0.002;-0.002;-0.002")
        tixi.updateTextElement(f"{increment_map_xpath}/dcms", "-0.002;-0.002;-0.002;0.002")
        tixi.updateTextElement(f"{increment_map_xpath}/dcml", "0.002;0.002;-0.002;0.002")

    @log_test
    def test_generate_stab_table(self) -> None:

        # Test Linear Regression
        self.assert_equal_function(
            f=generate_stab_table,
            input_args=(self.cpacs, "test_apm", self.wkdir, True, ),
            expected=([
                [
                    "mach", "alt", "aoa", "aos",
                    "long_stab", "dir_stab", "lat_stab",
                    "comment"
                ],
                [
                    0.3, 0.0, 0.0, 0.0,
                    "Stable", "Stable", "Unstable",
                    "Aircraft is unstable for Lateral axis i.e. Clb >=0. "
                ],
                [
                    0.3, 0.0, 0.0, 10.0,
                    "Stable", "Stable", "Unstable",
                    "Aircraft is unstable for Lateral axis i.e. Clb >=0. "
                ],
                [
                    0.3, 0.0, 10.0, 0.0,
                    "Stable", "Unstable", "Unstable",
                    "Aircraft is unstable for Directional axis "
                    "i.e. Cnb <=0. Aircraft is unstable for Lateral axis i.e. Clb >=0. "
                ],
                [
                    0.3, 0.0, 10.0, 10.0,
                    "Stable", "Unstable", "Unstable",
                    "Aircraft is unstable for Directional axis "
                    "i.e. Cnb <=0. Aircraft is unstable for Lateral axis i.e. Clb >=0. "
                ]
            ])
        )

        # Test data
        self.assert_equal_function(
            f=generate_stab_table,
            input_args=(self.cpacs, "test_apm", self.wkdir, False,),
            expected=([
                [
                    "mach", "alt", "aoa", "aos",
                    "long_stab", "dir_stab", "lat_stab",
                    "comment"
                ],
                [
                    0.3, 0.0, 0.0, 0.0,
                    "Stable", "Stable", "Stable",
                    "Aircraft is stable along all axes."
                ],
                [
                    0.3, 0.0, 0.0, 10.0,
                    "Stable", "Stable", "Unstable",
                    "Aircraft is unstable for Lateral axis i.e. Clb >=0. "
                ],
                [
                    0.3, 0.0, 10.0, 0.0,
                    "Stable", "Unstable", "Stable",
                    "Aircraft is unstable for Directional axis i.e. Cnb <=0. "
                ],
                [
                    0.3, 0.0, 10.0, 10.0,
                    "Unstable", "Stable", "Stable",
                    "Aircraft is unstable for Longitudinal axis i.e. Cma >=0. "
                ]
            ])

        )

# =================================================================================================
#    MAIN
# =================================================================================================


if __name__ == "__main__":
    unittest.main(verbosity=0)
