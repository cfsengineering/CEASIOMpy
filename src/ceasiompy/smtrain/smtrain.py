"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Script to train a Surrogate Model in CEASIOMPY.
Either (1) Kriging or (2-3) Multi-Fidelity Kriging model can be used,
depending on the level of fidelity chosen.

TODO:
    * More tests on adaptive sampling
    * Never tested with 3 levels of fidelity
"""


# Imports
import sys
import shutil

from ceasiompy.utils.ceasiompyutils import call_main
from ceasiompy.smtrain.func.plot import plot_validation
from ceasiompy.smtrain.func.sampling import (
    lh_sampling,
    lh_sampling_geom,
)
from ceasiompy.smtrain.func.config import (
    get_settings,
    design_of_experiment,
    get_elements_to_optimise,
    create_list_cpacs_geometry,
)
from ceasiompy.smtrain.func.trainsurrogatemodel import (
    save_model,
    training_existing_db,
    run_first_level_training,
    run_adaptative_refinement,
    run_adapt_refinement_geom_rbf,
    run_adaptative_refinement_geom,
    run_first_level_training_geometry,
    run_adaptative_refinement_geom_existing_db,
)

from pathlib import Path
from pandas import DataFrame
from cpacspy.cpacspy import CPACS
from ceasiompy.smtrain.func.config import TrainingSettings

from ceasiompy import log
from ceasiompy.pyavl import MODULE_NAME as PYAVL
from ceasiompy.smtrain import (
    LEVEL_TWO,
    MODULE_NAME as SMTRAIN,
)


# Methods

def _load_smtrain_model(cpacs: CPACS) -> None:
    ranges_gui = get_elements_to_optimise(cpacs)

    krg_model, rbf_model, sets, param_order = training_existing_db(
        results_dir,
        split_ratio,
        selected_krg_model,
        selected_rbf_model
    )

    if fidelity_level == LEVEL_TWO:
        run_adaptative_refinement_geom_existing_db(
            cpacs=cpacs,
            results_dir=results_dir,
            model=krg_model,
            level1_sets=sets,
            rmse_obj=rmse_obj,
            objective=objective,
            aeromap_uid=aeromap_selected,
            ranges_gui=ranges_gui,
        )

    if selected_krg_model:
        log.info("Validation plots.")
        plot_dir = results_dir / "Validation_plot_KRG"
        plot_dir.mkdir(parents=True, exist_ok=True)
        plot_validation(krg_model, sets, objective, plot_dir)

        save_model(cpacs, krg_model, objective, results_dir, param_order)

    if selected_rbf_model:
        log.info("Validation plots.")
        plot_dir = results_dir / "Validation_plot_RBF"
        plot_dir.mkdir(parents=True, exist_ok=True)
        plot_validation(rbf_model, sets, objective, plot_dir)

        save_model(cpacs, rbf_model, objective, results_dir, param_order)


def _flight_condition_exploration(
    cpacs: CPACS,
    results_dir: Path,
    objective,
    split_ratio,
    fidelity_level,
    rmse_obj,
):
    n_samples, ranges = design_of_experiment(cpacs)
    lh_sampling_path = lh_sampling(n_samples, ranges, results_dir)

    # First level fidelity training
    model, sets, param_order = run_first_level_training(
        cpacs=cpacs,
        lh_sampling_path=lh_sampling_path,
        objective=objective,
        split_ratio=split_ratio,
        result_dir=results_dir,
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

    # 3. Plot, save and get results
    log.info("Validation plots.")
    plot_dir = results_dir / "Validation_plot"
    plot_dir.mkdir(parents=True, exist_ok=True)
    plot_validation(model, sets, objective, plot_dir)

    save_model(cpacs, model, objective, results_dir,param_order)


def _geometry_exploration(
    cpacs: CPACS,
    results_dir: Path,
    training_settings: TrainingSettings,
) -> None:
    tixi = cpacs.tixi

    # Low Fidelity First (+ Always available by default)
    low_fidelity_dir = results_dir / "low_fidelity"
    low_fidelity_dir.mkdir(exist_ok=True)

    avl_results_dir = Path(low_fidelity_dir, PYAVL)
    avl_results_dir.mkdir(exist_ok=True)

    generated_cpacs_dir = low_fidelity_dir / "generated_cpacs"
    generated_cpacs_dir.mkdir(exist_ok=True)

    ranges_gui = get_elements_to_optimise(cpacs)
    df_ranges_gui = DataFrame([
        {"Parameter": k, "Min": v[0], "Max": v[1]}
        for k, v in ranges_gui.items()
    ])

    lh_sampling = lh_sampling_geom(
        n_samples=training_settings.n_samples,
        ranges_gui=ranges_gui,
        results_dir=results_dir,
    )

    # Create the list of CPACS files (in function of geometry values of lh_smapling)
    list_cpacs = create_list_cpacs_geometry(
        tixi=tixi,
        lh_sampling=lh_sampling,
        NEWCPACS_path
    )

    # First level fidelity training
    (
        krg_model,
        rbf_model,
        sets,
        idx_best_geom_conf,
        param_order
    ) = run_first_level_training_geometry(
        cpacs_list=list_cpacs,
        lh_sampling_geom_path=lh_sampling_geom_path,
        objective=objective,
        split_ratio=split_ratio,
        pyavl_dir=computations_dir,
        results_dir=low_fidelity_dir,
        ranges_gui=ranges_gui,
    )

    files = sorted(list(NEWCPACS_path.glob("*.xml")))
    for i, best_cpacs_path in enumerate(files):
        if i == idx_best_geom_conf:
            print(f"{best_cpacs_path=}")
            dest_path = Path(results_dir) / "best_geometric_configuration_low_fidelity.xml"
            shutil.copy2(best_cpacs_path, dest_path)

    if selected_krg_model:
        # Second level fidelity training
        if fidelity_level == LEVEL_TWO:
            run_adaptative_refinement_geom(
                cpacs=cpacs,
                results_dir=results_dir,
                model=krg_model,
                level1_sets=sets,
                rmse_obj=rmse_obj,
                objective=objective,
                ranges_gui=df_ranges_gui,
            )

    if selected_rbf_model:
        # Second level fidelity training
        if fidelity_level == LEVEL_TWO:
            run_adapt_refinement_geom_rbf(
                cpacs=cpacs,
                results_dir=results_dir,
                model=rbf_model,
                level1_sets=sets,
                rmse_obj=rmse_obj,
                objective=objective,
                ranges_gui=df_ranges_gui,
            )

    # Second level fidelity training
    # TODO: if fidelity_level == LEVEL_THREE:

    # 3. Plot, save and get results
    if selected_krg_model:
        log.info("Validation plots.")
        plot_dir = results_dir / "Validation_plot_KRG"
        plot_dir.mkdir(parents=True, exist_ok=True)
        plot_validation(krg_model, sets, objective, plot_dir)

        save_model(cpacs, krg_model, objective, results_dir, param_order)

    if selected_rbf_model:
        plot_dir = results_dir / "Validation_plot_RBF"
        plot_dir.mkdir(parents=True, exist_ok=True)
        plot_validation(rbf_model, sets, objective, plot_dir)

        save_model(cpacs, rbf_model, objective, results_dir, param_order)


# Main

def main(cpacs: CPACS, results_dir: Path) -> None:
    """
    Train a surrogate model (single-level or multi-fidelity) using aerodynamic data.

    1. Retrieve settings from the CPACS file
    2. Train surrogate model
    3. Plot and save model
    """
    tixi = cpacs.tixi

    # 1. Retrieve settings from the CPACS file
    training_settings = get_settings(tixi)

    old_new_sim = "Run New Simulations"

    if old_new_sim == "Run New Simulations":
        simulation_purpose = "Geometry Exploration"
        if simulation_purpose == "Flight Condition Exploration":
            _flight_condition_exploration(
                cpacs=cpacs,
                results_dir=results_dir,
                training_settings=training_settings,
            )

        if simulation_purpose == "Geometry Exploration":
            _geometry_exploration(
                cpacs
            )

    if old_new_sim == "Load Geometry Exploration Simulations":
        _load_smtrain_model(
            cpacs=cpacs,
        )


if __name__ == "__main__":
    call_main(main, SMTRAIN)
