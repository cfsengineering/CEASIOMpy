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
)
from ceasiompy.SMTrain import (
    INCLUDE_GUI,
    LEVEL_ONE,
    LEVEL_TWO,
    SMTRAIN_XPATH_AEROMAP_UID,
    SMTRAIN_PLOT_XPATH,
    SMTRAIN_TRAIN_PERC_XPATH,
    SMTRAIN_FIDELITY_LEVEL_XPATH,
    SMTRAIN_KRG_MODEL,
    SMTRAIN_RBF_MODEL,
    SMTRAIN_AVL_DATABASE_XPATH,
    SMTRAIN_UPLOAD_AVL_DATABASE_XPATH,
)


# ==============================================================================
#   VARIABLE
# ==============================================================================

cpacs_inout = CPACSInOut()

# ==============================================================================
#   GUI INPUTS
# ==============================================================================

cpacs_inout.add_input(
    var_name="aeromap_uid",
    var_type=list,
    default_value=st.session_state.cpacs.get_aeromap_uid_list(),
    unit=None,
    descr="Name of the aero map to calculate",
    xpath=SMTRAIN_XPATH_AEROMAP_UID,
    gui=INCLUDE_GUI,
    gui_name="__AEROMAP_SELECTION",
    gui_group="Aeromap settings",
)

cpacs_inout.add_input(
    var_name="choose_db",
    var_type=list,
    default_value=["Run New Simulations", "Load Geometry Exploration Simulations"],
    unit=None,
    descr="Load pre-computed results from files or Generate new simulations.",
    xpath=SMTRAIN_UPLOAD_AVL_DATABASE_XPATH,
    gui=INCLUDE_GUI,
    gui_name="Load Existing or Run New Simulations",
    gui_group="Simulation Settings",
)

cpacs_inout.add_input(
    var_name="krg_model",
    var_type=bool,
    default_value=False,
    unit=None,
    descr="Select this model for the simulation (choose more than one for comparison).",
    xpath=SMTRAIN_KRG_MODEL,
    gui=INCLUDE_GUI,
    gui_name="KRG",
    gui_group="Training Surrogate Settings",
)

cpacs_inout.add_input(
    var_name="rbf_model",
    var_type=bool,
    default_value=False,
    unit=None,
    descr="Select this model for the simulation (choose more than one for comparison). "
    "This model will be trained only with AVL simulations.",
    xpath=SMTRAIN_RBF_MODEL,
    gui=INCLUDE_GUI,
    gui_name="RBF",
    gui_group="Training Surrogate Settings",
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

# cpacs_inout.add_input(
#     var_name="mesh_choice",
#     var_type="DynamicChoice",
#     default_value=["CPACS2GMSH mesh", "Path", "db"],
#     unit=None,
#     descr="Choose from where to upload the mesh",
#     xpath=USED_SU2_MESH_XPATH,
#     gui=False,
#     gui_name="Choose mesh",
#     gui_group="Training Surrogate Settings",
#     test_value=["CPACS2GMSH mesh"],
# )


# cpacs_inout.add_input(
# var_name="rmse_objective",
# var_type=float,
# default_value=0.05,
# unit=None,
# descr="Selects the model's RMSE threshold value for Bayesian optimisation",
# xpath=SMTRAIN_THRESHOLD_XPATH,
# gui=INCLUDE_GUI,
# gui_name="RMSE Threshold",
# gui_group="Training Surrogate Settings",
# )

# cpacs_inout.add_input(
# var_name="max_iter",
# var_type=int,
# default_value=1000,
# unit=None,
# descr="Maximum number of iterations performed by SU2",
# xpath=SU2_MAX_ITER_XPATH,
# gui=INCLUDE_GUI,
# gui_name="Maximum iterations",
# gui_group="Training Surrogate Settings",
# test_value=1,
# )

# cpacs_inout.add_input(
#     var_name="type_mesh",
#     var_type=list,
#     default_value=["Euler", "RANS"],
#     unit=None,
#     descr="Choose between Euler and RANS mesh",
#     xpath=GMSH_MESH_TYPE_XPATH,
#     gui=INCLUDE_GUI,
#     gui_name="Choose the mesh type",
#     gui_group="Mesh type",
# )


# cpacs_inout.add_input(
#     var_name="farfield_mesh_size_factor",
#     var_type=float,
#     default_value=10,
#     unit=None,
#     descr="""Factor proportional to the biggest cell on the plane
#             to obtain cell size on the farfield(just for Euler)""",
#     xpath=GMSH_MESH_SIZE_FARFIELD_XPATH,
#     gui=INCLUDE_GUI,
#     gui_name="Farfield mesh size factor",
#     gui_group="Mesh options",
# )

# cpacs_inout.add_input(
#     var_name="fuselage_mesh_size_factor",
#     var_type=float,
#     default_value=1.0,
#     unit=None,
#     descr="Factor proportional to fuselage radius of curvature to obtain cell size on it",
#     xpath=GMSH_MESH_SIZE_FACTOR_FUSELAGE_XPATH,
#     gui=INCLUDE_GUI,
#     gui_name="Fuselage mesh size factor",
#     gui_group="Mesh options",
# )

# cpacs_inout.add_input(
#     var_name="wing_mesh_size_factor",
#     var_type=float,
#     default_value=1.0,
#     unit=None,
#     descr="Factor proportional to wing radius of curvature to obtain cell size on it",
#     xpath=GMSH_MESH_SIZE_FACTOR_WINGS_XPATH,
#     gui=INCLUDE_GUI,
#     gui_name="Wings mesh size factor",
#     gui_group="Mesh options",
# )

# cpacs_inout.add_input(
#     var_name="engine_mesh_size",
#     var_type=float,
#     default_value=0.23,
#     unit="[m]",
#     descr="Value assigned for the engine surfaces mesh size",
#     xpath=GMSH_MESH_SIZE_ENGINES_XPATH,
#     gui=INCLUDE_GUI,
#     gui_name="Engines",
#     gui_group="Mesh options",
# )

# cpacs_inout.add_input(
#     var_name="propeller_mesh_size",
#     var_type=float,
#     default_value=0.23,
#     unit="[m]",
#     descr="Value assigned for the propeller surfaces mesh size",
#     xpath=GMSH_MESH_SIZE_PROPELLERS_XPATH,
#     gui=INCLUDE_GUI,
#     gui_name="Propellers",
#     gui_group="Mesh options",
# )


# cpacs_inout.add_input(
#     var_name="n_power_factor",
#     var_type=float,
#     default_value=2,
#     unit=None,
#     descr="Power of the power law of the refinement on LE and TE. ",
#     xpath=GMSH_N_POWER_FACTOR_XPATH,
#     gui=INCLUDE_GUI,
#     gui_name="n power factor",
#     gui_group="Advanced mesh parameters",
# )

# cpacs_inout.add_input(
#     var_name="n_power_field",
#     var_type=float,
#     default_value=0.9,
#     unit=None,
#     descr="Value that changes the measure of fist cells near aircraft parts",
#     xpath=GMSH_N_POWER_FIELD_XPATH,
#     gui=INCLUDE_GUI,
#     gui_name="n power field",
#     gui_group="Advanced mesh parameters",
# )

# cpacs_inout.add_input(
#     var_name="refine_factor",
#     var_type=float,
#     default_value=2.0,
#     unit=None,
#     descr="Refinement factor of wing leading/trailing edge mesh",
#     xpath=GMSH_REFINE_FACTOR_XPATH,
#     gui=INCLUDE_GUI,
#     gui_name="LE/TE refinement factor",
#     gui_group="Advanced mesh parameters",
# )

# cpacs_inout.add_input(
#     var_name="refine_truncated",
#     var_type=bool,
#     default_value=False,
#     unit=None,
#     descr="Enable the refinement of truncated trailing edge",
#     xpath=GMSH_REFINE_TRUNCATED_XPATH,
#     gui=INCLUDE_GUI,
#     gui_name="Refine truncated TE",
#     gui_group="Advanced mesh parameters",
# )

# cpacs_inout.add_input(
#     var_name="auto_refine",
#     var_type=bool,
#     default_value=False,
#     unit=None,
#     descr="Automatically refine the mesh on surfaces that are small compare to the chosen mesh"
#     "size, this option increase the mesh generation time",
#     xpath=GMSH_AUTO_REFINE_XPATH,
#     gui=INCLUDE_GUI,
#     gui_name="Auto refine",
#     gui_group="Advanced mesh parameters",
# )

# cpacs_inout.add_input(
#     var_name="refine_factor_angled_lines",
#     var_type=float,
#     default_value=1.5,
#     unit="1",
#     descr="Refinement factor of edges at intersections that are not flat enough",
#     xpath=GMSH_REFINE_FACTOR_ANGLED_LINES_XPATH,
#     gui=True,
#     gui_name="Refinement factor of lines in between angled surfaces (only in RANS)",
#     gui_group="Advanced mesh parameters",
# )


# cpacs_inout.add_input(
#     var_name="n_layer",
#     var_type=int,
#     default_value=20,
#     unit=None,
#     descr="Number of prismatic element layers.",
#     xpath=GMSH_NUMBER_LAYER_XPATH,
#     gui=INCLUDE_GUI,
#     gui_name="Number of layer",
#     gui_group="RANS options",
# )

# cpacs_inout.add_input(
#     var_name="h_first_layer",
#     var_type=float,
#     default_value=3,
#     unit="[\u03bcm]",
#     descr="is the height of the first prismatic cell, touching the wall, in mesh length units.",
#     xpath=GMSH_H_FIRST_LAYER_XPATH,
#     gui=INCLUDE_GUI,
#     gui_name="Height of first layer",
#     gui_group="RANS options",
# )

# cpacs_inout.add_input(
#     var_name="max_layer_thickness",
#     var_type=float,
#     default_value=100,
#     unit="[mm]",
#     descr="The maximum allowed absolute thickness of the prismatic layer.",
#     xpath=GMSH_MAX_THICKNESS_LAYER_XPATH,
#     gui=INCLUDE_GUI,
#     gui_name="Max layer thickness",
#     gui_group="RANS options",
# )

# cpacs_inout.add_input(
#     var_name="growth_ratio",
#     var_type=float,
#     default_value=1.2,
#     unit=None,
#     descr="the largest allowed ratio between the wall-normal edge lengths of consecutive cells",
#     xpath=GMSH_GROWTH_RATIO_XPATH,
#     gui=INCLUDE_GUI,
#     gui_name="Growth ratio",
#     gui_group="RANS options",
# )

# cpacs_inout.add_input(
#     var_name="growth_factor",
#     var_type=float,
#     default_value=1.4,
#     unit=None,
#     descr="Desired growth factor between edge lengths of coincident tetrahedra",
#     xpath=GMSH_GROWTH_FACTOR_XPATH,
#     gui=INCLUDE_GUI,
#     gui_name="Growth factor",
#     gui_group="RANS options",
# )

# cpacs_inout.add_input(
#     var_name="feature_angle",
#     var_type=float,
#     default_value=40,
#     unit="[grad]",
#     descr="Larger angles are treated as resulting from approximation of curved surfaces",
#     xpath=GMSH_FEATURE_ANGLE_XPATH,
#     gui=INCLUDE_GUI,
#     gui_name="Feature Angle",
#     gui_group="RANS options",
# )

# cpacs_inout.add_input(
#     var_name="intake_percent",
#     var_type=float,
#     default_value=20,
#     unit="[%]",
#     descr="Position of the intake surface boundary condition in percentage of"
#     " the engine length from the beginning of the engine",
#     xpath=GMSH_INTAKE_PERCENT_XPATH,
#     gui=INCLUDE_GUI,
#     gui_name="Engine intake position",
#     gui_group="Engines",
# )
# cpacs_inout.add_input(
#     var_name="exhaust_percent",
#     var_type=float,
#     default_value=20,
#     unit="[%]",
#     descr="Position of the exhaust surface boundary condition in percentage of"
#     " the engine length from the end of the engine",
#     xpath=GMSH_EXHAUST_PERCENT_XPATH,
#     gui=INCLUDE_GUI,
#     gui_name="Engine exhaust position",
#     gui_group="Engines",
# )

cpacs_inout.add_output(
    var_name="su2_mesh_path",
    var_type="pathtype",
    default_value=None,
    unit=None,
    descr="Absolute path of the SU2 mesh",
    xpath=SU2MESH_XPATH,
)
