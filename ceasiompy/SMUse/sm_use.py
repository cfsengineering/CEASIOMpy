"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

"""

# =================================================================================================
#   IMPORTS
# =================================================================================================

from pathlib import Path
from cpacspy.cpacspy import CPACS

from ceasiompy.utils.ceasiompyutils import call_main
from ceasiompy.SMUse.func.config import load_surrogate
from ceasiompy.SMUse.func.predictions import make_predictions

from ceasiompy.SMUse.func.results import (
    get_smu_results,
    save_new_dataset,
)

from ceasiompy import log
from ceasiompy.SMUse import MODULE_DIR

# =================================================================================================
#    MAIN
# =================================================================================================


def main(cpacs: CPACS, results_dir: Path) -> None:
    """
    Run Surrogate model:
        1. Loads a pre-trained surrogate model.
        2. Makes aerodynamic predictions.
        3. Saves predictions in 'new' dataset.
        4. Udpates aeromap.
    """

    # 1.Loads a pre-trained surrogate model
    log.info("Loading pre-trained surrogate model")
    model, coefficient, datasets = load_surrogate(cpacs)

    # 2. Makes aerodynamic predictions
    log.info("Making predictions")
    predictions = make_predictions(datasets, model)

    # 3. Saves predictions in 'new' dataset
    log.info("Saving predictions")
    save_new_dataset(datasets, predictions, coefficient)

    # 4. Udpates aeromap accordingly
    log.info("Updates aeromap")
    get_smu_results(cpacs, results_dir)


if __name__ == "__main__":
    call_main(main, MODULE_DIR)
