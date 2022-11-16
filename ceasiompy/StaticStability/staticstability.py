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
from cpacspy.cpacspy import CPACS
from cpacspy.cpacsfunctions import (
    add_string_vector,
    create_branch,
    get_string_vector,
    get_value_or_default,
)
from ceasiompy.utils.ceasiompyutils import get_results_directory
from markdownpy.markdownpy import MarkdownDoc
from ceasiompy.utils.ceasiomlogger import get_logger
from ceasiompy.utils.commonxpath import STABILITY_XPATH
from ceasiompy.utils.moduleinterfaces import (
    check_cpacs_input_requirements,
    get_toolinput_file_path,
    get_tooloutput_file_path,
)

log = get_logger()

MODULE_DIR = Path(__file__).parent
MODULE_NAME = MODULE_DIR.name


# =================================================================================================
#   FUNCTIONS
# =================================================================================================


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

    aeromap_to_analyze_xpath = STABILITY_XPATH + "/aeroMapToAnalyze"

    aeromap_uid_list = []

    try:
        aeromap_uid_list = get_string_vector(cpacs.tixi, aeromap_to_analyze_xpath)
    except ValueError:  # if aeroMapToPlot is not define, select all aeromaps
        aeromap_uid_list = cpacs.get_aeromap_uid_list()
        create_branch(cpacs.tixi, aeromap_to_analyze_xpath)
        add_string_vector(cpacs.tixi, aeromap_to_analyze_xpath, aeromap_uid_list)

    long_stab_xpath = STABILITY_XPATH + "/stabilityToCheck/longitudinal"
    longitudinal_stability = get_value_or_default(cpacs.tixi, long_stab_xpath, True)

    dir_stab_xpath = STABILITY_XPATH + "/stabilityToCheck/directional"
    directional_stability = get_value_or_default(cpacs.tixi, dir_stab_xpath, True)

    lat_stab_xpath = STABILITY_XPATH + "/stabilityToCheck/lateral"
    lateral_stability = get_value_or_default(cpacs.tixi, lat_stab_xpath, True)

    STABILITY_DICT = {True: "Stable", False: "Unstable", None: "Not define"}

    for aeromap_uid in aeromap_uid_list:

        md.h4(f"Static stability of '{aeromap_uid}' aeromap")
        aeromap = cpacs.get_aeromap_by_uid(aeromap_uid)

        df = aeromap.df.groupby(["machNumber", "altitude"])

        for (mach, alt), _ in df:

            md.h6(f"@ Ma={mach} and alt={alt}m")

            if longitudinal_stability:
                stable, msg = aeromap.check_longitudinal_stability(alt=alt, mach=mach)
                md.p(f"- Longitudinal: {STABILITY_DICT[stable]}  {msg}", no_new_line=True)

            if directional_stability:
                stable, msg = aeromap.check_directional_stability(alt=alt, mach=mach)
                md.p(f"- Directional: {STABILITY_DICT[stable]}  {msg}", no_new_line=True)

            if lateral_stability:
                stable, msg = aeromap.check_lateral_stability(alt=alt, mach=mach)
                md.p(f"- Lateral: {STABILITY_DICT[stable]}  {msg}", no_new_line=True)

    cpacs.save_cpacs(cpacs_out_path, overwrite=True)
    md.save()


# =================================================================================================
#    MAIN
# =================================================================================================


def main(cpacs_path, cpacs_out_path):

    log.info("----- Start of " + MODULE_NAME + " -----")

    # check_cpacs_input_requirements(cpacs_path)

    static_stability_analysis(cpacs_path, cpacs_out_path)

    log.info("----- End of " + MODULE_NAME + " -----")


if __name__ == "__main__":

    cpacs_path = get_toolinput_file_path(MODULE_NAME)
    cpacs_out_path = get_tooloutput_file_path(MODULE_NAME)

    main(cpacs_path, cpacs_out_path)
