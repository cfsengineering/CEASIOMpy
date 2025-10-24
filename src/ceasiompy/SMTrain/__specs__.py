"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Initialization for SMTrain module.

"""

# ==============================================================================
#   IMPORTS
# ==============================================================================

from ceasiompy.utils.moduleinterfaces import CPACSInOut

from ceasiompy.SU2Run import SU2_MAX_ITER_XPATH
from ceasiompy.utils.guixpaths import USED_SU2_MESH_XPATH
from ceasiompy.SMTrain import (
    INCLUDE_GUI,
    LEVEL_ONE,
    LEVEL_TWO,
    OBJECTIVES_LIST,
    SMTRAIN_MAX_ALT,
    SMTRAIN_MAX_MACH,
    SMTRAIN_MAX_AOA,
    SMTRAIN_MAX_AOS,
    SMTRAIN_THRESHOLD_XPATH,
    SMTRAIN_NSAMPLES_XPATH,
    SMTRAIN_PLOT_XPATH,
    SMTRAIN_OBJECTIVE_XPATH,
    SMTRAIN_TRAIN_PERC_XPATH,
    SMTRAIN_FIDELITY_LEVEL_XPATH,
    SMTRAIN_AVL_DATABASE_XPATH,
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
    default_value=[LEVEL_TWO, LEVEL_ONE],  # TODO: , "Three levels" not implemented yet
    unit=None,
    descr="""Select if you want to train a simple kriging (1 level of fidelity) or you want to
    train a Multi-Fidelity kriging (2 or 3 levels)""",
    xpath=SMTRAIN_FIDELITY_LEVEL_XPATH,
    gui=INCLUDE_GUI,
    gui_name="Choice of fidelity level",
    gui_group="Training Surrogate Settings",
    test_value=[LEVEL_ONE],
)

cpacs_inout.add_input(
    var_name="training_part",
    var_type=float,
    default_value=0.7,
    descr="Defining the percentage of the data to use to train the model in [0, 1]",
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
    var_name="avl_dataset_enriching",
    var_type=bool,
    default_value=True,
    unit=None,
    descr="Enrich your dataset from previously computed AVL values stored in ceasiompy.db",
    xpath=SMTRAIN_AVL_DATABASE_XPATH,
    gui=INCLUDE_GUI,
    gui_name="Data from ceasiompy.db",
    gui_group="Data Enriching Settings",
    test_value=False,
    expanded=True,
)

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
    test_value=7,
)

cpacs_inout.add_input(
    var_name="mesh_choice",
    var_type="DynamicChoice",
    default_value=["CPACS2GMSH mesh", "Path", "db"],
    unit=None,
    descr="Choose from where to upload the mesh",
    xpath=USED_SU2_MESH_XPATH,
    gui=INCLUDE_GUI,
    gui_name="Choose mesh",
    gui_group="Second Level of Fidelity Parameters",
    test_value=["CPACS2GMSH mesh"],
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
    gui_group="Second Level of Fidelity Parameters",
)

cpacs_inout.add_input(
    var_name="max_iter",
    var_type=int,
    default_value=1000,
    unit=None,
    descr="Maximum number of iterations performed by SU2",
    xpath=SU2_MAX_ITER_XPATH,
    gui=INCLUDE_GUI,
    gui_name="Maximum iterations",
    gui_group="Second Level of Fidelity Parameters",
    test_value=1,
)
