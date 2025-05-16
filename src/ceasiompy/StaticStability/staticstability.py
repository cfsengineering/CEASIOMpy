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
from ceasiompy.utils.ceasiompyutils import call_main
from ceasiompy.StaticStability.func.utils import markdownpy_to_markdown
from ceasiompy.StaticStability.func.extractdata import generate_stab_table

from cpacspy.cpacspy import CPACS
from markdownpy.markdownpy import MarkdownDoc

from ceasiompy import log
from ceasiompy.StaticStability import MODULE_NAME
from ceasiompy.utils.commonxpaths import STATICSTABILITY_LR_XPATH

# =================================================================================================
#    MAIN
# =================================================================================================


def main(cpacs: CPACS, wkdir: Path) -> None:
    """
    Analyses longitudinal, directional and lateral stability
    from the data of a CPACS file.

    Args:
        cpacs (CPACS): Input CPACS file.
        wkdir (str): Results directory.

    """

    tixi = cpacs.tixi
    md = MarkdownDoc(Path(wkdir, f"{MODULE_NAME}.md"))
    md.h2(MODULE_NAME)

    for aeromap_uid in cpacs.get_aeromap_uid_list():
        if not str(aeromap_uid) == "aeromap_empty":
            log_msg = f"Static stability of '{aeromap_uid}' aeromap."
            log.info(log_msg)
            md.h4(log_msg)

            lr_bool = get_value(tixi, STATICSTABILITY_LR_XPATH)
            table = generate_stab_table(cpacs, aeromap_uid, wkdir, lr_bool)
            markdownpy_to_markdown(md, table)

    md.save()


if __name__ == "__main__":
    call_main(main, MODULE_NAME)
