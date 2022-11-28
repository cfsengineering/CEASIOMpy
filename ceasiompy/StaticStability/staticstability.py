"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Static stability module

Python version: >=3.8

| Author: Aidan Jungo
| Creation: 2022-11-14

TODO:

"""

# =================================================================================================
#   IMPORTS
# =================================================================================================

from pathlib import Path

from ceasiompy.utils.ceasiomlogger import get_logger
from ceasiompy.utils.ceasiompyutils import get_aeromap_list_from_xpath, get_results_directory
from ceasiompy.utils.commonxpath import (
    CHECK_DIRECTIONAL_STABILITY_XPATH,
    CHECK_LATERAL_STABILITY_XPATH,
    CHECK_LONGITUDINAL_STABILITY_XPATH,
    STABILITY_AEROMAP_TO_ANALYZE_XPATH,
)
from ceasiompy.utils.moduleinterfaces import (
    check_cpacs_input_requirements,
    get_toolinput_file_path,
    get_tooloutput_file_path,
)
from cpacspy.cpacsfunctions import get_value_or_default
from cpacspy.cpacspy import CPACS
from markdownpy.markdownpy import MarkdownDoc, Table

log = get_logger()

MODULE_DIR = Path(__file__).parent
MODULE_NAME = MODULE_DIR.name

STABILITY_DICT = {True: "Stable", False: "Unstable", None: "Not define"}

# =================================================================================================
#   FUNCTIONS
# =================================================================================================


def generate_longitudinal_stab_table(aeromap):
    """Generate the Markdownpy Table for the longitudinal stability to show in the results.

    Args:
        aeromap (aeromap object): cpacspy aeromap object
    """

    stability_table = [["mach", "alt", "aos", "Longitudinal stability", "Comment"]]

    for (mach, alt, aos), _ in aeromap.df.groupby(["machNumber", "altitude", "angleOfSideslip"]):
        stable, msg = aeromap.check_longitudinal_stability(alt=alt, mach=mach, aos=aos)

        if stable is None:
            continue

        stability_table.append([str(mach), str(alt), str(aos), STABILITY_DICT[stable], msg])

    return stability_table


def generate_directional_stab_table(aeromap):
    """Generate the Markdownpy Table for the directional stability to show in the results.

    Args:
        aeromap (aeromap object): cpacspy aeromap object
    """

    stability_table = [["mach", "alt", "aoa", "Directional stability", "Comment"]]

    for (mach, alt, aoa), _ in aeromap.df.groupby(["machNumber", "altitude", "angleOfAttack"]):
        stable, msg = aeromap.check_directional_stability(alt=alt, mach=mach, aoa=aoa)

        if stable is None:
            continue

        stability_table.append([str(mach), str(alt), str(aoa), STABILITY_DICT[stable], msg])

    return stability_table


def generate_lateral_stab_table(aeromap):
    """Generate the Markdownpy Table for the lateral stability to show in the results.

    Args:
        aeromap (aeromap object): cpacspy aeromap object
    """

    stability_table = [["mach", "alt", "aoa", "Lateral stability", "Comment"]]

    for (mach, alt, aoa), _ in aeromap.df.groupby(["machNumber", "altitude", "angleOfAttack"]):
        stable, msg = aeromap.check_lateral_stability(alt=alt, mach=mach, aoa=aoa)

        if stable is None:
            continue

        stability_table.append([str(mach), str(alt), str(aoa), STABILITY_DICT[stable], msg])

    return stability_table


def static_stability_analysis(cpacs_path, cpacs_out_path):
    """Function 'static_stability_analysis' analyses longitudinal, directional and lateral
    stability.

    Args:
        cpacs_path (str): Path to CPACS file
        cpacs_out_path (str):Path to CPACS output file

    """

    cpacs = CPACS(cpacs_path)

    results_dir = get_results_directory("StaticStability")
    md = MarkdownDoc(Path(results_dir, "Static_stability.md"))
    md.h2("Static stability")

    for aeromap_uid in get_aeromap_list_from_xpath(cpacs, STABILITY_AEROMAP_TO_ANALYZE_XPATH):

        md.h4(f"Static stability of '{aeromap_uid}' aeromap")
        aeromap = cpacs.get_aeromap_by_uid(aeromap_uid)

        if get_value_or_default(cpacs.tixi, CHECK_LONGITUDINAL_STABILITY_XPATH, True):

            table = generate_longitudinal_stab_table(aeromap)
            if len(table) > 1:
                md.p(Table(table).write())

        if get_value_or_default(cpacs.tixi, CHECK_DIRECTIONAL_STABILITY_XPATH, False):

            table = generate_directional_stab_table(aeromap)
            if len(table) > 1:
                md.p(Table(table).write())

        if get_value_or_default(cpacs.tixi, CHECK_LATERAL_STABILITY_XPATH, False):

            table = generate_lateral_stab_table(aeromap)
            if len(table) > 1:
                md.p(Table(table).write())

    md.save()
    cpacs.save_cpacs(cpacs_out_path, overwrite=True)


# =================================================================================================
#    MAIN
# =================================================================================================


def main(cpacs_path, cpacs_out_path):

    log.info("----- Start of " + MODULE_NAME + " -----")

    check_cpacs_input_requirements(cpacs_path)

    static_stability_analysis(cpacs_path, cpacs_out_path)

    log.info("----- End of " + MODULE_NAME + " -----")


if __name__ == "__main__":

    cpacs_path = get_toolinput_file_path(MODULE_NAME)
    cpacs_out_path = get_tooloutput_file_path(MODULE_NAME)

    main(cpacs_path, cpacs_out_path)
