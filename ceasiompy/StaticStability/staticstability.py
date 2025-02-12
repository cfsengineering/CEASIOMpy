"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Static stability module

Python version: >=3.8

| Author: Leon Deligny
| Creation: 2025-01-27
"""

# =================================================================================================
#   IMPORTS
# =================================================================================================

from pathlib import Path

from ceasiompy.utils.ceasiomlogger import get_logger
from ceasiompy.utils.ceasiompyutils import get_aeromap_list_from_xpath, get_results_directory
from ceasiompy.StaticStability.func.extract_stability_data import generate_stab_table
from cpacspy.cpacsfunctions import get_value_or_default
from ceasiompy.utils.moduleinterfaces import check_cpacs_input_requirements, get_toolinput_file_path, get_tooloutput_file_path

from cpacspy.cpacspy import CPACS
from markdownpy.markdownpy import MarkdownDoc, Table

from ceasiompy.utils.commonxpath import CHECK_STABILITY_XPATH, AVL_AEROMAP_UID_XPATH
from typing import List

# =================================================================================================
#   FUNCTIONS
# =================================================================================================

log = get_logger()

MODULE_DIR = Path(__file__).parent
MODULE_NAME = MODULE_DIR.name

def static_stability_analysis(cpacs_path: str, cpacs_out_path: str) -> None:
    """
    Analyses longitudinal, directional and lateral stability.

    Args:
        cpacs_path (str): Path to CPACS file.
        cpacs_out_path (str): Path to CPACS output file.
        
    """

    cpacs = CPACS(cpacs_path)

    results_dir = get_results_directory("StaticStability")
    md = MarkdownDoc(Path(results_dir, "Static_stability.md"))
    md.h2("Static stability")
    
    def markdownpy_to_markdown(table: List[List[str]]) -> None:
        """
        Writes a Markdownpy Table to a Markdown object.
    
        Args:
            table (Markdownpy Table): Table generated from 'generate_stab_table' function.
            
    
        """
        if len(table) > 1:
            md.p(Table(table).write())
            md.line()
      
    for aeromap_uid in get_aeromap_list_from_xpath(cpacs, AVL_AEROMAP_UID_XPATH):
        log.info(f"Static stability of '{aeromap_uid}' aeromap")
        md.h4(f"Static stability of '{aeromap_uid}' aeromap")
        
        aeromap = cpacs.get_aeromap_by_uid(aeromap_uid)

        if get_value_or_default(cpacs.tixi, CHECK_STABILITY_XPATH, True):
            table = generate_stab_table(aeromap, cpacs)
            markdownpy_to_markdown(table)
            
          
    md.save()
    cpacs.save_cpacs(cpacs_out_path, overwrite=True)


# =================================================================================================
#    MAIN
# =================================================================================================


def main(cpacs_path: str, cpacs_out_path: str) -> None:

    log.info("----- Start of " + MODULE_NAME + " -----")
    
    check_cpacs_input_requirements(cpacs_path)
    
    static_stability_analysis(cpacs_path, cpacs_out_path)
    
    log.info("----- End of " + MODULE_NAME + " -----")
    

if __name__ == "__main__":

    cpacs_path = get_toolinput_file_path(MODULE_NAME)
    cpacs_out_path = get_tooloutput_file_path(MODULE_NAME)

    main(cpacs_path, cpacs_out_path)