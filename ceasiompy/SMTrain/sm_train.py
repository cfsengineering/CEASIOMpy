"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Script to train a Surrogate Model in CEASIOMPY.
The surrogate model can be trained either through a csv file containing the inputs and outputs,
or by carrying out a Design of Experiments after providing the domain extremes.
Either kriging or Multi-Fidelity kriging algorithm can be used,
depending on the level of fidelity chosen.

| Author: Giacomo Gronda
| Creation: 2025-03-20

TODO:
    * Create test functions
    * Adapt SaveAeroCoefficient for the adaptive sampling
    * More test on adaptive sampling
    * Never tested with 3 levels of fidelity
    * Define how to change AVL and SU2 settings

"""

# ==============================================================================
#   IMPORTS
# ==============================================================================

from ceasiompy.utils.ceasiompyutils import call_main
from ceasiompy.SMTrain.func.plot import plot_validation
from ceasiompy.SMTrain.func.results import get_smt_results
from ceasiompy.SMTrain.func.config import (
    get_settings,
    design_of_experiment,
    get_datasets_from_aeromaps,
)
from ceasiompy.SMTrain.func.sampling import (
    new_doe,
    split_data,
    lh_sampling,
)
from ceasiompy.SMTrain.func.trainsurrogate import (
    save_model,
    train_surrogate_model,
    run_first_level_training,
    run_adaptative_refinement,
)

from pathlib import Path
from cpacspy.cpacspy import CPACS

from ceasiompy import log
from ceasiompy.SMTrain import (
    LEVEL_ONE,
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
    3. Plot, save and get results
    """

    # 1. Retrieve settings from the CPACS file
    (
        fidelity_level,
        split_ratio,
        obj_coef,
        show_plot,
        new_dataset,
        fraction_of_new_samples,
        doe, avl, rmse_obj,
    ) = get_settings(cpacs)

    # 2. Train surrogate model
    if doe:
        # Generate new samples
        n_samples, ranges = design_of_experiment(cpacs)
        lh_sampling_path = lh_sampling(n_samples, ranges, results_dir)

        # One level fidelity model training
        if fidelity_level == LEVEL_ONE:
            model, sets, datasets = run_first_level_training(
                cpacs=cpacs,
                results_dir=results_dir,
                avl=avl,
                lh_sampling_path=lh_sampling_path,
                obj_coef=obj_coef,
                split_ratio=split_ratio,
            )

        elif fidelity_level == LEVEL_TWO:
            # Train the first-level (low-fidelity) model using AVL
            model, sets, datasets = run_first_level_training(
                cpacs=cpacs,
                results_dir=results_dir,
                avl=True,
                lh_sampling_path=lh_sampling_path,
                obj_coef=obj_coef,
                split_ratio=split_ratio,
            )

            run_adaptative_refinement(
                cpacs,
                results_dir,
                model,
                datasets,
                rmse_obj,
                obj_coef,
            )

    else:
        datasets = get_datasets_from_aeromaps(cpacs, obj_coef)
        sets = split_data(fidelity_level, datasets, split_ratio)
        model, _ = train_surrogate_model(fidelity_level, datasets, sets)
        if new_dataset:
            new_doe(datasets, model, fraction_of_new_samples, results_dir)

    # 3. Plot, save and get results
    if show_plot:
        log.info("Validation plots.")
        plot_validation(model, sets, obj_coef, results_dir)

    save_model(model, obj_coef, datasets, results_dir)
    get_smt_results(cpacs, results_dir)


if __name__ == "__main__":
    call_main(main, MODULE_NAME)
