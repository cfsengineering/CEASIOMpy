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

from ceasiompy.utils.commonxpaths import (
    SU2MESH_XPATH,
    CEASIOMPY_XPATH,
)
from ceasiompy.SMTrain import (
    INCLUDE_GUI,
    LEVEL_ONE,
    LEVEL_TWO,
    OBJECTIVES_LIST,
    SMTRAIN_XPATH,
    # SMTRAIN_NEWDOE,
    SMTRAIN_MAX_ALT,
    SMTRAIN_MAX_MACH,
    SMTRAIN_MAX_AOA,
    SMTRAIN_MAX_AOS,
    SMTRAIN_THRESHOLD_XPATH,
    SMTRAIN_NSAMPLES_XPATH,
    # SMTRAIN_NEW_DATASET,
    SMTRAIN_PLOT_XPATH,
    SMTRAIN_OBJECTIVE_XPATH,
    SMTRAIN_TRAIN_PERC_XPATH,
    SMTRAIN_FIDELITY_LEVEL_XPATH,
    # SMTRAIN_NEWDATASET_FRAC_XPATH,
    SMTRAIN_TRAINING_AEROMAP_XPATH,
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
    default_value=[LEVEL_ONE, LEVEL_TWO],  # TODO: , "Three levels" not implemented yet
    unit=None,
    descr="""Select if you want to train a simple kriging (1 level of fidelity) or you want to
    train a Multi-Fidelity kriging (2 or 3 levels)""",
    xpath=SMTRAIN_FIDELITY_LEVEL_XPATH,
    gui=INCLUDE_GUI,
    gui_name="Choice of fidelity level",
    gui_group="Training Surrogate Settings",
)

cpacs_inout.add_input(
    var_name="trainig_part",
    var_type=float,
    default_value=0.7,
    descr="Defining the percentage of the data to use to train the model in [0;1]",
    xpath=SMTRAIN_TRAIN_PERC_XPATH,
    gui=INCLUDE_GUI,
    gui_name=r"% of training data",
    gui_group="Training Surrogate Settings",
)

cpacs_inout.add_input(
    var_name="objective",
    var_type=list,
    default_value=OBJECTIVES_LIST,
    unit=None,
    descr="Objective function list for the surrogate model to predict",
    xpath=SMTRAIN_OBJECTIVE_XPATH,
    gui=INCLUDE_GUI,
    gui_name="Objective",
    gui_group="Training Surrogate Settings",
)

cpacs_inout.add_input(
    var_name="show_validation_plot",
    var_type=bool,
    default_value=True,
    unit=None,
    descr="Choose if the validation plot must be shown or not",
    xpath=SMTRAIN_PLOT_XPATH,
    gui=INCLUDE_GUI,
    gui_name="Validation plot",
    gui_group="Plot Settings",
    test_value=False,
    expanded=False,
)

cpacs_inout.add_input(
    var_name="training_datasets",
    var_type=list,
    default_value=st.session_state.cpacs.get_aeromap_uid_list().reverse(),
    unit=None,
    descr="Select, in the RIGHT ORDER, training datasets from the aeromaps",
    xpath=SMTRAIN_TRAINING_AEROMAP_XPATH,
    gui=INCLUDE_GUI,
    gui_name="__AEROMAP_SELECTION",
    gui_group="Training Dataset",
)

# cpacs_inout.add_input(
#     var_name="new_dataset",
#     var_type=bool,
#     default_value=False,
#     unit=None,
#     descr="""Choose if you want a new suggested dataset to improve the multy-fidelity
#     surrogate model""",
#     xpath=SMTRAIN_NEW_DATASET,
#     gui=INCLUDE_GUI,
#     gui_name="New Dataset",
#     gui_group="New Suggested Dataset",
# )

# cpacs_inout.add_input(
#     var_name="fraction_of_new_samples",
#     var_type=int,
#     default_value=2,
#     unit=None,
#     descr="Choose the fraction of new samples for the new dataset",
#     xpath=SMTRAIN_NEWDATASET_FRAC_XPATH,
#     gui=INCLUDE_GUI,
#     gui_name="Fraction of new samples",
#     gui_group="New Suggested Dataset",
# )

# cpacs_inout.add_input(
#     var_name="design_of_experiment_bool",
#     var_type=bool,
#     default_value=False,
#     unit=None,
#     descr="""Choose if you want to start a Design of Experiments with the Latin
#     Hypercube Sampling""",
#     xpath=SMTRAIN_NEWDOE,
#     gui=INCLUDE_GUI,
#     gui_name="Design of Experiments",
#     gui_group="Design of Experiments",
#     test_value=True,
# )

cpacs_inout.add_input(
    var_name="max_altitute",
    var_type=int,
    default_value=1000,
    unit="m",
    descr="Choose the maximum altitude (>=0)",
    xpath=SMTRAIN_MAX_ALT,
    gui=INCLUDE_GUI,
    gui_name="Maximum altitude Range",
    gui_group="Design of Experiments",
)

cpacs_inout.add_input(
    var_name="max_mach",
    var_type=float,
    default_value=0.4,
    unit=None,
    descr="Choose the maximum mach number (>=0.1)",
    xpath=SMTRAIN_MAX_MACH,
    gui=INCLUDE_GUI,
    gui_name="Maximum mach Number Range",
    gui_group="Design of Experiments",
)

cpacs_inout.add_input(
    var_name="max_aoa",
    var_type=int,
    default_value=15,
    unit="deg",
    descr="Choose the maximum angle of attack (>=0)",
    xpath=SMTRAIN_MAX_AOA,
    gui=INCLUDE_GUI,
    gui_name="Maximum angle of attack Range",
    gui_group="Design of Experiments",
)

cpacs_inout.add_input(
    var_name="max_aos",
    var_type=int,
    default_value=15,
    unit="deg",
    descr="Choose the maximum angle of sideslip (>=0)",
    xpath=SMTRAIN_MAX_AOS,
    gui=INCLUDE_GUI,
    gui_name="Maximum angle of sideslip Range",
    gui_group="Design of Experiments",
)

cpacs_inout.add_input(
    var_name="number_of_samples",
    var_type=int,
    default_value=10,
    unit=None,
    descr="Choose the number of samples",
    xpath=SMTRAIN_NSAMPLES_XPATH,
    gui=INCLUDE_GUI,
    gui_name="Number of samples",
    gui_group="Design of Experiments",
    test_value=1,
)

cpacs_inout.add_input(
    var_name="su2_mesh_path",
    var_type="pathtype",
    default_value="-",
    unit=None,
    descr="Absolute path of the SU2 mesh",
    xpath=SU2MESH_XPATH,
    gui=INCLUDE_GUI,
    gui_name="SU2 Mesh",
    gui_group="SU2 Parameters",
)

cpacs_inout.add_input(
    var_name="rmse_objective",
    var_type=float,
    default_value=0.05,
    unit=None,
    descr="Selects the model's RMSE threshold value for Bayesian optimisation",
    xpath=SMTRAIN_THRESHOLD_XPATH,
    gui=INCLUDE_GUI,
    gui_name="RMSE Threshold",
    gui_group="SU2 Parameters",
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
