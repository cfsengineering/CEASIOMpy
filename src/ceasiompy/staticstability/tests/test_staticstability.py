"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Test functions for StaticStability module.
"""

# Futures
from __future__ import annotations

# Imports

import unittest
import tempfile

from ceasiompy.utils.decorators import log_test
from cpacspy.cpacsfunctions import create_branch
from ceasiompy.utils.ceasiompyutils import (
    current_workflow_dir,
    get_results_directory,
)
from ceasiompy.staticstability.func.utils import markdownpy_to_markdown
from ceasiompy.staticstability.staticstability import (
    main,
    generate_stab_table,
)

from pathlib import Path
from markdownpy.markdownpy import MarkdownDoc
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
        print(generate_stab_table(self.cpacs, "test_apm", self.wkdir, True))
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
                    "Aircraft is unstable for Lateral axis i.e. Clb >=0. ",
                ],
                [
                    0.3, 0.0, 10.0, 0.0,
                    "Stable", "Unstable", "Unstable",
                    "Aircraft is unstable for Directional axis i.e. Cnb <=0. "
                    "Aircraft is unstable for Lateral axis i.e. Clb >=0. "
                ],
                [
                    0.3, 0.0, 10.0, 10.0,
                    "Stable", "Unstable", "Unstable",
                    "Aircraft is unstable for Directional axis i.e. Cnb <=0. "
                    "Aircraft is unstable for Lateral axis i.e. Clb >=0. "
                ],
                [
                    0.5, 1000.0, 0.0, 0.0,
                    "Stable", "Stable", "Unstable",
                    "Aircraft is unstable for Lateral axis i.e. Clb >=0. "
                ],
                [
                    0.5, 1000.0, 0.0, 10.0,
                    "Stable", "Stable", "Unstable",
                    "Aircraft is unstable for Lateral axis i.e. Clb >=0. ",
                ],
                [
                    0.5, 1000.0, 10.0, 0.0,
                    "Stable", "Unstable", "Unstable",
                    "Aircraft is unstable for Directional axis i.e. Cnb <=0. "
                    "Aircraft is unstable for Lateral axis i.e. Clb >=0. "
                ],
                [
                    0.5, 1000.0, 10.0, 10.0,
                    "Stable", "Unstable", "Unstable",
                    "Aircraft is unstable for Directional axis i.e. Cnb <=0. "
                    "Aircraft is unstable for Lateral axis i.e. Clb >=0. "
                ],
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
                ],
                [
                    0.5, 1000.0, 0.0, 0.0,
                    "Stable", "Stable", "Stable",
                    "Aircraft is stable along all axes."
                ],
                [
                    0.5, 1000.0, 0.0, 10.0,
                    "Stable", "Stable", "Unstable",
                    "Aircraft is unstable for Lateral axis i.e. Clb >=0. "
                ],
                [
                    0.5, 1000.0, 10.0, 0.0,
                    "Stable", "Unstable", "Stable",
                    "Aircraft is unstable for Directional axis i.e. Cnb <=0. "
                ],
                [
                    0.5, 1000.0, 10.0, 10.0,
                    "Unstable", "Stable", "Stable",
                    "Aircraft is unstable for Longitudinal axis i.e. Cma >=0. "
                ]
            ])

        )

    @log_test
    def test_main_creates_markdown(self: TestStaticStability) -> None:
        create_branch(self.test_cpacs.tixi, STATICSTABILITY_LR_XPATH)

        # Use Linear Regression (test_apm)
        self.test_cpacs.tixi.updateBooleanElement(STATICSTABILITY_LR_XPATH, True)

        with tempfile.TemporaryDirectory() as tmpdir:
            main(self.test_cpacs, Path(tmpdir))
            md_path = Path(tmpdir, f"{MODULE_NAME}.md")
            with open(md_path, "r") as f:
                content = f.read()
                self.assertIn("mach", content)
                self.assertIn("alt", content)
                self.assertIn("aoa", content)
                self.assertIn("aos", content)

    @log_test
    def test_markdownpy_to_markdown(self: TestStaticStability) -> None:
        # Create a dummy MarkdownDoc in a temp file
        with tempfile.TemporaryDirectory() as tmpdir:
            md_path = Path(tmpdir, "test.md")
            md = MarkdownDoc(md_path)

            # Simple table to test
            table = [["col1", "col2"], ["val1", "val2"], ["val3", "val4"]]

            markdownpy_to_markdown(md, table)
            md.save()

            # Check file content
            with open(md_path, "r") as f:
                content = f.read()
                self.assertIn("|col1|col2|", content)
                self.assertIn("|val1|val2|", content)
                self.assertIn("|val3|val4|", content)


# Main
if __name__ == "__main__":
    unittest.main(verbosity=0)
