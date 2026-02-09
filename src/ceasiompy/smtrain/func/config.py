"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Get settings from GUI. Manage data_frames and perform LHS when required.
"""

# Imports

import numpy as np

from shutil import copyfile
from cpacspy.cpacsfunctions import (
    get_value,
    create_branch,
    get_string_vector,
)
from scipy.optimize import differential_evolution
from ceasiompy.utils.geometryfunctions import get_xpath_for_param
from ceasiompy.smtrain.func.utils import (
    get_columns,
    domain_converter,
    get_model_typename,
)
from ceasiompy.utils.ceasiompyutils import (
    aircraft_name,
    get_sane_max_cpu,
    get_selected_aeromap,
    get_conditions_from_aeromap,
)

from pathlib import Path
from numpy import ndarray
from pandas import DataFrame
from smt.applications import MFK
from scipy.optimize import Bounds
from cpacspy.cpacspy import CPACS
from tixi3.tixi3wrapper import Tixi3
from scipy.optimize import OptimizeResult
from ceasiompy.database.func.storing import CeasiompyDb
from ceasiompy.smtrain.func.utils import (
    GeomBounds,
    TrainingSettings,
)
from smt.surrogate_models import (
    KRG,
    RBF,
)

from ceasiompy import log
from ceasiompy.utils.commonxpaths import WINGS_XPATH
from ceasiompy.smtrain import (
    NORMALIZED_DOMAIN,
    AEROMAP_FEATURES,
    SMTRAIN_MODELS_XPATH,
    SMTRAIN_XPATH_PARAMS_AEROMAP,
    SMTRAIN_GEOM_WING_OPTIMISE,
    SMTRAIN_NSAMPLES_AEROMAP_XPATH,
    SMTRAIN_NSAMPLES_GEOMETRY_XPATH,
    SMTRAIN_OBJECTIVE_XPATH,
    SMTRAIN_TRAIN_PERC_XPATH,
    SMTRAIN_FIDELITY_LEVEL_XPATH,
    SMTRAIN_OBJECTIVE_DIRECTION_XPATH,
)


# Functions

def get_settings(tixi: Tixi3) -> TrainingSettings:
    """
    Reads the global and new suggested data_frame settings.
    """

    # Extract values from CPACS
    sm_models = get_string_vector(tixi, SMTRAIN_MODELS_XPATH)
    objective = get_value(tixi, SMTRAIN_OBJECTIVE_XPATH)
    n_samples = int(get_value(tixi, SMTRAIN_NSAMPLES_GEOMETRY_XPATH))
    direction = get_value(tixi, xpath=SMTRAIN_OBJECTIVE_DIRECTION_XPATH)
    fidelity_level = get_value(tixi, SMTRAIN_FIDELITY_LEVEL_XPATH)
    data_repartition = get_value(tixi, SMTRAIN_TRAIN_PERC_XPATH)

    if not sm_models:
        raise ValueError("You need to choose a surrogate model type in the Settings Page.")

    return TrainingSettings(
        sm_models=sm_models,
        objective=objective,
        n_samples=n_samples,
        direction=direction,
        fidelity_level=fidelity_level,
        data_repartition=data_repartition,
    )


def retrieve_aeromap_data(
    cpacs: CPACS,
    objective: str,
    aeromap_uid: str | None = None,
) -> DataFrame:
    """
    Retrieves the aerodynamic data from a CPACS aeromap
    and prepares input-output data for training.
    """
    if aeromap_uid is None:
        activate_aeromap = get_selected_aeromap(cpacs)
    else:
        activate_aeromap = cpacs.get_aeromap_by_uid(aeromap_uid)

    altitude, mach, aoa, aos = get_conditions_from_aeromap(activate_aeromap)

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
        data=filtered,
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


def get_params_to_optimise(cpacs: CPACS) -> GeomBounds:

    """
    Retrieves the geometric parameters selected bythe user for optimisation and the number
    of sample.
    """
    log.info("Retrieving parameters to optimize.")

    tixi = cpacs.tixi

    param_names: list[str] = []
    min_values: list[float] = []
    max_values: list[float] = []

    wings_to_optimise = []
    params_to_optimise = []
    sections_to_optimise = []

    n_wings_to_optimise = tixi.getNumberOfChilds(SMTRAIN_GEOM_WING_OPTIMISE)

    # Wings
    for i in range(1, n_wings_to_optimise + 1):
        wing_name = tixi.getChildNodeName(SMTRAIN_GEOM_WING_OPTIMISE, i)
        wing_selected_path = f"{SMTRAIN_GEOM_WING_OPTIMISE}/{wing_name}/selected"
        wing_status = tixi.getTextElement(wing_selected_path)
        if wing_status.strip().lower() != "true":
            continue

        # Sections
        wings_to_optimise.append(wing_name)
        section_path = f"{SMTRAIN_GEOM_WING_OPTIMISE}/{wing_name}/sections"
        n_section_to_optimise = tixi.getNumberOfChilds(section_path)
        for j in range(1, n_section_to_optimise + 1):
            section_name = tixi.getChildNodeName(section_path, j)
            section_selected_path = section_path + f"/{section_name}/selected"
            section_status = tixi.getTextElement(section_selected_path)
            if section_status.strip().lower() != "true":
                continue
            sections_to_optimise.append(section_name)
            parameters_path = section_path + f"/{section_name}/parameters"
            n_parameters = tixi.getNumberOfChilds(parameters_path)

            # Parameters
            for k in range(1, n_parameters + 1):
                parameter_name = tixi.getChildNodeName(parameters_path, k)
                status_parameter_path = parameters_path + f"/{parameter_name}/status"
                status_parameter = tixi.getTextElement(status_parameter_path)
                if status_parameter.strip().lower() != "true":
                    continue
                params_to_optimise.append(
                    f"{wing_name}_{section_name}_{parameter_name}"
                )
                min_value_path = parameters_path + f"/{parameter_name}/min_value/value"
                max_value_path = parameters_path + f"/{parameter_name}/max_value/value"

                min_value = tixi.getDoubleElement(min_value_path)
                max_value = tixi.getDoubleElement(max_value_path)

                if min_value >= max_value:
                    log.info(f"""{parameter_name=} has constant range
                        (i.e. not a variable). Skipping...
                    """)
                    continue

                param_names.append(f"{parameter_name}_of_{section_name}_of_{wing_name}")
                min_values.append(min_value)
                max_values.append(max_value)

    if not wings_to_optimise:
        raise ValueError("You need to select a wing to perform geometry optimization.")
    if not sections_to_optimise:
        raise ValueError("You need to select a section to perform geometry optimization.")
    if not params_to_optimise:
        raise ValueError("You need to select a parameter to perform geometry optimization.")

    bounds = Bounds(
        lb=np.array(min_values, dtype=float),
        ub=np.array(max_values, dtype=float),
    )
    log.info(f'{len(min_values)} Parameters with {bounds=}')

    return GeomBounds(
        bounds=bounds,
        param_names=param_names,
    )


def update_geometry_cpacs(cpacs_path_in: Path, cpacs_path_out: Path, geom_params: dict) -> CPACS:
    tixi = Tixi3()
    tixi.open(str(cpacs_path_in), True)

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
    return CPACS(cpacs_path_out)


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


def create_list_cpacs_geometry(
    cpacs: CPACS,
    lh_sampling: DataFrame,
    results_dir: Path,
) -> list[CPACS]:
    log.info("Creating CPACS file from LHS samples.")

    # Constants
    tixi = cpacs.tixi
    cpacs_name = cpacs.ac_name
    cpacs_path_in = cpacs.cpacs_file

    generated_cpacs_dir = results_dir / "generated_cpacs"
    generated_cpacs_dir.mkdir(exist_ok=True)

    # Variables
    cpacs_list = []

    # Loop for each configuration
    for i, geom_row in lh_sampling.iterrows():
        cpacs_out = generated_cpacs_dir / f"{cpacs_name}_{i+1:03d}.xml"
        copyfile(cpacs.cpacs_file, cpacs_out)

        params_to_update = {}
        for col in lh_sampling.columns:
            if "_of_" not in col:
                raise ValueError(f"Syntax: _of_ i.e. {col=} is not a valid parameter.")

            # SYNTAX: {comp}_of_{section}_of_{param}
            col_parts = col.split('_of_')
            param = col_parts[0]
            wing_uid = col_parts[2]
            section_uid = col_parts[1]
            val = geom_row[col]

            xpath = get_xpath_for_param(
                tixi=tixi,
                param=param,
                wing_uid=wing_uid,
                section_uid=section_uid,
            )

            if param not in params_to_update:
                params_to_update[param] = {'values': [], 'xpath': []}

            params_to_update[param]['values'].append(val)
            params_to_update[param]['xpath'].append(xpath)

        # Update CPACS file
        cpacs_obj = update_geometry_cpacs(
            cpacs_path_in=cpacs_path_in,
            cpacs_path_out=cpacs_out,
            geom_params=params_to_update,
        )
        cpacs_list.append(cpacs_obj)

    return cpacs_list


def normalize_data(
    cpacs: CPACS,
    data_frame: DataFrame,
    geom_bounds: GeomBounds,
) -> tuple[GeomBounds, DataFrame, DataFrame]:
    """
    Normalizes columns of data_frame
    contained in geom_bounds.param_names with geom_bouds.bounds values.
    For the Aeromap values it uses the CPACS aeromap min/max (i.e. the selected aeromap).
    """
    lb = np.asarray(geom_bounds.bounds.lb, dtype=float)
    ub = np.asarray(geom_bounds.bounds.ub, dtype=float)
    norm_lb = np.empty_like(lb, dtype=float)
    norm_ub = np.empty_like(ub, dtype=float)

    for i in range(len(geom_bounds.param_names)):
        from_domain = (lb[i], ub[i])
        norm_lb[i] = domain_converter(lb[i], from_domain, NORMALIZED_DOMAIN)
        norm_ub[i] = domain_converter(ub[i], from_domain, NORMALIZED_DOMAIN)

    norm_bounds = Bounds(
        lb=norm_lb,
        ub=norm_ub,
    )

    geom_bounds_norm = GeomBounds(
        bounds=norm_bounds,
        param_names=geom_bounds.param_names,
    )

    df_norm = data_frame.copy()
    for i, param in enumerate(geom_bounds.param_names):
        df_norm[param] = domain_converter(
            df_norm[param].to_numpy(dtype=float, copy=False),
            (lb[i], ub[i]),
            NORMALIZED_DOMAIN,
        )

    aeromap_min_max = {}
    try:
        selected_aeromap = get_selected_aeromap(cpacs)
        altitude, mach, aoa, aos = get_conditions_from_aeromap(selected_aeromap)
        aeromap_min_max = {
            "altitude": (float(np.min(altitude)), float(np.max(altitude))),
            "machNumber": (float(np.min(mach)), float(np.max(mach))),
            "angleOfAttack": (float(np.min(aoa)), float(np.max(aoa))),
            "angleOfSideslip": (float(np.min(aos)), float(np.max(aos))),
        }
    except Exception as exc:
        log.warning(
            "Could not retrieve aeromap min/max from CPACS; "
            f"aeromap normalization will be skipped. {exc!r}"
        )

    aeromap_not_normalized = []
    for feature in AEROMAP_FEATURES:
        if feature not in df_norm.columns:
            aeromap_not_normalized.append(feature)
            continue
        bounds = aeromap_min_max.get(feature)
        if bounds is None:
            aeromap_not_normalized.append(feature)
            continue
        df_norm[feature] = domain_converter(
            df_norm[feature].to_numpy(dtype=float, copy=False),
            bounds,
            NORMALIZED_DOMAIN,
        )

    if aeromap_not_normalized:
        log.warning(
            "Aeromap columns not normalized: "
            + ", ".join(aeromap_not_normalized)
        )

    aeromap_features_present = [
        feature
        for feature in AEROMAP_FEATURES
        if feature in df_norm.columns
    ]
    if not aeromap_features_present:
        raise ValueError("Could not normalize Aeromap values.")

    aeromap_minimal = df_norm[aeromap_features_present].drop_duplicates(
        ignore_index=True
    )

    return geom_bounds_norm, df_norm, aeromap_minimal


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
    model: KRG | MFK | RBF,
    geom_bounds: GeomBounds,
    aeromap_norm_df: DataFrame,
    training_settings: TrainingSettings,
) -> tuple[OptimizeResult, float]:
    """
    Run global optimization on a surrogate model.
    Returns optimal normalized/physical parameters.
    """

    model_name = get_model_typename(model)
    direction = 1 if training_settings.direction == "Maximize" else -1
    aeromap_values = None
    if not aeromap_norm_df.empty:
        aeromap_features_present = [
            feature for feature in AEROMAP_FEATURES if feature in aeromap_norm_df.columns
        ]
        if aeromap_features_present:
            aeromap_values = aeromap_norm_df[aeromap_features_present].to_numpy(
                dtype=float, copy=False
            )

    def build_x_full(x_norm_row: ndarray) -> ndarray:
        if aeromap_values is None or aeromap_values.size == 0:
            return x_norm_row
        n = aeromap_values.shape[0]
        geom_block = np.repeat(x_norm_row, repeats=n, axis=0)
        return np.concatenate([geom_block, aeromap_values], axis=1)

    def surrogate_objective(x_norm: ndarray) -> float:
        try:
            x_norm = np.asarray(x_norm).reshape(1, -1)
            x_full = build_x_full(x_norm)
            y_pred_vec = model.predict_values(x_full).ravel()
            y_pred = float(np.mean(y_pred_vec))

            # TODO: use a loss function
            return direction * y_pred
        except Exception as exc:
            raise RuntimeError(
                f"surrogate_objective failed during differential_evolution evaluation: {exc!r}"
            ) from exc

    log.info(f"Starting best geometry search on {model_name} surrogate ---")

    opt_result = differential_evolution(
        func=surrogate_objective,
        bounds=geom_bounds.bounds,
        tol=1e-3,
        maxiter=1000,
        polish=True,
    )

    log.info("Finished finding best geometry from surrogate model functional space.")

    # Compute f(x_opt) = y_opt
    x_opt = np.array(opt_result.x).reshape(1, -1)
    x_full = build_x_full(x_opt)
    y_opt = float(np.mean(model.predict_values(x_full).ravel()))

    return opt_result, y_opt


def save_best_surrogate_geometry(
    cpacs: CPACS,
    best_model: KRG | MFK | RBF,
    geom_bounds: GeomBounds,
    results_dir: Path,
    aeromap_norm_df: DataFrame,
    training_settings: TrainingSettings,
) -> None:
    """
    Optimize Geometry on surrogate's function.
    """
    best_model_name = get_model_typename(best_model)

    best_result, _ = optimize_surrogate(
        model=best_model,
        geom_bounds=geom_bounds,
        aeromap_norm_df=aeromap_norm_df,
        training_settings=training_settings,
    )

    sm_results_dir = results_dir / f"{best_model_name}_results"
    sm_results_dir.mkdir(parents=True, exist_ok=True)

    csv_path = sm_results_dir / f"best_{best_model_name}_params.csv"

    log.info(f"Best surrogate parameters saved to CSV: {csv_path}")

    best_cpacs_path = sm_results_dir / f"best_{best_model_name}_geometry.xml"
    copyfile(cpacs.cpacs_file, best_cpacs_path)

    best_cpacs = CPACS(best_cpacs_path)
    tixi = best_cpacs.tixi

    params_to_update = {}
    for full_name, val in zip(geom_bounds.param_names, best_result.x):
        # SYNTAX: {param}_of_{section}_of_{wing}
        parts = full_name.split("_of_")
        if len(parts) != 3:
            log.warning(f"Skipping malformed parameter name: {full_name}")
            continue

        name_parameter, section_uid, wing_uid = parts

        xpath = get_xpath_for_param(
            tixi=tixi,
            param=name_parameter,
            wing_uid=wing_uid,
            section_uid=section_uid
        )
        if name_parameter not in params_to_update:
            params_to_update[name_parameter] = {"values": [], "xpath": []}

        params_to_update[name_parameter]["values"].append(float(val))
        params_to_update[name_parameter]["xpath"].append(xpath)

    update_geometry_cpacs(
        best_cpacs_path,
        best_cpacs_path,
        params_to_update,
    )
    best_cpacs.save_cpacs(best_cpacs_path, overwrite=True)

    log.info(f"Best surrogate geometry saved to: {best_cpacs_path}")
