"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Script to perform shape optimization using a surrogate model.

"""

# ==============================================================================
#   IMPORTS
# ==============================================================================

import numpy as np
import pandas as pd
from pathlib import Path
from cpacspy.cpacspy import CPACS
from ceasiompy import log
import sys
from skopt import gp_minimize

from ceasiompy.utils.ceasiompyutils import (
    get_aeromap_conditions,
    write_inouts,
)
from ceasiompy.SMTrain.func.trainsurrogate import (
    save_model,
    run_first_level_training,
    run_adaptative_refinement,
)
from ceasiompy.SMTrain.func.createdata import (
    launch_avl,
    launch_su2,
)

from ceasiompy.SMTrain.func.sampling import lh_sampling
from ceasiompy.SMTrain.func.config import design_of_experiment

from ceasiompy.utils.ceasiompyutils import call_main
from tixi3.tixi3wrapper import Tixi3


# =================================================================================================


BASE_CPACS  = Path("D150_simple.xml")
MODEL_UID = "wing"     # or "fuselage", "engine", ecc.
PART_UID = "Wing1"
SECTION_UIDS = [f"{PART_UID}_Sec{i}" for i in range(1, 5)]
AEROMAP_UID = ''

xpath_base = f"/cpacs/vehicles/aircraft/model/{MODEL_UID}s/{MODEL_UID}[@uID='{PART_UID}']/sections"
aeroMap = f"/cpacs/vehicles/aircraft/model/analyses/aeroPerformance"



def get_part_transformations(cpacs: Path, base_xpath: str, section_tag: str = "section") -> np.ndarray:
    
    """

    Extracts the transformation parameters (scaling, rotation, translation) for each section of a given part from a CPACS file.
    Requires the model's UID (e.g. wing, fuselage, engine, ecc.) and the part's UID (e.g. wing1, fuselage1, ecc.) and the base XPath to its sections.

    """
    
    tx = CPACS(cpacs).tixi
    # counter for the number of sections
    n_sections = tx.getNamedChildrenCount(base_xpath, section_tag)
    section_uids = [tx.getTextAttribute(f"{base_xpath}/{section_tag}[{i+1}]", "uID") for i in range(n_sections)]
    scal_x, scal_y, scal_z, rot_y = [], [], [], []
    trans_x, trans_y, trans_z = [], [], []

    for uid in section_uids:
        
        print(f"Extraction parameters for UID section: {uid}")
        
        px = f"{base_xpath}/{section_tag}[@uID='{uid}']/transformation"

        scal_x.append(tx.getDoubleElement(f"{px}/scaling/x"))
        scal_y.append(tx.getDoubleElement(f"{px}/scaling/y"))
        scal_z.append(tx.getDoubleElement(f"{px}/scaling/z"))
        rot_y.append(tx.getDoubleElement(f"{px}/rotation/y"))
        trans_x.append(tx.getDoubleElement(f"{px}/translation/x"))
        trans_y.append(tx.getDoubleElement(f"{px}/translation/y"))
        trans_z.append(tx.getDoubleElement(f"{px}/translation/z"))
    
    return {
    "scaling_x": np.array(scal_x),
    "scaling_y": np.array(scal_y),
    "scaling_z": np.array(scal_z),
    "rotation_y": np.array(rot_y),
    "translation_x": np.array(trans_x),
    "translation_y": np.array(trans_y),
    "translation_z": np.array(trans_z),
    }

def surrogate_objective(objective: np.ndarray, surrogate_model) -> float:
    """

    Objective function to be minimized by the optimizer.
    objective: vector of design variables (shape parameters)
    surrogate_model: trained surrogate model (e.g., Kringing, GP, ecc.)

    """
    prediction = surrogate_model.predict(objective.reshape(1, -1))
    return prediction[0]

def update_cpacs_parameters(cpacs_path_in: str, cpacs_path_out: str, params: dict) -> None:

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

def main() -> None:

    cpacs_file = (Path(sys.argv[1]).resolve()
                  if len(sys.argv) > 1 else BASE_CPACS.resolve())
    print(f"Using CPACS file: {cpacs_file}")

    result_dir = cpacs_file.parent / "results"
    result_dir.mkdir(exist_ok=True)

    cpacs = CPACS(cpacs_file)

    # ---- get aeromap condition ----
    flight_conditions = get_aeromap_conditions(cpacs, aeroMap)
    # print("Flight conditions:")
    alt_list, mach_list, aoa_list, aos_list = flight_conditions

    aoa = aoa_list[0]
    aos = aos_list[0]
    mach = mach_list[0]
    alt = alt_list[0]

    cpacs.create_aeromap_from_csv()
    
    # ---- range and parameters definition ----
    params_raw = get_part_transformations(cpacs_file, xpath_base, section_tag="section")
    print("Current twist rotation_y:", params_raw["rotation_y"])

    n_sections = len(params_raw["rotation_y"])
    ranges = {f"twist_{i}": (-5.0, 0.0) for i in range(n_sections)}
    n_samples = 20  

    # ---- LHS generation----
    lh_sampling_path = lh_sampling(n_samples, ranges, result_dir)
    samples_df = pd.read_csv(lh_sampling_path)
    print(f"LHS samples:\n{samples_df}")

    # ---- BATCH simulation (each point LHS) ----
    cpacs_batch_files = []
    for idx, sample in samples_df.iterrows():
        # Updated twist values:
        twist_vals = [sample[f"twist_{i}"] for i in range(n_sections)]
        params = {
            "twist": {
                "values": twist_vals,
                "xpath": [f"{xpath_base}/section[@uID='{uid}']/transformation/rotation/y" for uid in SECTION_UIDS],
            },
        }
        cpacs_out = result_dir / f"cpacs_sample_{idx}.xml"
        update_cpacs_parameters(cpacs_file, cpacs_out, params)
        cpacs_obj = CPACS(cpacs_out)

        print(f"Running AVL for sample {idx} with twist values: {twist_vals}")
        launch_avl(cpacs_obj, lh_sampling_path, "cd")
        # Also SU2 can be launched here if needed
        # launch_su2(cpacs_obj, None, "cd")
        cpacs_obj.tixi.save(str(cpacs_out))
        cpacs_batch_files.append(cpacs_out)
    print("AVL analysis completed and results retrieved.")


    objective = "cd"
    split_ratio = 0.7

    # ---- TRAINING 
    cpacs_train = CPACS(cpacs_batch_files[-1])
    model, sets = run_first_level_training(cpacs_train, lh_sampling_path, objective, split_ratio)
    print("Surrogate model trained with low-fidelity simulations data.")

    # ---- optimization ----
    bounds = [(-5.0, 0.0)] * n_sections
    def objective_wrapper(twist_list):
        return surrogate_objective(np.array(twist_list), model)
    result = gp_minimize(objective_wrapper, bounds, n_calls=50, random_state=42)
    print(f"Optimal twist found: {result.x}")
    print(f"Predicted objective at optimal twist: {result.fun}")

if __name__ == "__main__":
    main()




















# def main() -> None:

#     cpacs_file = (Path(sys.argv[1]).resolve()
#                   if len(sys.argv) > 1 else BASE_CPACS.resolve())
   
#     # cpacs_obj = CPACS(cpacs_file)
#     print(f"Using CPACS file: {cpacs_file}")

#     result_dir = cpacs_file.parent / "results"
#     result_dir.mkdir(exist_ok=True)


#     # get flight conditions
#     flight_conditions = get_aeromap_conditions(CPACS(cpacs_file), aeroMap)
#     # print("Flight conditions:")
#     alt_list, mach_list, aoa_list, aos_list = flight_conditions
#     # print(f"Altitudes: {alt_list}")
#     # print(f"Mach numbers: {mach_list}")
#     # print(f"Angles of attack: {aoa_list}")
#     # print(f"Angles of sideslip: {aos_list}")


#     # Read parameters
#     params_raw = get_part_transformations(BASE_CPACS, xpath_base, section_tag="section")
#     print("Current twist rotation_y:", params_raw["rotation_y"])
#     # print("Transformations for each section:")
#     # for key, value in params.items():
#     #     print(f"{key}: {value}")

#     # definition of ranges for each design variable
#     n_sections = len(params["twist"]["values"])
#     bounds = [(-5.0, 0.0)] * n_sections
#     n_samples = 20

#     lh_sampling_path = lh_sampling(n_samples, ranges, result_dir)
#     samples_df = pd.read_csv(lh_sampling_path)

#     params = {
#         "twist": {
#             "values": params_raw["rotation_y"],  
#             "xpath": [
#                 f"{xpath_base}/section[@uID='{uid}']/transformation/rotation/y" for uid in SECTION_UIDS            ],
#         },
#       ### Add more parameters as needed ###
#     }

#     updated_cpacs_file = update_cpacs_parameters(cpacs_file, "updated_cpacs.xml", params)

#     cpacs_obj = CPACS(updated_cpacs_file)
#     df_avl = launch_avl(cpacs_obj, lh_sampling_path, objective)
#     print("AVL analysis completed and results retrieved.")

#     # df_su2 = launch_su2(CPACS(updated_cpacs_file), lh_sampling_path=None, objective="cd")

#     cpacs_obj.tixi.save(str(df_avl))

#     n_samples, ranges = design_of_experiment(cpacs_obj)


#         # First level fidelity training
#     model, sets = run_first_level_training(
#         cpacs=cpacs_obj,
#         lh_sampling_path=lh_sampling_path,
#         objective=objective,
#         split_ratio=split_ratio,
#     )
#     print("Surrogate model trained with low-fidelity simulations data.")



#     def objective_wrapper(twist_list):
#         twist_array = np.array(twist_list)
#         return surrogate_objective(twist_array, model)
    
#     result = gp_minimize(objective_wrapper, bounds, n_calls=50, random_state=42)

#     print(f"Optimal twist found: {result.x}")
#     print(f"Predicted objective at optimal twist: {result.fun}")


# if __name__ == "__main__":
#     main()




