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
from ceasiompy.staticstability.func.extractdata import compute_stab_table
from ceasiompy.staticstability.staticstability import (
    main as staticstability,
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
    def test_compute_stab_table(self: TestStaticStability) -> None:
        # Test direct derivatives mode
        self.assert_equal_function(
            f=compute_stab_table,
            input_args=(self.cpacs, "test_apm", self.wkdir,),
            expected=(True, ),
        )

    @log_test
    def test_main_raises_when_all_aeromaps_fail(self: TestStaticStability) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            with self.assertRaises(RuntimeError) as err:
                staticstability(self.test_cpacs, Path(tmpdir))
            self.assertIn("StaticStability failed", str(err.exception))


# Main
if __name__ == "__main__":
    main(verbosity=0)
