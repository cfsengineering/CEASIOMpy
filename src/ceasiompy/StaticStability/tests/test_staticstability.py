"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Test functions for StaticStability module.

| Author: Leon Deligny
| Creation: 21 March 2025

"""

# =================================================================================================
#   IMPORTS
# =================================================================================================

import unittest
import tempfile

from ceasiompy.utils.decorators import log_test
from cpacspy.cpacsfunctions import create_branch
from ceasiompy.utils.ceasiompyutils import current_workflow_dir
from ceasiompy.StaticStability.func.utils import markdownpy_to_markdown
from ceasiompy.StaticStability.staticstability import (
    main,
    generate_stab_table,
)

from pathlib import Path
from cpacspy.cpacspy import AeroMap
from markdownpy.markdownpy import MarkdownDoc
from ceasiompy.utils.ceasiompytest import CeasiompyTest

from ceasiompy import log
from ceasiompy.StaticStability import (
    MODULE_NAME,
    STATICSTABILITY_LR_XPATH,
)

# =================================================================================================
#   CLASSES
# =================================================================================================


class TestStaticStability(CeasiompyTest):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.wkdir = current_workflow_dir()
        cls.aeromap_empty: AeroMap = cls.test_cpacs.get_aeromap_by_uid("aeromap_empty")
        cls.aeromap: AeroMap = cls.test_cpacs.get_aeromap_by_uid("test_apm")
        tixi = cls.test_cpacs.tixi

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
    def test_generate_stab_table(self) -> None:
        # Test Linear Regression
        self.assert_equal_function(
            f=generate_stab_table,
            input_args=(self.test_cpacs, "test_apm", self.wkdir, True, ),
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
            input_args=(self.test_cpacs, "test_apm", self.wkdir, False,),
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
    def test_main_creates_markdown(self):

        create_branch(self.test_cpacs.tixi, STATICSTABILITY_LR_XPATH)
        self.test_cpacs.tixi.updateBooleanElement(STATICSTABILITY_LR_XPATH, False)

        with tempfile.TemporaryDirectory() as tmpdir:
            main(self.test_cpacs, Path(tmpdir))
            md_path = Path(tmpdir, f"{MODULE_NAME}.md")
            with open(md_path, "r") as f:
                content = f.read()
                self.assertIn("StaticStability", content)
                self.assertIn("Static stability of 'test_apm' aeromap.", content)

    @log_test
    def test_markdownpy_to_markdown(self):
        # Create a dummy MarkdownDoc in a temp file
        with tempfile.TemporaryDirectory() as tmpdir:
            md_path = Path(tmpdir, "test.md")
            md = MarkdownDoc(md_path)

            # Simple table to test
            table = [
                ["col1", "col2"],
                ["val1", "val2"],
                ["val3", "val4"]
            ]

            markdownpy_to_markdown(md, table)
            md.save()

            # Check file content
            with open(md_path, "r") as f:
                content = f.read()
                self.assertIn("|col1|col2|", content)
                self.assertIn("|val1|val2|", content)
                self.assertIn("|val3|val4|", content)


# =================================================================================================
#    MAIN
# =================================================================================================


if __name__ == "__main__":
    unittest.main(verbosity=0)
