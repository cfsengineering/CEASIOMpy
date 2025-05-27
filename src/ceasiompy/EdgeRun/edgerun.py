"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed for Airinnova AB, Stockholm, Sweden

Functions to manipulate Edge input file and results (TO-DO)
"""

# =================================================================================================
#   IMPORTS
# =================================================================================================

from ceasiompy.EdgeRun.func.config import edge_cfd
from ceasiompy.EdgeRun.func.extractforces import extract_edge_forces

from pathlib import Path
from cpacspy.cpacspy import CPACS

from ceasiompy import log


# =================================================================================================
#    MAIN
# =================================================================================================


def main(cpacs: CPACS, results_dir: Path) -> None:
    log.info("Create edge input file")
    edge_cfd(cpacs, results_dir)

    log.info("Starting edge postprocessing")
    extract_edge_forces(results_dir)
