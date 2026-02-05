"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Script to train a Surrogate Model in CEASIOMPY.
Either (1) Kriging or (2-3) Multi-Fidelity Kriging model can be used,
depending on the level of fidelity chosen.

TODO:
    * Adapt SaveAeroCoefficient for the adaptive sampling
    * More tests on adaptive sampling
    * Never tested with 3 levels of fidelity
"""

# Imports
import sys
import time
import shutil
import pandas as pd

from ceasiompy.utils.ceasiompyutils import call_main, get_results_directory
from ceasiompy.smtrain.func.plot import plot_validation
from ceasiompy.smtrain.func.sampling import (
    lh_sampling,
    lh_sampling_geom
)
from ceasiompy.smtrain.func.config import (
    get_settings,
    create_list_cpacs_geometry,
    get_elements_to_optimise,
    design_of_experiment,
)

from ceasiompy.smtrain.func.trainsurrogatemodel import (
    save_model,
    run_first_level_training,
    run_first_level_training_geometry,
    run_adaptative_refinement,
    run_adaptative_refinement_geom,
    run_adaptative_refinement_geom_RBF,
    training_existing_db,
    run_adaptative_refinement_geom_existing_db,
)


from pathlib import Path
from cpacspy.cpacspy import CPACS

from tixi3.tixi3wrapper import Tixi3

from ceasiompy import log
from ceasiompy.smtrain import (
    LEVEL_TWO,
    MODULE_NAME,
)


# Main

def main(cpacs: CPACS, results_dir: Path) -> None:
    """
    Train a surrogate model (single-level or multi-fidelity) using aerodynamic data.

    1. Retrieve settings from the CPACS file
    2. Train surrogate model
    3. Plot and save model
    """
    start = time.perf_counter()
    # 1. Retrieve settings from the CPACS file
    (
        aeromap_selected,
        fidelity_level,
        split_ratio,
        objective,
        rmse_obj,
        simulation_purpose,
        old_new_sim,
        selected_krg_model,
        selected_rbf_model,
    ) = get_settings(cpacs)

    if old_new_sim == "Run New Simulations":
        if simulation_purpose == "Flight Condition Exploration":
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

        if simulation_purpose == "Geometry Exploration":

            results_dir = get_results_directory(
                module_name='SMTrain',
            )

            low_fidelity_dir = results_dir / "Low_Fidelity"
            low_fidelity_dir.mkdir(exist_ok=True)

            computations_dir = Path(low_fidelity_dir, "AVL")
            computations_dir.mkdir(exist_ok=True)

            NEWCPACS_path = low_fidelity_dir / "New_CPACS"
            NEWCPACS_path.mkdir(exist_ok=True)

            cpacs_file = cpacs.cpacs_file

            tixi = Tixi3()
            tixi.open(str(cpacs_file))

            print(f"The aeromap selected by the user is: {aeromap_selected}")

            (
                wings_to_optimise,
                sections_to_optimise,
                parameters_to_optimise,
                ranges_gui,
                n_samples_geometry
            ) = get_elements_to_optimise(cpacs)

            df_ranges_gui = pd.DataFrame([
                {"Parameter": k, "Min": v[0], "Max": v[1]}
                for k, v in ranges_gui.items()
            ])

            if not wings_to_optimise:
                log.error("SELECT AT LEAST ONE WING!")
                sys.exit(1)
            if not sections_to_optimise:
                log.error("SELECT AT LEAST ONE SECTION!")
                sys.exit(1)
            if not parameters_to_optimise:
                log.error("SELECT AT LEAST ONE WING!")
                sys.exit(1)
            if not selected_krg_model and not selected_rbf_model:
                log.error("SELECT AT LEAST ONE MODEL!")
                sys.exit(1)

            lh_sampling_geom_path = lh_sampling_geom(n_samples_geometry, ranges_gui, results_dir)

            # Create the list of CPACS files (in function of geometry values of lh_smapling)
            list_cpacs = create_list_cpacs_geometry(
                cpacs_file,
                lh_sampling_geom_path,
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
                aeromap_uid=aeromap_selected,
                lh_sampling_geom_path=lh_sampling_geom_path,
                objective=objective,
                split_ratio=split_ratio,
                pyavl_dir=computations_dir,
                results_dir=low_fidelity_dir,
                KRG_model_bool=selected_krg_model,
                RBF_model_bool=selected_rbf_model,
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
                        aeromap_uid=aeromap_selected,
                        ranges_gui=df_ranges_gui,
                    )

            if selected_rbf_model:
                # Second level fidelity training
                if fidelity_level == LEVEL_TWO:
                    run_adaptative_refinement_geom_RBF(
                        cpacs=cpacs,
                        results_dir=results_dir,
                        model=rbf_model,
                        level1_sets=sets,
                        rmse_obj=rmse_obj,
                        objective=objective,
                        aeromap_uid=aeromap_selected,
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

    if old_new_sim == "Load Geometry Exploration Simulations":

        (_, _, _, ranges_gui, _) = get_elements_to_optimise(cpacs)

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

    end = time.perf_counter()
    print(f"ESECUTION TIME: {end - start} seconds")


if __name__ == "__main__":
    call_main(main, MODULE_NAME)
