"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Initialization for SMTrain module.
"""

# Imports

import streamlit as st

from ceasiompy.utils.ceasiompyutils import safe_remove
from ceasiompy.utils.guiobjects import (
    int_vartype,
    list_vartype,
    bool_vartype,
    float_vartype,
    dataframe_vartype,
    multiselect_vartype,
)


from cpacspy.cpacspy import CPACS

from ceasiompy.utils.commonxpaths import SU2MESH_XPATH
from ceasiompy.SMTrain import (
    LEVEL_ONE,
    LEVEL_TWO,
    SMTRAIN_MODELS_XPATH,
    SMTRAIN_TRAIN_PERC_XPATH,
    SMTRAIN_FIDELITY_LEVEL_XPATH,
    SMTRAIN_AVL_DATABASE_XPATH,
    SMTRAIN_UPLOAD_AVL_DATABASE_XPATH,
)


# Variable

def gui_settings(cpacs: CPACS) -> None:
    tixi = cpacs.tixi

    list_vartype(
        tixi=tixi,
        default_value=["Run New Simulations", "Load Geometry Exploration Simulations"],
        key="smtrain_load_or_explore",
        name="Load Existing or Run New Simulations",
        description="Load pre-computed results from files or Generate new simulations.",
        xpath=SMTRAIN_UPLOAD_AVL_DATABASE_XPATH,
    )

    chosen_models = multiselect_vartype(
        tixi=tixi,
        xpath=SMTRAIN_MODELS_XPATH,
        default_value=["KRG, RBF"],
        name="Surrogate Model Type",
        description="Kriging (KRG) or/and Radial Basis Functions (RBF).",
        key="smtrain_chosen_model",
    )

    if "KRG" in chosen_models:
        list_vartype(
            tixi=tixi,
            xpath=SMTRAIN_FIDELITY_LEVEL_XPATH,
            default_value=[LEVEL_TWO, LEVEL_ONE],  # TODO: , "Three levels" not implemented yet
            name="Range of fidelity level(s).",
            description="""1st-level of fidelity (low fidelity),
                2nd level of fidelity (low + high fidelity) on high-variance points.
            """,
            key="smtrain_fidelity_level",
        )

    float_vartype(
        tixi=tixi,
        xpath=SMTRAIN_TRAIN_PERC_XPATH,
        default_value=0.7,
        name=r"% used of training data",
        description="Defining the percentage of the data to use to train the model.",
        key="smtrain_training_percentage",
        min_value=0.0,
        max_value=1.0,
    )

    # cpacs_inout.add_input(
    #     var_name="avl_dataset_enriching",
    #     var_type=bool,
    #     default_value=True,
    #     unit=None,
    #     descr="Enrich your dataset from previously computed AVL values stored in ceasiompy.db",
    #     xpath=SMTRAIN_AVL_DATABASE_XPATH,
    #     gui=True,
    #     gui_name="Data from ceasiompy.db",
    #     gui_group="Data Enriching Settings",
    #     test_value=False,
    #     expanded=True,
    # )

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
