"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Static stability module

| Author: Leon Deligny
| Creation: 2025-01-27

"""

# =================================================================================================
#   IMPORTS
# =================================================================================================

from pathlib import Path

from cpacspy.cpacsfunctions import get_value
from ceasiompy.StaticStability.func.utils import markdownpy_to_markdown
from ceasiompy.StaticStability.func.extractdata import generate_stab_table

from cpacspy.cpacspy import CPACS
from markdownpy.markdownpy import MarkdownDoc
from ceasiompy.utils.guisettings import GUISettings

from ceasiompy import log
from ceasiompy.StaticStability import (
    MODULE_NAME,
    STATICSTABILITY_LR_XPATH,
)

# =================================================================================================
#    MAIN
# =================================================================================================


def main(
    cpacs: CPACS,
    gui_settings: GUISettings,
    results_dir: Path,
) -> None:
    """
    Analyses longitudinal, directional and lateral stability
    from the data of a CPACS file.

    Args:
        cpacs (CPACS): Input CPACS file.
        results_dir (str): Results directory.

    """

    md = MarkdownDoc(Path(results_dir, f"{MODULE_NAME}.md"))
    md.h2(MODULE_NAME)

    for aeromap_uid in cpacs.get_aeromap_uid_list():
        try:
            log_msg = f"Static stability of '{aeromap_uid}' aeromap."
            log.info(log_msg)
            md.h4(log_msg)

            lr_bool = get_value(gui_settings.tixi, STATICSTABILITY_LR_XPATH)
            table = generate_stab_table(cpacs, aeromap_uid, results_dir, lr_bool)
            markdownpy_to_markdown(md, table)
        except Exception as e:
            log.warning(
                f"Could not compute static stability of aeromap {aeromap_uid} " f"due to error {e}"
            )

    md.save()
