"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Script to train a Surrogate Model in CEASIOMPY.
Either (1) Kriging or (2-3) Multi-Fidelity Kriging model can be used,
depending on the level of fidelity chosen.

| Author: Giacomo Gronda
| Creation: 2025-03-20

TODO:
    * Adapt SaveAeroCoefficient for the adaptive sampling
    * More tests on adaptive sampling
    * Never tested with 3 levels of fidelity
"""

# ==============================================================================
#   IMPORTS
# ==============================================================================

from ceasiompy.utils.ceasiompyutils import call_main
from ceasiompy.SMTrain.func.plot import plot_validation
from ceasiompy.SMTrain.func.sampling import lh_sampling
from ceasiompy.SMTrain.func.config import (
    get_settings,
    design_of_experiment,
)
from ceasiompy.SMTrain.func.trainsurrogate import (
    save_model,
    run_first_level_training,
    run_adaptative_refinement,
)

from pathlib import Path
from cpacspy.cpacspy import CPACS

from ceasiompy import log
from ceasiompy.SMTrain import (
    LEVEL_TWO,
    MODULE_NAME,
)

# =================================================================================================
#    MAIN
# =================================================================================================


def main(cpacs: CPACS, results_dir: Path) -> None:
    """
    Train a surrogate model (single-level or multi-fidelity) using aerodynamic data.

    1. Retrieve settings from the CPACS file
    2. Train surrogate model
    3. Plot and save model
    """

    # 1. Retrieve settings from the CPACS file
    (
        fidelity_level,
        split_ratio,
        objective,
        show_plot,
        rmse_obj,
    ) = get_settings(cpacs)

    # 2. Train surrogate model
    # Get and Generate new samples if necessary
    n_samples, ranges = design_of_experiment(cpacs)
    lh_sampling_path = lh_sampling(n_samples, ranges, results_dir)

    # First level fidelity training
    model, sets = run_first_level_training(
        cpacs=cpacs,
        lh_sampling_path=lh_sampling_path,
        objective=objective,
        split_ratio=split_ratio,
    )

    # Second level fidelity training
    if fidelity_level == LEVEL_TWO:
        run_adaptative_refinement(
            cpacs=cpacs,
            results_dir=results_dir,
            model=model,
            level1_sets=sets,
            rmse_obj=rmse_obj,
            objective=objective,
        )

    # Second level fidelity training
    # TODO: if fidelity_level == LEVEL_THREE:

    # 3. Plot, save and get results
    if show_plot:
        log.info("Validation plots.")
        plot_validation(model, sets, objective, results_dir)

    save_model(cpacs, model, objective, results_dir)


if __name__ == "__main__":
    call_main(main, MODULE_NAME)
