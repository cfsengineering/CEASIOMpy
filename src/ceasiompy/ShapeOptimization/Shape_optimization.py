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
from pandas import DataFrame
from pathlib import Path
from cpacspy.cpacspy import CPACS
from ceasiompy import log
import sys, subprocess
import textwrap
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
# AEROMAP_UID = ''

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

### *** QUI BISOGNA PASSARE IL CPACS CHE FORNISCE IN USCITA IL MODULO AVL ***
def read_coeffs_from_cpacs(cpacs: CPACS, aeromap_uid: str) -> float: 
    """ read the aerodynamic coefficients from CPACS file after PyAVL or SU2 run """
    results = cpacs.tixi
    # 
    cl_xpath = f"/cpacs/toolspecific/CEASIOMpy/avl/table/cl"
    cd_xpath = f"/cpacs/toolspecific/CEASIOMpy/avl/table/cd"
    cl_value = results.getDoubleElement(cl_xpath)
    cd_value = results.getDoubleElement(cd_xpath)
    return cl_value, cd_value

### FORSE QUI BISOGNA COPIARE I VALORI NEL CPACS DI PARTENZA
### IN MODO DA LAVORARE POI SU QUELLO CON IL CICLO DI OTTIMIZZAZIONE

### OPPPURE TENEREE SEMPLICEMENTE IL CPACS DI PARTENZA E FARE IL GRADIENTE
### SU QUELLO, MENTRE I RISULTATI VENOGNO LETTI DAL CPACS DI OUTPUT DA AVL


def update_cpacs_with_shape():




def main() -> None:

    cpacs_file = (Path(sys.argv[1]).resolve()
                  if len(sys.argv) > 1 else BASE_CPACS.resolve())
    print(f"Using CPACS file: {cpacs_file}")

    result_dir = cpacs_file.parent / "results"
    result_dir.mkdir(exist_ok=True)

    cpacs = CPACS(cpacs_file)

    transformations = get_part_transformations(cpacs_file, xpath_base)
    n_sections = len(transformations["rotation_y"])

    # ---- get aeromap condition ----
    flight_conditions = get_aeromap_conditions(cpacs, aeroMap)
    # print("Flight conditions:")
    alt_list, mach_list, aoa_list, aos_list = flight_conditions

    # ---- run CEASIOMpy PyAVL module ----
    proc = subprocess.run(
        ["ceasiompy_run", "-m", str(cpacs_file), "PyAVL"],
        cwd=result_dir, capture_output=True, text=True
    )

    if proc.returncode:
        print("\nCEASIOMpy / PyAVL failed:\n",
              textwrap.indent(proc.stdout + proc.stderr, "│ "))
        raise RuntimeError("PyAVL exited with non-zero status")
    else:
        print("\nCEASIOMpy / PyAVL completed successfully:\n",
              textwrap.indent(proc.stdout, "│ "))
    


if __name__ == "__main__":
    main()

