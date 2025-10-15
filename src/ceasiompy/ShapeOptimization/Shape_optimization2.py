
# ==============================================================================
#   IMPORTS
# ==============================================================================

import numpy as np
import pandas as pd
import csv
import streamlit as st
import shutil

from scipy.optimize import minimize, basinhopping
from pathlib import Path
from pandas import DataFrame
from cpacspy.cpacspy import CPACS
from ceasiompy import log
import sys
from unittest.mock import MagicMock
from ceasiompy.PyAVL.pyavl import main as run_avl
from ceasiompy.PyAVL.func.results import get_avl_aerocoefs
from tixi3.tixi3wrapper import Tixi3
from functools import partial


import joblib

from typing import (
    List,
    Dict,
    Tuple,
    Union,
)

from ceasiompy.SMTrain.func.trainsurrogate import (
    get_hyperparam_space,
    train_surrogate_model,
    save_model,
)

from ceasiompy.SMTrain.func.sampling import (
    lh_sampling,
    split_data,
)

from ceasiompy.PyAVL import (
    AVL_AEROMAP_UID_XPATH,
    MODULE_NAME as PYAVL_NAME,
)

from ceasiompy.utils.ceasiompyutils import (
    current_workflow_dir,
    update_cpacs_from_specs,
)



# =================================================================================================


BASE_CPACS  = Path("D150_simple.xml")
MODEL_UID = "wing"     # or "fuselage", "engine", ecc.
PART_UID = "Wing1"
SECTION_UIDS = [f"{PART_UID}_Sec{i}" for i in range(1, 5)]
POSITIONING_UIDS = [f"{PART_UID}_Sec{i}" for i in range(1, 5)]
AEROMAP_UID = 'aeromap_empty'
N_SAMPLES = 5

FIDELITY_LEVEL_list = ["LEVEL_ONE", "LEVEL_TWO", "LEVEL_THREE"]
OBJECTIVES_LIST = ["cl", "cd", "cs", "cmd", "cml", "cms"]

parameters = {
    "sweepAngle" : 10,
    "dihedralAngle" : 5,
}

xpath_base = f"/cpacs/vehicles/aircraft/model/{MODEL_UID}s/{MODEL_UID}[@uID='{PART_UID}']/sections"
aeroMap = f"/cpacs/vehicles/aircraft/model/analyses/aeroPerformance"
xpath_coeffs = f"/cpacs/vehicles/aircraft/model/{MODEL_UID}s/{MODEL_UID}[@uID='{PART_UID}']/positionings"


def update_cpacs(cpacs_path_in: Path, cpacs_path_out: Path, params: dict) -> None:

    tixi = Tixi3()
    tixi.open(str(cpacs_path_in), True)

    # function to create missing branches in the XML tree if needed
    def create_branch(tixi_handle, xpath: str):
        parts = xpath.strip('/').split('/')
        for i in range(1, len(parts) + 1):
            pth = '/' + '/'.join(parts[:i])
            if not tixi_handle.checkElement(pth):
                parent = '/' + '/'.join(parts[:i-1]) if i > 1 else '/'
                tixi_handle.createElement(parent, parts[i - 1])

    for param_name, param_info in params.items():
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
                    raise ValueError(f"The value of {param_name} at path {xp} contain more than one element, need a scalar value.")

            tixi.updateDoubleElement(xp, float(val), "%g")

    # Save and close the CPACS file modified
    tixi.save(str(cpacs_path_out))
    tixi.close()
    return cpacs_path_out

def define_ranges(cpacs: CPACS):
    """
    Define the ranges for all the parameters within the value imposed inside the dictionary
    'parameters'.
    e.g. read the value of 'sweepAngle1','sweepAngle2', 'dihedralAngle1', 'dihedralAngle2' and
    for each of these apply the tollerance.
    """
    ranges = {}
    tixi = cpacs.tixi
    count = tixi.getNamedChildrenCount(xpath_coeffs, "positioning")
    
    for params,toll in parameters.items():
        for i in range(1, count + 1):
            node_path = f"{xpath_coeffs}/positioning[{i}]/{params}"
            val = tixi.getDoubleElement(node_path)
            key_name = f"{params}_{i}"
            ranges[key_name] = (val - toll, val + toll)
            # print(f"Parameter: {key_name}, Range: {ranges[key_name]}")

    return ranges, list(ranges.keys())


def run_simulations(cpacs_template: Path, samples_df: pd.DataFrame, result_dir: Path, output_csv: Path):
    """
    Run iteratively the simulations,  

    """
    
    sim_dir = result_dir / "cpacs_updated"
    sim_dir.mkdir(exist_ok=True)

    PyAVL_dir = result_dir / f"Py_AVL_simulations"
    PyAVL_dir.mkdir(exist_ok=True)

    headers = list(samples_df.columns) + ["cd", "cs", "cl", "cmd", "cms", "cml", "cmd_b", "cms_a", "cml_b"]

    if not output_csv.exists():
        with open(output_csv, mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(headers)
    
    
    for idx, row in samples_df.iterrows():
        # print(f"Running simulation {idx + 1} with parameters: \n{row.to_dict()}")
        print(f"Running simulation {idx + 1}")

        cpacs_iter = sim_dir / f"cpacs_{idx+1}.xml"
        shutil.copy(cpacs_template, cpacs_iter) # Copy the template CPACS file for each iteration
        
        avl_dir = PyAVL_dir / f"avl_results_case_{idx+1}"
        avl_dir.mkdir(exist_ok=True)


        results_avl_file = avl_dir / "Case00_alt0.0_mach0.3_aoa0.0_aos0.0_q0.0_p0.0_r0.0" / "st.txt"

        # create the parameters dictionary to update CPACS
        params_to_update = {}
        for param in parameters.keys():
            param_values = [row[f"{param}_{i+1}"] for i in range(len(SECTION_UIDS))]
            param_xpaths = [f"{xpath_coeffs}/positioning[{i+1}]/{param}" for i in range(len(SECTION_UIDS))]
            params_to_update[param] = {
                "values": param_values,
                "xpath": param_xpaths
                }
    
        # update the CPACS file with the new parameters
        update_cpacs(cpacs_iter, cpacs_iter, params_to_update)

        cpacs_file = CPACS(cpacs_iter)
        tixi = cpacs_file.tixi

        # Run AVL analysis
        st.session_state = MagicMock()
        update_cpacs_from_specs(cpacs_file, PYAVL_NAME, test=True)

        # Update CPACS with the new aeromap
        tixi.updateTextElement(AVL_AEROMAP_UID_XPATH, AEROMAP_UID)

        run_avl(cpacs_file, avl_dir)
        
        # Retrieve aero coefs
        aeroCoeffs = get_avl_aerocoefs(results_avl_file)

        # Append the results to the CSV file
        with open(output_csv, mode="a", newline="") as f:
            writer = csv.writer(f)
            data_row = list(row.values) + list(aeroCoeffs)
            writer.writerow(data_row)

        
def train_sm(cpacs: CPACS, dataset_path: Path, result_dir: Path, objective: str):
    

    
    # convert to ndarray the csv file, in order to get the hyperparameter space
    df1 = pd.read_csv(dataset_path, usecols=list(range(8)) + [10]) # to include CL --> usecols=list(range(9)) + [11]
    ndarray1 = df1.to_numpy()
    # print(ndarray1)

    level1_set = {
        "x_train" : ndarray1
    }

    level2_set = None

    level3_set = None

    # get hyperparameter space
    hyperparams = get_hyperparam_space(
        level1_sets = level1_set, 
        level2_sets = level2_set, 
        level3_sets = level3_set,
    )

    # print(f"The hyperparameters are:")
    # for hp in hyperparams:
    #     print(hp)

    # split dataset
    split_ratio = 0.7
    # training datasets
    if df1 is not None:
        # print(f"Splitting the dataset 1")
        t1s = split_data(df1, objective, split_ratio)

    
    model, rmse = train_surrogate_model(t1s)
    save_model(cpacs, model, objective, result_dir)

    # print("The model generated is:")
    # print(model)

    return model


def cost_function(x, mdl, target_idx):
    
    x_t = np.array(x).reshape(1,-1)
    y_pred = mdl.predict_values(x_t)
    # print("Output shape:", y_pred.shape)
    # print("Value predict:")
    # print(y_pred) 

    return y_pred[0,target_idx]


def find_minima(model, x0, bounds, target_index, params_keys, csv_path_minima):
  
  
    def fun(x):
        return cost_function(x, model, target_index)
    
    minimizer_kwargs = {
    "method": "L-BFGS-B",
    "bounds": bounds
    }
    
    n_runs = 20
    minima = []

    for i in range(n_runs):
        result = basinhopping(
        fun, 
        x0, 
        niter=100, 
        minimizer_kwargs=minimizer_kwargs,
        )

        minima.append((result.fun, result.x))
    
    # minima_sorted = sorted(minima, key=lambda t: t[0])
    

    # def far_enough(new_x, existing_xs, tol=3):
    #     return all(np.linalg.norm(new_x - x) > tol for x in existing_xs)
    
    # filtered_minima = []
    # for val, x in minima_sorted:
    #     if far_enough(x, [fx for _, fx in filtered_minima]):
    #         filtered_minima.append((val, x))
    
    for i, (val, x) in enumerate(minima):
        print(f"Minimum #{i+1}: function value = {val:.6f}")
        for name, value in zip(params_keys, x):
            print(f" {name} = {value}")   
    
    # SAVE FILE IN CSV
    with open(csv_path_minima, mode='w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(list(params_keys) + ['function_value'])
        for val, x in minima:
            writer.writerow(list(x) + [val])





def main() -> None:
    
    cpacs_file = (Path(sys.argv[1]).resolve()
                  if len(sys.argv) > 1 else BASE_CPACS.resolve())
    print(f"Using CPACS file: {cpacs_file}")

    cpacs_obj = CPACS(cpacs_file)
    
    workflow_dir = current_workflow_dir()
    simulations_dir = workflow_dir / "simulations"
    simulations_dir.mkdir(exist_ok=True)
    surrogate_model_dir = workflow_dir / "SurrogateModel"
    surrogate_model_dir.mkdir(exist_ok=True)
    smt_dir = surrogate_model_dir / "Training"
    smt_dir.mkdir(exist_ok=True)

    csv_path_minima = simulations_dir / "minimum.csv"

    ranges, params_keys = define_ranges(cpacs_obj)

    
    # ---- LHS generation----
    lh_sampling_path = lh_sampling(N_SAMPLES, ranges, simulations_dir)
    samples_df = pd.read_csv(lh_sampling_path)
    # print(f"LHS samples:\n{samples_df}")

    dataSet_path = simulations_dir / "simulation_results.csv"
    
    objective = "cl"

    # print(f"Run simulation for each configuration")
    run_simulations(cpacs_file, samples_df, simulations_dir, dataSet_path)

    train_sm(cpacs_obj, dataSet_path, smt_dir, objective)

    model_path = smt_dir / "surrogateModel_{}.pkl".format(objective)
    # Load the model and its metadata
    if not model_path.exists():
        raise FileNotFoundError(f"Surrogate model file not found: {model_path}")

    with open(model_path, "rb") as file:
        model_metadata = joblib.load(file)



    print(type(model_metadata))
    print(model_metadata.keys())

    model = model_metadata["model"]
    coefficient = model_metadata["coefficient"]

    # print(model)
    # print(coefficient)

    bounds = list(ranges.values())

    # print("The bounds are:")
    # print(bounds)

    target_index = 0
    x0 = np.array([np.random.uniform(low, high) for (low, high) in bounds])

    find_minima(model,x0,bounds,target_index, params_keys, csv_path_minima)


if __name__ == "__main__":
    main()

