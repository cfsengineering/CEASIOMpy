"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Get settings from GUI. Manage datasets and perform LHS when required.
"""

# Imports

import numpy as np
import pandas as pd

from shutil import copyfile
from cpacspy.cpacsfunctions import get_value
from ceasiompy.smtrain.func.utils import get_columns
from ceasiompy.utils.ceasiompyutils import aircraft_name
from ceasiompy.utils.geometryfunctions import get_xpath_for_param
from pathlib import Path
from ceasiompy.utils.commonpaths import get_wkdir
from scipy.optimize import (
    differential_evolution,
)
from pandas import DataFrame
from tixi3.tixi3wrapper import Tixi3
from ceasiompy.database.func.storing import CeasiompyDb
from cpacspy.cpacspy import (
    CPACS,
    AeroMap,
)
from ceasiompy import log
from ceasiompy.smtrain import (
    SMTRAIN_XPATH_PARAMS_AEROMAP,
    SMTRAIN_GEOM_WING_OPTIMISE,
    SMTRAIN_NSAMPLES_AEROMAP_XPATH,
    SMTRAIN_NSAMPLES_GEOMETRY_XPATH,
    SMTRAIN_OBJECTIVE_XPATH,
    SMTRAIN_SIMULATION_PURPOSE_XPATH,
    SMTRAIN_THRESHOLD_XPATH,
    SMTRAIN_TRAIN_PERC_XPATH,
    SMTRAIN_FIDELITY_LEVEL_XPATH,
    SMTRAIN_UPLOAD_AVL_DATABASE_XPATH,
)

from ceasiompy.utils.commonxpaths import (
    WINGS_XPATH,
    SELECTED_AEROMAP_XPATH,
)


# Functions

def get_settings(cpacs: CPACS):
    """
    Reads the global and new suggested dataset settings.
    """
    tixi = cpacs.tixi
    aeromap_selected = get_value(tixi, SELECTED_AEROMAP_XPATH)
    fidelity_level = get_value(tixi, SMTRAIN_FIDELITY_LEVEL_XPATH)
    data_repartition = get_value(tixi, SMTRAIN_TRAIN_PERC_XPATH)
    objective = get_value(tixi, SMTRAIN_OBJECTIVE_XPATH)
    rmse_obj = get_value(tixi, SMTRAIN_THRESHOLD_XPATH)
    simulation_purpose = get_value(tixi, SMTRAIN_SIMULATION_PURPOSE_XPATH)
    old_new_sim = get_value(tixi, SMTRAIN_UPLOAD_AVL_DATABASE_XPATH)
    # selected_krg_model = get_value(tixi, SMTRAIN_KRG_MODEL)
    # selected_rbf_model = get_value(tixi, SMTRAIN_RBF_MODEL)
    log.info(f"Surrogate's model {objective=} with {fidelity_level=}")

    return (
        aeromap_selected,
        fidelity_level,
        data_repartition,
        objective,
        rmse_obj,
        simulation_purpose,
        old_new_sim,
        # selected_krg_model,
        # selected_rbf_model,
    )


def retrieve_aeromap_data(
    cpacs: CPACS,
    aeromap_uid: str,
    objective: str,
) -> DataFrame:
    """
    Retrieves the aerodynamic data from a CPACS aeromap
    and prepares input-output data for training.
    """
    activate_aeromap: AeroMap = cpacs.get_aeromap_by_uid(aeromap_uid)
    log.info(f"Aeromap {aeromap_uid} retrieved successfully.")

    # Extract data as lists
    altitude = activate_aeromap.get("altitude").tolist()
    mach = activate_aeromap.get("machNumber").tolist()
    aoa = activate_aeromap.get("angleOfAttack").tolist()
    aos = activate_aeromap.get("angleOfSideslip").tolist()

    if objective == "cl_cd":
        cl = np.array(activate_aeromap.get("cl").tolist())
        cd = np.array(activate_aeromap.get("cd").tolist())
        obj = cl / cd
    else:
        obj = activate_aeromap.get(objective).tolist()

    # Only keep rows where objective is not nan
    filtered = [
        (alt, m, a, s, o)
        for alt, m, a, s, o in zip(altitude, mach, aoa, aos, obj)
        if not np.isnan(o)
    ]

    return DataFrame(
        filtered,
        columns=get_columns(objective),
    )


def retrieve_ceasiompy_db_data(
    tixi: Tixi3,
    objective: str,
) -> DataFrame:
    """
    Get data from ceasiompy.db used in previous AVL computations.
    """
    aircraft: str = aircraft_name(tixi)
    ceasiompy_db = CeasiompyDb()
    data = ceasiompy_db.get_data(
        table_name="avl_data",
        columns=["alt", "mach", "alpha", "beta", objective],
        db_close=True,
        filters=[
            # f"mach IN ({ranges['machNumber'][0]}, {ranges['machNumber'][1]})",
            f"aircraft = '{aircraft}'",
            # f"alt IN ({ranges['altitude'][0]}, {ranges['altitude'][1]})",
            # f"alpha IN ({ranges['angleOfAttack'][0]}, {ranges['angleOfAttack'][1]})",
            # f"beta IN ({ranges['angleOfSideslip'][0]}, {ranges['angleOfSideslip'][1]})",
            "pb_2V = 0.0",
            "qc_2V = 0.0",
            "rb_2V = 0.0",
        ],
    )
    log.info(f"Importing from ceasiompy.db {data=}")
    data_df = DataFrame(
        data,
        columns=get_columns(objective),
    ).drop_duplicates(ignore_index=True)

    return data_df


def design_of_experiment(cpacs: CPACS) -> tuple[int, dict[str, list[float]]]:
    """
    Retrieves the aeromap data,
    extracts the range for each input variable,
    and returns the number of samples and the defined ranges.
    """
    tixi = cpacs.tixi
    n_samples = int(get_value(tixi, SMTRAIN_NSAMPLES_AEROMAP_XPATH))
    if n_samples < 0:
        raise ValueError(
            "New samples can not be negative."
            "If you solely intend to use the data from ceasiompy.db, "
            "leave n_samples to 0."
            "Otherwise, try choose a high-enough n_samples >=7."
        )

    params_aeromap_xpath = SMTRAIN_XPATH_PARAMS_AEROMAP + "/parameter"
    n_param_aeromap = tixi.getNumberOfChilds(params_aeromap_xpath)

    range_params_aeromap = {}

    for i in range(1,n_param_aeromap + 1):
        name_param = tixi.getChildNodeName(params_aeromap_xpath, i)
        status_param = tixi.getTextElement(f"{params_aeromap_xpath}/{name_param}/status")

        if status_param.strip().lower() == "false":
            param_min_value = 0.0
            param_max_value = 0.0
            range_params_aeromap[name_param] = (param_min_value , param_max_value)
            continue

        if status_param.strip().lower() == "true":
            param_min_value = tixi.getDoubleElement(
                f"{params_aeromap_xpath}/{name_param}/min_value/value"
            )
            param_max_value = tixi.getDoubleElement(
                f"{params_aeromap_xpath}/{name_param}/max_value/value"
            )
            range_params_aeromap[name_param] = (param_min_value , param_max_value)

    log.info(f"Design of Experiment Settings for {n_samples=}.")
    for key, (min_value, max_value) in range_params_aeromap.items():
        log.info(f"{min_value} <= {key} <= {max_value}")

    return n_samples, range_params_aeromap


def get_elements_to_optimise(cpacs: CPACS):

    """
    Retrieves the geometric parameters selected bythe user for optimisation and the number
    of sample.
    """

    tixi = cpacs.tixi
    n_samples_geom = int(get_value(tixi, SMTRAIN_NSAMPLES_GEOMETRY_XPATH))
    if n_samples_geom < 0:
        raise ValueError(
            "New samples can not be negative."
            "If you solely intend to use the data from ceasiompy.db, "
            "leave n_samples to 0."
            "Otherwise, try choose a high-enough n_samples >=7."
        )

    tixi = cpacs.tixi
    wings_to_optimise = []
    sections_to_optimise = []
    parameters_to_optimise = []
    ranges_gui = {}

    n_wings_to_optimise = tixi.getNumberOfChilds(SMTRAIN_GEOM_WING_OPTIMISE)

    for i in range(1,n_wings_to_optimise + 1):
        wing_name = tixi.getChildNodeName(SMTRAIN_GEOM_WING_OPTIMISE, i)
        wing_selected_path = f"{SMTRAIN_GEOM_WING_OPTIMISE}/{wing_name}/selected"
        wing_status = tixi.getTextElement(wing_selected_path)
        if wing_status.strip().lower() == "true":
            wings_to_optimise.append(wing_name)
            section_path = f"{SMTRAIN_GEOM_WING_OPTIMISE}/{wing_name}/sections"
            n_section_to_optimise = tixi.getNumberOfChilds(section_path)
            for j in range(1, n_section_to_optimise + 1):
                section_name = tixi.getChildNodeName(section_path, j)
                section_selected_path = section_path + f"/{section_name}/selected"
                section_status = tixi.getTextElement(section_selected_path)
                if section_status.strip().lower() == "true":
                    sections_to_optimise.append(section_name)
                    parameters_path = section_path + f"/{section_name}/parameters"
                    n_parameters = tixi.getNumberOfChilds(parameters_path)
                    for k in range(1,n_parameters + 1):
                        parameter_name = tixi.getChildNodeName(parameters_path, k)
                        status_parameter_path = parameters_path + f"/{parameter_name}/status"
                        status_parameter = tixi.getTextElement(status_parameter_path)
                        if status_parameter.strip().lower() == "true":
                            parameters_to_optimise.append(
                                f"{wing_name}_{section_name}_{parameter_name}"
                            )
                            min_value_path = parameters_path + f"/{parameter_name}/min_value/value"
                            max_value_path = parameters_path + f"/{parameter_name}/max_value/value"
                            min_value = tixi.getDoubleElement(min_value_path)
                            max_value = tixi.getDoubleElement(max_value_path)
                            ranges_gui[
                                f"{parameter_name}_of_{section_name}_of_{wing_name}"
                            ] = [min_value,max_value]

    return wings_to_optimise,sections_to_optimise,parameters_to_optimise,ranges_gui, n_samples_geom


def update_geometry_cpacs(cpacs_path_in: Path, cpacs_path_out: Path, geom_params: dict) -> CPACS:

    tixi = Tixi3()
    tixi.open(str(cpacs_path_in), True)

    # function to create missing branches in the XML tree if needed
    def create_branch(tixi_handle, xpath: str):
        parts = xpath.strip('/').split('/')
        for i in range(1, len(parts) + 1):
            pth = '/' + '/'.join(parts[:i])
            if not tixi_handle.checkElement(pth):
                parent = '/' + '/'.join(parts[:i - 1]) if i > 1 else '/'
                tixi_handle.createElement(parent, parts[i - 1])

    for param_name, param_info in geom_params.items():
        values = param_info["values"]
        xpaths = param_info["xpath"]

        for val, xp in zip(values, xpaths):
            # create the branch if it does not exist
            create_branch(tixi, xp)

            # check that val is a single value
            if hasattr(val, "__len__") and not isinstance(val, (str, bytes)):
                if len(val) == 1:
                    val = val[0]
                else:
                    raise ValueError(
                        f"The value of {param_name} at path {xp} contain more"
                        "than one element, need a scalar value."
                    )

            tixi.updateDoubleElement(xp, float(val), "%g")

    # Save and close the CPACS file modified
    tixi.save(str(cpacs_path_out))
    tixi.close()

    cpacs_obj = CPACS(cpacs_path_out)

    return cpacs_obj


def relative_ranges(
    cpacs:CPACS,
    wings_to_optimise: list,
    sections_to_optimise: list,
    max_geom_ranges: dict
):

    tixi = cpacs.tixi

    ranges = {}

    for wing_selected in wings_to_optimise:
        wing_section_path = WINGS_XPATH + f"/wing[@uID='{wing_selected}']/sections"
        wing_positioning_path = WINGS_XPATH + f"/wing[@uID='{wing_selected}']/positionings"
        n_sections_wing = tixi.getNumberOfChilds(wing_section_path)
        for i in range(1,n_sections_wing + 1):
            section_path = wing_section_path + f"/section[{i}]"
            section_uid = tixi.getTextAttribute(section_path,"uID")
            if section_uid not in sections_to_optimise:
                continue
            for params,toll_percentage in max_geom_ranges.items():
                transf_path = f"{wing_section_path}/section[@uID='{section_uid}']/transformation"
                toll = toll_percentage / 100
                if params == "twist":
                    node_path = f"{transf_path}/rotation/y"
                    val = tixi.getDoubleElement(node_path)
                    key_name = f"{wing_selected}_{section_uid}_{params}"
                    ranges[key_name] = [val * (1 - toll), val * (1 + toll)]
                elif params == "chord":
                    node_path = f"{transf_path}/scaling/x"
                    val = tixi.getDoubleElement(node_path)
                    key_name = f"{wing_selected}_{section_uid}_{params}"
                    ranges[key_name] = [val * (1 - toll), val * (1 + toll)]
                elif params == "thickness":
                    node_path = f"{transf_path}/scaling/z"
                    val = tixi.getDoubleElement(node_path)
                    key_name = f"{wing_selected}_{section_uid}_{params}"
                    ranges[key_name] = [val * (1 - toll), val * (1 + toll)]

            positioning_path = wing_positioning_path + f"/positioning[{i}]"
            positioning_uid = tixi.getTextAttribute(positioning_path,"uID")
            for params,toll in max_geom_ranges.items():
                toll = toll_percentage / 100
                if any(positioning_uid.startswith(a) for a in sections_to_optimise):
                    x_ = f"{wing_positioning_path}/positioning[@uID='{positioning_uid}']"
                    if params == "length":
                        node_path = f"{x_}/{params}"
                        val = tixi.getDoubleElement(node_path)
                        key_name = f"{wing_selected}_{section_uid}_{params}"
                        ranges[key_name] = [val * (1 - toll), val * (1 + toll)]
                    if params == "sweepAngle":
                        node_path = f"{x_}/{params}"
                        val = tixi.getDoubleElement(node_path)
                        key_name = f"{wing_selected}_{section_uid}_{params}"
                        ranges[key_name] = [val * (1 - toll), val * (1 + toll)]
                    if params == "dihedralAngle":
                        node_path = f"{x_}/{params}"
                        val = tixi.getDoubleElement(node_path)
                        key_name = f"{wing_selected}_{section_uid}_{params}"
                        ranges[key_name] = [val * (1 - toll), val * (1 + toll)]
    return ranges


def create_list_cpacs_geometry(cpacs_file: Path, sampling_geom_csv: Path, NEWCPACS_path: Path):

    tixi = Tixi3()
    tixi.open(str(cpacs_file))

    list_cpacs = []

    df_geom = pd.read_csv(sampling_geom_csv)

    # Loop for each configuration
    for i, geom_row in df_geom.iterrows():
        cpacs_out = NEWCPACS_path / f"CPACS_geom_{i+1:03d}.xml"
        copyfile(cpacs_file, cpacs_out)

        params_to_update = {}
        for col in df_geom.columns:
            # SINTAX: {comp}_of_{section}_of_{param}
            col_parts = col.split('_of_')
            uID_wing = col_parts[2]
            uID_section = col_parts[1]
            name_parameter = col_parts[0]
            val = geom_row[col]

            xpath = get_xpath_for_param(tixi, name_parameter, uID_wing, uID_section)

            if name_parameter not in params_to_update:
                params_to_update[name_parameter] = {'values': [], 'xpath': []}

            params_to_update[name_parameter]['values'].append(val)
            params_to_update[name_parameter]['xpath'].append(xpath)

        # Update CPACS file
        cpacs_obj = update_geometry_cpacs(cpacs_file, cpacs_out, params_to_update)
        list_cpacs.append(cpacs_obj)

    return list_cpacs


def normalize_dataset(dataset_path: Path):
    dataset = pd.read_csv(dataset_path)
    param_cols = dataset.columns[:-1]

    df_norm = dataset.copy()
    normalization_params = {}

    for col in param_cols:
        col_mean = dataset[col].mean()
        col_std = dataset[col].std()
        if col_std == 0:
            df_norm[col] = 0.0
        else:
            df_norm[col] = (dataset[col] - col_mean) / col_std
        normalization_params[col] = {"mean": col_mean, "std": col_std}
    return normalization_params,df_norm


def normalize_input_from_gui(
    sliders_values: dict,
    param_order: list,
    normalization_params: dict,
) -> np.ndarray:
    x_phys = np.array(
        [sliders_values[p] for p in param_order],
        dtype=float
    )

    x_norm = np.zeros_like(x_phys)
    for i, p in enumerate(param_order):
        std = normalization_params[p]["std"]
        mean = normalization_params[p]["mean"]
        x_norm[i] = 0.0 if std == 0 else (x_phys[i] - mean) / std

    return x_norm


def phys_to_norm(x_phys, params, normalization_params):
    x_norm = np.zeros_like(x_phys)
    for i, p in enumerate(params):
        std = normalization_params[p]["std"]
        mean = normalization_params[p]["mean"]
        x_norm[i] = 0.0 if std == 0 else (x_phys[i] - mean) / std
    return x_norm


def norm_to_phys(x_norm, params, normalization_params):
    x_phys = np.zeros_like(x_norm)
    for i, p in enumerate(params):
        std = normalization_params[p]["std"]
        mean = normalization_params[p]["mean"]
        x_phys[i] = mean if std == 0 else x_norm[i] * std + mean
    return x_phys


def optimize_surrogate(
    surrogate_model,
    model_name: str,
    objective: str,
    param_order: list,
    normalization_params: dict,
    final_level1_df_c: pd.DataFrame,
):
    """
    Run global optimization on a surrogate model.
    Returns optimal normalized/physical parameters and metadata.
    """

    MAXIMIZE_OBJECTIVES = {"cl", "cl/cd"}
    maximize = objective.lower() in MAXIMIZE_OBJECTIVES

    def surrogate_objective(x_norm):
        x_norm = np.asarray(x_norm).reshape(1, -1)
        y_pred = float(surrogate_model.predict_values(x_norm)[0, 0])
        return -y_pred if maximize else y_pred

    # ---- bounds in normalized space ----
    bounds = []
    for p in param_order:
        std = normalization_params[p]["std"]
        mean = normalization_params[p]["mean"]

        if std == 0:
            bounds.append((0.0, 0.0))
        else:
            lo = (final_level1_df_c[p].min() - mean) / std
            hi = (final_level1_df_c[p].max() - mean) / std
            bounds.append((lo, hi))

    log.info(f"--- Starting global optimization on {model_name} surrogate ---")

    opt_result = differential_evolution(
        surrogate_objective,
        bounds=bounds,
        tol=1e-3,
        maxiter=1000,
        polish=True
    )

    x_opt_norm = opt_result.x

    # ---- denormalize ----
    x_opt_phys = {}
    for i, p in enumerate(param_order):
        std = normalization_params[p]["std"]
        mean = normalization_params[p]["mean"]
        x_opt_phys[p] = mean if std == 0 else x_opt_norm[i] * std + mean

    y_opt = float(
        surrogate_model.predict_values(
            np.array(x_opt_norm).reshape(1, -1)
        )[0, 0]
    )

    return {
        "model": model_name,
        "success": bool(opt_result.success),
        "message": opt_result.message,
        "objective": objective,
        "x_opt_norm": x_opt_norm.tolist(),
        "x_opt_phys": x_opt_phys,
        "y_opt_predicted": y_opt,
    }


def save_best_surrogate_geometry(
    surrogate_model,
    model_name: str,
    objective: str,
    param_order: list,
    normalization_params: dict,
    final_level1_df_c: pd.DataFrame,
    results_dir: Path,
):
    """
    Optimize surrogate and save best configuration (CSV with predicted y, CPACS).
    """

    # ---- optimization ----
    best_result = optimize_surrogate(
        surrogate_model=surrogate_model,
        model_name=model_name,
        objective=objective,
        param_order=param_order,
        normalization_params=normalization_params,
        final_level1_df_c=final_level1_df_c,
    )

    # ---- save CSV of best parameters + predicted y ----
    csv_path = results_dir / f"best_surrogate_parameters_{model_name}.csv"
    df_params = pd.DataFrame.from_dict(
        best_result["x_opt_phys"],
        orient="index",
        columns=["value"]
    )

    df_params.loc[objective] = best_result["y_opt_predicted"]
    df_params.to_csv(csv_path)

    log.info(f"Best surrogate parameters saved to CSV: {csv_path}")

    # ---- update CPACS geometry ----
    wkdir = get_wkdir()
    cpacs_template = wkdir / "00_ToolInput.xml"
    best_cpacs_path = results_dir / f"best_surrogate_geometry_{model_name}.xml"
    copyfile(cpacs_template, best_cpacs_path)

    best_cpacs = CPACS(best_cpacs_path)
    tixi = best_cpacs.tixi

    params_to_update = {}

    for full_name, val in best_result["x_opt_phys"].items():
        # SINTAX: {param}_of_{section}_of_{wing}
        parts = full_name.split("_of_")
        if len(parts) != 3:
            log.warning(f"Skipping malformed parameter name: {full_name}")
            continue

        name_parameter, uID_section, uID_wing = parts

        xpath = get_xpath_for_param(
            tixi=tixi,
            param=name_parameter,
            wing_uid=uID_wing,
            section_uid=uID_section
        )

        if name_parameter not in params_to_update:
            params_to_update[name_parameter] = {"values": [], "xpath": []}
        params_to_update[name_parameter]["values"].append(float(val))
        params_to_update[name_parameter]["xpath"].append(xpath)

    update_geometry_cpacs(
        best_cpacs_path,
        best_cpacs_path,
        params_to_update
    )

    best_cpacs.save_cpacs(best_cpacs_path, overwrite=True)

    log.info(f"Best surrogate geometry saved to: {best_cpacs_path}")

    return best_result
