"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland.
"""

# Imports
from ceasiompy.su2run.su2run import main as run_su2
from ceasiompy.smtrain.func.config import retrieve_aeromap_data
from ceasiompy.cpacs2gmsh.cpacs2gmsh import main as run_cpacs2gmsh

from pathlib import Path
from pandas import DataFrame
from cpacspy.cpacspy import CPACS
from ceasiompy.smtrain.func.config import TrainingSettings


# Functions

def launch_gmsh_su2(
    cpacs: CPACS,
    results_dir: Path,
    training_settings: TrainingSettings,
) -> DataFrame:
    """
    Executes SU2 CFD analysis using an aeromap or high-variance points.
    """

    run_cpacs2gmsh(
        cpacs=cpacs,
        results_dir=results_dir,
    )
    run_su2(
        cpacs=cpacs,
        results_dir=results_dir,
    )

    return retrieve_aeromap_data(
        cpacs=cpacs,
        objective=training_settings.objective,
    )
