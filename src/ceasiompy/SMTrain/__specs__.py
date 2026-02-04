"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Initialization for SMTrain module.
"""

# Imports

import streamlit as st

from ceasiompy.utils.ceasiompyutils import safe_remove
from cpacspy.cpacsfunctions import get_value_or_default
from ceasiompy.PyAVL.__specs__ import gui_settings as avl_settings
from ceasiompy.SU2Run.__specs__ import gui_settings as su2_settings
from ceasiompy.CPACS2GMSH.__specs__ import gui_settings as gmsh_settings

from ceasiompy.utils.geometryfunctions import (
    get_xpath_for_param,
    return_uid_wings_sections,
)
from ceasiompy.utils.guiobjects import (
    int_vartype,
    list_vartype,
    bool_vartype,
    float_vartype,
    multiselect_vartype,
)

from cpacspy.cpacspy import CPACS
from tixi3.tixi3wrapper import Tixi3

from ceasiompy.PyAVL import MODULE_NAME as PYAVL
from ceasiompy.SU2Run import MODULE_NAME as SU2RUN
from ceasiompy.CPACS2GMSH import MODULE_NAME as CPACS2GMSH
from ceasiompy.SMTrain import (
    LEVEL_ONE,
    LEVEL_TWO,
    OBJECTIVES_LIST,
    WING_PARAMETERS,
    AEROMAP_FEATURES,
    SMTRAIN_MODELS_XPATH,
    SMTRAIN_OBJECTIVE_XPATH,
    SMTRAIN_TRAIN_PERC_XPATH,
    SMTRAIN_GEOM_WING_OPTIMISE,
    SMTRAIN_FIDELITY_LEVEL_XPATH,
    SMTRAIN_NSAMPLES_AEROMAP_XPATH,
    SMTRAIN_NSAMPLES_GEOMETRY_XPATH,
    SMTRAIN_SIMULATION_PURPOSE_XPATH,
    SMTRAIN_UPLOAD_AVL_DATABASE_XPATH,
)


# Variable

def gui_settings(cpacs: CPACS) -> None:
    tixi = cpacs.tixi

    chosen_models = multiselect_vartype(
        tixi=tixi,
        xpath=SMTRAIN_MODELS_XPATH,
        default_value=["KRG, RBF"],
        name="Surrogate Model Type",
        description="Kriging (KRG) or/and Radial Basis Functions (RBF).",
        key="smtrain_chosen_model",
    )

    if "KRG" in chosen_models:
        fidelity_level = list_vartype(
            tixi=tixi,
            xpath=SMTRAIN_FIDELITY_LEVEL_XPATH,
            default_value=[LEVEL_ONE, LEVEL_TWO],  # TODO: , "Three levels" not implemented yet
            name="Range of fidelity level(s).",
            description="""1st-level of fidelity (low fidelity),
                2nd level of fidelity (low + high fidelity) on high-variance points.
            """,
            key="smtrain_fidelity_level",
        )
        with st.expander(
            label=f"First Level (Low Fidelity, {PYAVL} Settings)",
            expanded=False,
        ):
            avl_settings(cpacs)
        
        if fidelity_level == "Two levels":
            with st.expander(
                label=f"Second Level (High Fidelity, {CPACS2GMSH} + {SU2RUN} Settings)", 
            ):
                tab = st.tabs(
                    tabs=[CPACS2GMSH, SU2RUN],
                )
                if tab == CPACS2GMSH:
                    gmsh_settings(cpacs)
                if tab == SU2RUN:
                    su2_settings(cpacs)

    else:
        safe_remove(tixi, xpath=SMTRAIN_FIDELITY_LEVEL_XPATH)

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

    load_existing = list_vartype(
        tixi=tixi,
        default_value=["Run New Simulations", "Load Geometry Exploration Simulations"],
        key="smtrain_load_or_explore",
        name="Load Existing or Run New Simulations",
        description="Load pre-computed results from files or Generate new simulations.",
        xpath=SMTRAIN_UPLOAD_AVL_DATABASE_XPATH,
    )

    if load_existing == "Run New Simulations":
        list_vartype(
            tixi=tixi,
            xpath=SMTRAIN_OBJECTIVE_XPATH,
            description="Objective function list for the surrogate model to predict",
            name="Objective",
            key="smtrain_objective",
            default_value=OBJECTIVES_LIST,
        )

        int_vartype(
            tixi=tixi,
            xpath=SMTRAIN_NSAMPLES_GEOMETRY_XPATH,
            default_value=10,
            key="smtrain_sample_number",
            name="Number of samples",
            description="""
                Samples corresponds to the number of distinct geometry we will run the solver on.
            """,
        )

        xpath = SMTRAIN_GEOM_WING_OPTIMISE
        uid_list = return_uid_wings_sections(tixi)
        wings = sorted(set(wing_uid for (wing_uid, _) in uid_list))

        st.markdown('###### Select the wings to optimise')
        for i_wing, wing_uid in enumerate(wings):
            default_value = True if i_wing == 0 else False
            selected_wing_xpath = xpath + f"/{wing_uid}"
            wing_optimized = bool_vartype(
                tixi=tixi,
                xpath=selected_wing_xpath,
                default_value=default_value,
                key=f"smtrain_{wing_uid}_selected",
                name=f"Wing {wing_uid=}",
                description=f"Optimize wing {wing_uid=}.",
            )

            if wing_optimized:
                _wing_settings(
                    tixi=tixi,
                    uid_list=uid_list,
                    wing_uid=wing_uid,
                    selected_wing_xpath=selected_wing_xpath,
                )
    elif load_existing == "Load Geometry Exploration Simulations":
        st.info("Whats going on ?")
        # uploaded_existing_simulations = st.file_uploader(
        #     "Upload simulations file",
        #     type=["csv"],
        #     key='existing_avl_results'
        # )
        # if uploaded_existing_simulations:
        #     # Ensure working directory exists
        #     working_dir = Path(st.session_state.workflow.working_dir)
        #     working_dir.mkdir(parents=True, exist_ok=True)

        #     # Save the uploaded CSV to the working directory
        #     csv_filename = 'avl_simulations_results.csv'
        #     csv_path = working_dir / csv_filename
        #     with open(csv_path, "wb") as f:
        #         f.write(uploaded_existing_simulations.getbuffer())

        #     # Load the CSV into a DataFrame and store both DataFrame
        #     # and path in session_state
        #     simulations_df = pd.read_csv(csv_path)
        #     st.session_state.simulations_df = simulations_df
        #     st.session_state.simulations_file_path = str(csv_path)

        #     st.success("CSV copied to working directory!")
        #     st.write(f"DataFrame shape: {simulations_df.shape}")
        #     st.dataframe(simulations_df.head())
        #     st.write(f"Persistent path: {csv_path}")


def _wing_settings(
    tixi: Tixi3,
    xpath,
    uid_list,
    wing_uid,
    selected_wing_xpath,
):
    # Sections of specific wing
    sections = [
        sec_uid
        for (wng, sec_uid) in uid_list
        if wng == wing_uid
    ]
    st.markdown(f"##### ↪️ Sections of {wing_uid}")
    for i_sec, section_uid in enumerate(sections):
        sec_left_col, sec_right_col = st.columns([2, 3])
        sec_selected_xpath = selected_wing_xpath + f"/{section_uid}"

        with sec_left_col:
            default_value = True if i_sec == 0 else False
            sec_optimized = bool_vartype(
                tixi=tixi,
                xpath=sec_selected_xpath,
                key=f"smtrain_{wing_uid}_{section_uid}_selected",
                description=f"Optimize {section_uid=} of {wing_uid=}",
                default_value=default_value,
                name=f"Section {section_uid=} of {wing_uid=}"
            )

        with sec_right_col:
            if sec_optimized:
                base_xpath = xpath + f"/{wing_uid}/sections/{section_uid}/parameters"
                for i_param, param in enumerate(WING_PARAMETERS):
                    params_xpath = base_xpath + f"/{param}"
                    default_value = True if i_param == 0 else False
                    status = bool_vartype(
                        tixi=tixi,
                        xpath=params_xpath + "/status",
                        default_value=default_value,
                        name=f"Status of {param}",
                        key=f"smtrain_{wing_uid}_{section_uid}_{param}_status",
                        description=f"""Choose if you want to optimize {param=}
                            of geometry element {wing_uid=} at {section_uid=}
                        """,
                    )

                    if status:
                        params_current_value_xpath = get_xpath_for_param(
                            tixi=tixi,
                            param=param,
                            wing_uid=wing_uid,
                            section_uid=section_uid
                        )

                        current_value = get_value_or_default(
                            tixi=tixi,
                            xpath=params_current_value_xpath,
                            default_value=0.0,
                        )

                        default_min_value = 0.8 * current_value
                        default_max_value = 1.2 * current_value

                        col_min, col_val, col_max = st.columns([0.5, 0.5, 0.5])

                        with col_min:
                            float_vartype(
                                tixi=tixi,
                                xpath=params_xpath + "/min_value/value",
                                description=f"""Define the range (1d design space) for {param=}
                                    of geometry element {wing_uid=} at {section_uid=}
                                """,
                                key=f"smtrain_{wing_uid}_{section_uid}_{param}_min_value",
                                default_value=default_min_value,
                                name=f"Minimum value of {param=}",
                                max_value=current_value,
                            )
                        with col_val:
                            st.markdown("Current value:")
                            st.markdown(f"<= {current_value:.3f} <=")

                        with col_max:
                            float_vartype(
                                tixi=tixi,
                                xpath=params_xpath + "/max_value/value",
                                description=f"""Define the range (1d design space) for {param=}
                                    of geometry element {wing_uid=} at {section_uid=}
                                """,
                                key=f"smtrain_{wing_uid}_{section_uid}_{param}_min_value",
                                default_value=default_max_value,
                                name=f"Maximum value of {param=}",
                                min_value=current_value,
                            )
