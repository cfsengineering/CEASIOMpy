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
    generate_stab_table,
    static_stability_analysis,
)
from ceasiompy.utils.ceasiompyutils import get_results_directory
from ceasiompy.utils.commonpaths import CPACS_FILES_PATH
from cpacspy.cpacspy import CPACS

MODULE_DIR = Path(__file__).parent
MODULE_NAME = MODULE_DIR.name
CPACS_IN = Path(CPACS_FILES_PATH, "D150_simple.xml")
CPACS_OUT_PATH = Path(MODULE_DIR, "D150_simple_staticstability_test_output.xml")


# =================================================================================================
#   FUNCTIONS
# =================================================================================================

def test_static_stability_analysis():
    """
    Test Function 'static_stability_analysis'
    """

    results_dir = get_results_directory("StaticStability")
    result_markdown_file = Path(results_dir, "Static_stability.md")

    if result_markdown_file.exists():
        result_markdown_file.unlink()

    if CPACS_OUT_PATH.exists():
        CPACS_OUT_PATH.unlink()

    static_stability_analysis(CPACS_IN, CPACS_OUT_PATH)

    assert CPACS_OUT_PATH.exists()
    assert result_markdown_file.exists()

    if CPACS_OUT_PATH.exists():
        CPACS_OUT_PATH.unlink()


# =================================================================================================
#   CLASSES
# =================================================================================================

class TestStaticStability:
    @classmethod
    def setup_class(cls):
        cls.cpacs = CPACS("/users/disk12/cfse2/Leon/CEASIOMpy_Leon/CEASIOMpy/test_files/CPACSfiles/D150_simple.xml")
        cls.aeromap_empty = cls.cpacs.get_aeromap_by_uid("aeromap_empty")
        cls.aeromap = cls.cpacs.get_aeromap_by_uid("test_apm")

    def test_generate_stab_table(self):
        """Test function 'generate_stab_table'"""

        '''
        print(self.aeromap_empty)

        print("First test on empty aeromap")
        table = generate_stab_table(self.aeromap_empty)
        assert len(table) == 1
        '''
        
        print("Adding rows")
        self.aeromap.add_row(mach=0.3, alt=0, aos=5.0, aoa=0, cma=-0.002, cnb=0.002, clb=-0.002)
        self.aeromap.add_row(mach=0.3, alt=0, aos=5.0, aoa=0, cma=0.002, cnb=0.002, clb=-0.002)
        self.aeromap.add_row(mach=0.3, alt=0, aos=5.0, aoa=0, cma=-0.002, cnb=-0.002, clb=-0.002)
        self.aeromap.add_row(mach=0.3, alt=0, aos=5.0, aoa=0, cma=-0.002, cnb=0.002, clb=0.002)
        
        print("Generating table")
        table = generate_stab_table(self.aeromap)
        assert table == [
            ["mach", "alt", "aoa", "aos", "cma", "cnb", "clb" "Longitudinal stability", "Directional stability", "Lateral stability", "Comment"],
            ["0.3", "0.0", "0.0", "5.0", "-0.002", "0.002", "-0.002", "Stable", "Stable", "Stable", "Aircraft is stable"],
            ["0.3", "0.0", "0.0", "5.0", "0.002", "0.002", "-0.002", "Unstable", "Stable", "Stable", "Aircraft is unstable"],
            ["0.3", "0.0", "0.0", "5.0", "-0.002", "-0.002", "-0.002", "Stable", "Unstable", "Stable", "Aircraft is unstable"],
            ["0.3", "0.0", "0.0", "5.0", "-0.002", "0.002", "0.002", "Stable", "Stable", "Unstable", "Aircraft is unstable"],
        ]

# =================================================================================================
#    MAIN
# =================================================================================================

if __name__ == "__main__":

    print("Running test_staticstability")
    print("To run test use the following command:")
    print(">> pytest -v")