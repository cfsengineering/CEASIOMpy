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

    aeromap_uid_list = get_aeromap_list_from_xpath(cpacs, STABILITY_AEROMAP_TO_ANALYZE_XPATH)
    longitudinal_stab = get_value_or_default(cpacs.tixi, CHECK_LONGITUDINAL_STABILITY_XPATH, True)
    directional_stab = get_value_or_default(cpacs.tixi, CHECK_DIRECTIONAL_STABILITY_XPATH, False)
    lateral_stab = get_value_or_default(cpacs.tixi, CHECK_LATERAL_STABILITY_XPATH, False)

    STABILITY_DICT = {True: "Stable", False: "Unstable", None: "Not define"}

    for aeromap_uid in aeromap_uid_list:

        md.h4(f"Static stability of '{aeromap_uid}' aeromap")
        aeromap = cpacs.get_aeromap_by_uid(aeromap_uid)

        df = aeromap.df.groupby(["machNumber", "altitude", "angleOfSideslip"])

        stability_table = [["mach", "alt", "aos", "Longitudinal stability", "Comment"]]

        for (mach, alt, aos), _ in df:

            if longitudinal_stab:
                stable, msg = aeromap.check_longitudinal_stability(alt=alt, mach=mach, aos=aos)

                if stable is not None:
                    stability_table.append(
                        [str(mach), str(alt), str(aos), STABILITY_DICT[stable], msg]
                    )

        if longitudinal_stab and len(stability_table) > 1:
            md_table = Table(stability_table)
            md.p(md_table.write())

        # Directional

        df = aeromap.df.groupby(["machNumber", "altitude", "angleOfAttack"])

        stability_table = [["mach", "alt", "aoa", "Directional stability", "Comment"]]

        for (mach, alt, aoa), _ in df:

            if directional_stab:
                stable, msg = aeromap.check_directional_stability(alt=alt, mach=mach, aoa=aoa)

                if stable is not None:
                    stability_table.append(
                        [str(mach), str(alt), str(aoa), STABILITY_DICT[stable], msg]
                    )

        if directional_stab and len(stability_table) > 1:

            md_table = Table(stability_table)
            md.p(md_table.write())

        # Lateral

        stability_table = [["mach", "alt", "aoa", "Lateral stability", "Comment"]]

        for (mach, alt, aoa), _ in df:

            if lateral_stab:
                stable, msg = aeromap.check_lateral_stability(alt=alt, mach=mach, aoa=aoa)

                if stable is not None:
                    stability_table.append(
                        [str(mach), str(alt), str(aoa), STABILITY_DICT[stable], msg]
                    )

        if lateral_stab and len(stability_table) > 1:

            md_table = Table(stability_table)
            md.p(md_table.write())

    cpacs.save_cpacs(cpacs_out_path, overwrite=True)
    md.save()


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
