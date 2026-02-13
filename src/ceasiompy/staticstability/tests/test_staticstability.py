"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Test functions for StaticStability module.
"""

# Futures
from __future__ import annotations

# Imports

import tempfile

from ceasiompy.utils.decorators import log_test
from cpacspy.cpacsfunctions import create_branch
from ceasiompy.utils.ceasiompyutils import (
    current_workflow_dir,
    get_results_directory,
)
from ceasiompy.staticstability.staticstability import (
    main as staticstability,
    generate_stab_table,
)

from pathlib import Path
from unittest import main
from ceasiompy.utils.ceasiompytest import CeasiompyTest
from cpacspy.cpacspy import (
    CPACS,
    AeroMap,
)

from ceasiompy import log
from ceasiompy.utils.commonpaths import CPACS_FILES_PATH
from ceasiompy.staticstability import (
    MODULE_NAME,
    STATICSTABILITY_LR_XPATH,
)

# =================================================================================================
#   CLASSES
# =================================================================================================


class TestStaticStability(CeasiompyTest):

    @classmethod
    def setUpClass(cls: TestStaticStability) -> None:
        super().setUpClass()
        cls.cpacs_path = Path(CPACS_FILES_PATH, "d150.xml")
        cls.cpacs = CPACS(cls.cpacs_path)
        cls.wkdir = current_workflow_dir()

        cls.aeromap_empty: AeroMap = cls.cpacs.get_aeromap_by_uid("aeromap_empty")
        cls.aeromap: AeroMap = cls.cpacs.get_aeromap_by_uid("test_apm")
        tixi = cls.cpacs.tixi
        cls.results_dir = get_results_directory(MODULE_NAME, True, cls.wkdir)

        log.info(f"cls.aeromap {cls.aeromap}")

        # Test directly values from derivatives
        # Access correct xpath in CPACS file
        increment_map_xpath = f"{cls.aeromap.xpath}/incrementMaps/incrementMap"

        # Ensure the incrementMap elements exist
        create_branch(tixi, f"{increment_map_xpath}/dcmd")
        create_branch(tixi, f"{increment_map_xpath}/dcms")
        create_branch(tixi, f"{increment_map_xpath}/dcml")

        # Add some rows in test_apm aeromap
        tixi.updateTextElement(
            f"{increment_map_xpath}/dcmd",
            "-0.002;0.002;-0.002;-0.002;-0.002;0.002;-0.002;-0.002"
        )
        tixi.updateTextElement(
            f"{increment_map_xpath}/dcms",
            "-0.002;-0.002;-0.002;0.002;-0.002;-0.002;-0.002;0.002"
        )
        tixi.updateTextElement(
            f"{increment_map_xpath}/dcml",
            "0.002;0.002;-0.002;0.002;0.002;0.002;-0.002;0.002"
        )

    @log_test
    def test_generate_stab_table(self: TestStaticStability) -> None:
        # Test direct derivatives mode
        self.assert_equal_function(
            f=generate_stab_table,
            input_args=(self.cpacs, "test_apm", self.wkdir, False,),
            expected=([
                [
                    "mach", "alt", "aoa", "aos",
                    "long_stab", "dir_stab", "lat_stab"
                ],
                [
                    0.3, 0.0, 0.0, 0.0,
                    "Stable", "Stable", "Stable",
                ],
                [
                    0.3, 0.0, 0.0, 10.0,
                    "Stable", "Stable", "Clb >= 0.",
                ],
                [
                    0.3, 0.0, 10.0, 0.0,
                    "Stable", "Cnb <= 0.", "Stable",
                ],
                [
                    0.3, 0.0, 10.0, 10.0,
                    "Cma >= 0.", "Stable", "Stable",
                ],
                [
                    0.5, 1000.0, 0.0, 0.0,
                    "Stable", "Stable", "Stable",
                ],
                [
                    0.5, 1000.0, 0.0, 10.0,
                    "Stable", "Stable", "Clb >= 0.",
                ],
                [
                    0.5, 1000.0, 10.0, 0.0,
                    "Stable", "Cnb <= 0.", "Stable",
                ],
                [
                    0.5, 1000.0, 10.0, 10.0,
                    "Cma >= 0.", "Stable", "Stable",
                ]
            ])

        )

    @log_test
    def test_generate_stab_table_lr_raises_type_error(self: TestStaticStability) -> None:
        with self.assertRaises(TypeError):
            generate_stab_table(self.cpacs, "test_apm", self.wkdir, True)

    @log_test
    def test_main_raises_when_all_aeromaps_fail(self: TestStaticStability) -> None:
        create_branch(self.test_cpacs.tixi, STATICSTABILITY_LR_XPATH)
        self.test_cpacs.tixi.updateBooleanElement(STATICSTABILITY_LR_XPATH, True)

        with tempfile.TemporaryDirectory() as tmpdir:
            with self.assertRaises(RuntimeError) as err:
                staticstability(self.test_cpacs, Path(tmpdir))
            self.assertIn("StaticStability failed", str(err.exception))


# Main
if __name__ == "__main__":
    main(verbosity=0)
