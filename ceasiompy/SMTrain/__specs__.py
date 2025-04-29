"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Initialization for SMTrain module.

"""

# ==============================================================================
#   IMPORTS
# ==============================================================================

import streamlit as st

from ceasiompy.utils.moduleinterfaces import CPACSInOut

from ceasiompy import log
from ceasiompy.SMTrain import include_gui
# from ceasiompy.utils.commonxpath import SMTRAIN_XPATH
from ceasiompy.utils.commonxpath import (
    SMTRAIN_DOE,
    SU2MESH_XPATH,
    SMTRAIN_XPATH,
    CEASIOMPY_XPATH,
)

# ==============================================================================
#   VARIABLE
# ==============================================================================

cpacs_inout = CPACSInOut()

# ==============================================================================
#   GUI INPUTS
# ==============================================================================

cpacs_inout.add_input(
    var_name="fidelity_level",
    var_type=list,
    default_value=["One level", "Two levels", "Three levels"],
    unit=None,
    descr="""Select if you want to train a simple kriging (1 level of fidelity) or you want to
    train a Multi-Fidelity kriging (2 or 3 levels)""",
    xpath=SMTRAIN_XPATH + "/fidelityLevel",
    gui=True,
    gui_name="Choice of fidelity level",
    gui_group="Global Settings",
)

cpacs_inout.add_input(
    var_name="trainig_part",
    var_type=float,
    default_value="0.7",
    descr="Defining the percentage of the data to use to train the model in [0;1]",
    xpath=SMTRAIN_XPATH + "/trainingPercentage",  # decidere anche divisione test e validation?
    gui=include_gui,
    gui_name="% of training data",
    gui_group="Global Settings",
)

cpacs_inout.add_input(
    var_name="objective",
    var_type=list,
    default_value=["cl", "cd", "cs", "cmd", "cml", "cms"],
    unit=None,
    descr="Objective function list for the surrogate model to predict",
    xpath=SMTRAIN_XPATH + "/objective",
    gui=include_gui,
    gui_name="Objective",
    gui_group="Global Settings",
)

cpacs_inout.add_input(
    var_name="show_validation_plot",
    var_type=bool,
    default_value=False,
    unit=None,
    descr="Choose if the validation plot must be shown or not",
    xpath=SMTRAIN_XPATH + "/ValidationPlot",
    gui=include_gui,
    gui_name="Validation plot",
    gui_group="Global Settings",
)

cpacs_inout.add_input(
    var_name="training_datasets",
    var_type=list,
    default_value=st.session_state.cpacs.get_aeromap_uid_list(),
    unit=None,
    descr="Select, in the RIGHT ORDER, training datasets from the aeromaps",
    xpath=SMTRAIN_XPATH + "/aeromapForTraining",
    gui=include_gui,
    gui_name="__AEROMAP_CHECKBOX",
    gui_group="Training Dataset",
)

cpacs_inout.add_input(
    var_name="new_dataset",
    var_type=bool,
    default_value=False,
    unit=None,
    descr="""Choose if you want a new suggested dataset to improve the multy-fidelity
    surrogate model""",
    xpath=SMTRAIN_XPATH + "/newDataset",
    gui=include_gui,
    gui_name="New Dataset",
    gui_group="New Suggested Dataset",
)

cpacs_inout.add_input(
    var_name="fraction_of_new_samples",
    var_type=int,
    default_value=2,
    unit=None,
    descr="Choose the fraction of new samples for the new dataset",
    xpath=SMTRAIN_XPATH + "/newDatasetFraction",
    gui=include_gui,
    gui_name="Fraction of new samples",
    gui_group="New Suggested Dataset",
)

cpacs_inout.add_input(
    var_name="designOfExperiments",
    var_type=bool,
    default_value=False,
    unit=None,
    descr="""Choose if you want to start a Design of Experiments with the Latin
    Hypercube Sampling""",
    xpath=SMTRAIN_DOE + "/newDoe",
    gui=include_gui,
    gui_name="Design of Experiments",
    gui_group="Design of Experiments",
)

cpacs_inout.add_input(
    var_name="dataset_for_doe",
    var_type=list,
    default_value=None,
    unit=None,
    descr="Select the aeromap with ranges for the Design of Experiments",
    xpath=SMTRAIN_XPATH + "/aeromapForDoe",
    gui=include_gui,
    gui_name="__AEROMAP_CHECKBOX",
    gui_group="Dataset with ranges",
)

cpacs_inout.add_input(
    var_name="number_of_samples",
    var_type=int,
    default_value=100,  # devono essere 2 o piu!!
    unit=None,
    descr="Choose the number of samples",
    xpath=SMTRAIN_DOE + "/nSamples",
    gui=include_gui,
    gui_name="Number of samples",
    gui_group="Design of Experiments",
)

cpacs_inout.add_input(
    var_name="use_AVL_or_SU2",
    var_type=list,
    default_value=["AVL", "SU2"],
    unit=None,
    descr="""Choose if you want to use AVL or SU2 for low fidelity simulation""",
    xpath=SMTRAIN_DOE + "useAVLorSU2",
    gui=True,
    gui_name="Use of AVL or SU2 for low fidelity simulations",
    gui_group="Design of Experiments",
)

cpacs_inout.add_input(
    var_name="su2_mesh_path",
    var_type="pathtype",
    default_value="-",
    unit="1",
    descr="Absolute path of the SU2 mesh",
    xpath=SU2MESH_XPATH,
    gui=True,
    gui_name="SU2 Mesh",
    gui_group="Design of Experiments",
)

cpacs_inout.add_input(
    var_name="rmse_objective",
    var_type=float,
    default_value=0.05,
    unit=None,
    descr="Selects the model's RMSE threshold value for Bayesian optimisation",
    xpath=SMTRAIN_DOE + "/rmseThreshold",
    gui=include_gui,
    gui_name="RMSE Threshold",
    gui_group="Design of Experiments",
)

# ==============================================================================
#   GUI OUTPUTS
# ==============================================================================

cpacs_inout.add_output(
    var_name="output",
    default_value=None,
    unit="1",
    descr="Description of the output",
    xpath=CEASIOMPY_XPATH + "/test/myOutput",
)

cpacs_inout.add_output(
    var_name="surrogateModel",
    default_value=None,
    unit="1",
    descr="path of the trained surrogate model",
    xpath=SMTRAIN_XPATH + "/surrogateModelPath",
)

# =================================================================================================
#    MAIN
# =================================================================================================

if __name__ == "__main__":
    log.info("Nothing to be executed.")
