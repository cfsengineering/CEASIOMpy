"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Test functions for 'StabilityStatic/staticstability.py'

Python version: >=3.8

| Author: Aidan Jungo
| Creation: 2022-11-14

TODO:

"""

# =================================================================================================
#   IMPORTS
# =================================================================================================

from pathlib import Path

from ceasiompy.StaticStability.staticstability import (
    generate_directional_stab_table,
    generate_lateral_stab_table,
    generate_longitudinal_stab_table,
    static_stability_analysis,
)
from ceasiompy.utils.commonpaths import CPACS_FILES_PATH
from cpacspy.cpacspy import CPACS

MODULE_DIR = Path(__file__).parent
MODULE_NAME = MODULE_DIR.name
CPACS_IN = Path(CPACS_FILES_PATH, "D150_simple.xml")
CPACS_OUT_PATH = Path(MODULE_DIR, "D150_simple_staticstability_test_output.xml")


# =================================================================================================
#   CLASSES
# =================================================================================================


# =================================================================================================
#   FUNCTIONS
# =================================================================================================


class TestGenerateTable:

    cpacs = CPACS(CPACS_IN)
    aeromap_empty = cpacs.get_aeromap_by_uid("aeromap_empty")
    aeromap = cpacs.get_aeromap_by_uid("test_apm")

    def test_generate_longitudinal_stab_table(self):
        """Test function 'generate_longitudinal_stab_table'"""

        table = generate_longitudinal_stab_table(self.aeromap_empty)
        assert len(table) == 1

        table = generate_longitudinal_stab_table(self.aeromap)
        assert table == [
            ["mach", "alt", "aos", "Longitudinal stability", "Comment"],
            ["0.3", "0.0", "0.0", "Unstable", ""],
            ["0.3", "0.0", "10.0", "Unstable", ""],
        ]

        self.aeromap.add_row(mach=0.3, alt=0, aos=5.0, aoa=0, cd=0.001, cl=1.1, cs=0.22, cms=0.22)
        self.aeromap.add_row(mach=0.3, alt=0, aos=5.0, aoa=4, cd=0.001, cl=1.1, cs=0.22, cms=0.12)
        table = generate_longitudinal_stab_table(self.aeromap)
        assert table == [
            ["mach", "alt", "aos", "Longitudinal stability", "Comment"],
            ["0.3", "0.0", "0.0", "Unstable", ""],
            ["0.3", "0.0", "5.0", "Stable", ""],
            ["0.3", "0.0", "10.0", "Unstable", ""],
        ]

    def test_generate_directional_stab_table(self):
        """Test function 'generate_directional_stab_table'"""

        table = generate_directional_stab_table(self.aeromap_empty)
        assert len(table) == 1

        table = generate_directional_stab_table(self.aeromap)
        assert table == [
            ["mach", "alt", "aoa", "Directional stability", "Comment"],
            ["0.3", "0.0", "0.0", "Unstable", ""],
            ["0.3", "0.0", "10.0", "Unstable", ""],
        ]

        self.aeromap.add_row(mach=0.3, alt=0, aos=0.0, aoa=5.0, cd=0.001, cl=1.1, cml=-0.22)
        self.aeromap.add_row(mach=0.3, alt=0, aos=5.0, aoa=5.0, cd=0.001, cl=1.1, cml=0.12)
        table = generate_directional_stab_table(self.aeromap)
        assert table == [
            ["mach", "alt", "aoa", "Directional stability", "Comment"],
            ["0.3", "0.0", "0.0", "Unstable", ""],
            ["0.3", "0.0", "5.0", "Stable", ""],
            ["0.3", "0.0", "10.0", "Unstable", ""],
        ]

    def test_generate_lateral_stab_table(self):
        """Test function 'generate_lateral_stab_table'"""

        table = generate_lateral_stab_table(self.aeromap_empty)
        assert len(table) == 1

        table = generate_lateral_stab_table(self.aeromap)
        assert table == [
            ["mach", "alt", "aoa", "Lateral stability", "Comment"],
            ["0.3", "0.0", "0.0", "Unstable", ""],
            ["0.3", "0.0", "5.0", "Unstable", ""],
            ["0.3", "0.0", "10.0", "Unstable", ""],
        ]

        self.aeromap.add_row(mach=0.3, alt=0, aos=0.0, aoa=15.0, cd=0.001, cl=1.1, cmd=0.22)
        self.aeromap.add_row(mach=0.3, alt=0, aos=5.0, aoa=15.0, cd=0.001, cl=1.1, cmd=-0.12)
        self.aeromap.add_row(mach=0.4, alt=0, aos=0.0, aoa=15.0, cd=0.001, cl=1.1, cmd=0.01)
        self.aeromap.add_row(mach=0.4, alt=0, aos=5.0, aoa=15.0, cd=0.001, cl=1.1, cmd=0.01)
        table = generate_lateral_stab_table(self.aeromap)
        assert table == [
            ["mach", "alt", "aoa", "Lateral stability", "Comment"],
            ["0.3", "0.0", "0.0", "Unstable", ""],
            ["0.3", "0.0", "5.0", "Unstable", ""],
            ["0.3", "0.0", "10.0", "Unstable", ""],
            ["0.3", "0.0", "15.0", "Stable", ""],
            ["0.4", "0.0", "15.0", "Unstable", "Neutral stability"],
        ]


def test_static_stability_analysis():
    """Test Function 'static_stability_analysis'"""

    result_markdown_file = Path(MODULE_DIR, "Results", "Stability", "Static_stability.md")

    if result_markdown_file.exists():
        result_markdown_file.unlink()

    if CPACS_OUT_PATH.exists():
        CPACS_OUT_PATH.unlink()

    static_stability_analysis(CPACS_IN, CPACS_OUT_PATH)

    assert CPACS_OUT_PATH.exists()
    assert result_markdown_file.exists()

    if result_markdown_file.exists():
        result_markdown_file.unlink()

    if CPACS_OUT_PATH.exists():
        CPACS_OUT_PATH.unlink()


# =================================================================================================
#    MAIN
# =================================================================================================

if __name__ == "__main__":

    print("Running test_staticstability")
    print("To run test use the following command:")
    print(">> pytest -v")
