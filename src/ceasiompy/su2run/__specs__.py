"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

GUI Interface of SU2Run.
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
)

from cpacspy.cpacspy import CPACS

from ceasiompy.cpacs2gmsh import HAS_PENTAGROW
from ceasiompy.su2run import (
    EULER_OR_RANS,
    SU2_DAMPING_DER_XPATH,
    SU2_ROTATION_RATE_XPATH,
    SU2_CONTROL_SURF_BOOL_XPATH,
    SU2_CONTROL_SURF_ANGLE_XPATH,
    SU2_CONFIG_RANS_XPATH,
    SU2_MAX_ITER_XPATH,
    SU2_CFL_NB_XPATH,
    SU2_CFL_ADAPT_XPATH,
    SU2_CFL_ADAPT_PARAM_DOWN_XPATH,
    SU2_CFL_ADAPT_PARAM_UP_XPATH,
    SU2_CFL_MIN_XPATH,
    SU2_CFL_MAX_XPATH,
    SU2_MG_LEVEL_XPATH,
    SU2_UPDATE_WETTED_AREA_XPATH,
    SU2_EXTRACT_LOAD_XPATH,
    SU2_ACTUATOR_DISK_XPATH,
    SU2_DYNAMICDERIVATIVES_BOOL_XPATH,
    SU2_DYNAMICDERIVATIVES_TIMESIZE_XPATH,
    SU2_DYNAMICDERIVATIVES_AMPLITUDE_XPATH,
    SU2_DYNAMICDERIVATIVES_FREQUENCY_XPATH,
    SU2_DYNAMICDERIVATIVES_INNERITER_XPATH,
    SU2_TARGET_CL_XPATH,
    SU2_FIXED_CL_XPATH,
)

from ceasiompy.utils.commonxpaths import (
    PROPELLER_THRUST_XPATH,
    PROPELLER_BLADE_LOSS_XPATH,
    RANGE_CRUISE_MACH_XPATH,
    RANGE_CRUISE_ALT_XPATH,
)


# Functions
def gui_settings(cpacs: CPACS) -> None:
    tixi = cpacs.tixi

    with st.container(
        border=True,
    ):
        default_value = EULER_OR_RANS if HAS_PENTAGROW else ["EULER"]
        list_vartype(
            tixi=tixi,
            default_value=default_value,
            xpath=SU2_CONFIG_RANS_XPATH,
            name="Euler or RANS simulation",
            key=f"{cpacs.ac_name}_su2run_euler_or_rans",
            help="Running Euler or RANS calculation.",
        )

    with st.expander(
        label="Simulation Settings",
        expanded=True,
    ):
        int_vartype(
            tixi=tixi,
            xpath=SU2_MAX_ITER_XPATH,
            default_value=1000,
            name="Maximum iterations",
            key=f"{cpacs.ac_name}_max_iter",
            help="Maximum number of iterations.",
        )

        with st.container(
            border=True,
        ):
            su2_run_damping_der = bool_vartype(
                tixi=tixi,
                xpath=SU2_DAMPING_DER_XPATH,
                default_value=False,
                name="Damping Derivatives",
                key=f"{cpacs.ac_name}_su2_run_damping_der",
                help="To check if damping derivatives should be calculated or not.",
            )
            if su2_run_damping_der:
                float_vartype(
                    tixi=tixi,
                    xpath=SU2_ROTATION_RATE_XPATH,
                    default_value=1.0,
                    name="Damping Der. rotation rate",
                    key=f"{cpacs.ac_name}_damping_derivatives_rotation_rate",
                    help="Rotation rate use to calculate damping derivatives.",
                )
            else:
                safe_remove(tixi, xpath=SU2_ROTATION_RATE_XPATH)

        with st.container(
            border=True,
        ):
            st.markdown("**CFL Settings**")
            left_col, mid_col, right_col = st.columns(3)
            with left_col:
                float_vartype(
                    tixi=tixi,
                    xpath=SU2_CFL_NB_XPATH,
                    default_value=1.0,
                    name="CFL Number",
                    key=f"{cpacs.ac_name}_cfl_nb",
                    help="CFL Number, Courant–Friedrichs–Lewy condition.",
                )

            with mid_col:
                float_vartype(
                    tixi=tixi,
                    xpath=SU2_CFL_MIN_XPATH,
                    default_value=0.5,
                    name="CFL Minimum Value",
                    key=f"{cpacs.ac_name}_cfl_min",
                    help="CFL Minimum Value.",
                )

            with right_col:
                float_vartype(
                    tixi=tixi,
                    xpath=SU2_CFL_MAX_XPATH,
                    default_value=100,
                    name="CFL Maximum Value",
                    key=f"{cpacs.ac_name}_cfl_max",
                    help="CFL Maximum Value.",
                )

            su2run_cfl_adapt = bool_vartype(
                tixi=tixi,
                xpath=SU2_CFL_ADAPT_XPATH,
                default_value=False,
                name="CFL Adaptation",
                key=f"{cpacs.ac_name}_su2run_cfl_adapt",
                help="CFL Adaptation.",
            )

            if su2run_cfl_adapt:
                with st.container(
                    border=True,
                ):
                    st.markdown("**CFL Adaptation Settings**")

                    left_col, right_col = st.columns(2)
                    with left_col:
                        float_vartype(
                            tixi=tixi,
                            xpath=SU2_CFL_ADAPT_PARAM_DOWN_XPATH,
                            default_value=0.5,
                            name="CFL Adaptation Factor Down",
                            key=f"{cpacs.ac_name}_cfl_adapt_param_down",
                            help="CFL Adaptation Factor Down.",
                        )

                    with right_col:
                        float_vartype(
                            tixi=tixi,
                            xpath=SU2_CFL_ADAPT_PARAM_UP_XPATH,
                            default_value=1.5,
                            name="CFL Adaptation Factor Up",
                            help="CFL Adaptation Factor Up.",
                            key=f"{cpacs.ac_name}_cfl_adapt_param_up",
                        )
            else:
                safe_remove(tixi, xpath=SU2_CFL_ADAPT_PARAM_DOWN_XPATH)
                safe_remove(tixi, xpath=SU2_CFL_ADAPT_PARAM_UP_XPATH)

        bool_vartype(
            tixi=tixi,
            xpath=SU2_EXTRACT_LOAD_XPATH,
            default_value=False,
            name="Extract loads",
            key=f"{cpacs.ac_name}_extract_loads",
            help="Option to extract loads (forces in each point) from results.",
        )

        int_vartype(
            tixi=tixi,
            xpath=SU2_MG_LEVEL_XPATH,
            default_value=3,
            name="Multigrid Level",
            key=f"{cpacs.ac_name}_mg_level",
            help="Multi-grid level (0 = no multigrid)",
        )

        bool_vartype(
            tixi=tixi,
            xpath=SU2_UPDATE_WETTED_AREA_XPATH,
            default_value=True,
            name="Update Wetted Area",
            key=f"{cpacs.ac_name}_update_wetted_area",
            help="Option to update the wetted area from the latest SU2 result.",
        )

    with st.container(
        border=True,
    ):
        su2run_control_surf = bool_vartype(
            tixi=tixi,
            xpath=SU2_CONTROL_SURF_BOOL_XPATH,
            default_value=False,
            name="Control Surfaces",
            key=f"{cpacs.ac_name}_su2run_control_surf",
            help="To check if control surfaces deflections should be calculated.",
        )

        if su2run_control_surf:
            dataframe_vartype(
                tixi=tixi,
                xpath=SU2_CONTROL_SURF_ANGLE_XPATH,
                help="Rotation angle of control surface.",
                default_value=[0.0],
                name="Control Surface",
                key=f"{cpacs.ac_name}_su2run_ctrl_surf_deflection",
            )
        else:
            safe_remove(tixi, xpath=SU2_CONTROL_SURF_ANGLE_XPATH)

    with st.container(
        border=True,
    ):
        include_actuator_disk = bool_vartype(
            tixi=tixi,
            xpath=SU2_ACTUATOR_DISK_XPATH,
            default_value=False,
            name="Include actuator disk(s)",
            key=f"{cpacs.ac_name}_include_actuator_disk",
            help="To check if actuator disk(s) should be included.",
        )

        if include_actuator_disk:
            left_col, right_col = st.columns(2, vertical_alignment="bottom")
            with left_col:
                bool_vartype(
                    tixi=tixi,
                    xpath=PROPELLER_BLADE_LOSS_XPATH,
                    default_value=False,
                    name="Tip loss correction",
                    key=f"{cpacs.ac_name}_prandtl",
                    help="Enable or disable the tip loss correction of Prandtl.",
                )
            with right_col:
                float_vartype(
                    tixi=tixi,
                    xpath=PROPELLER_THRUST_XPATH,
                    default_value=3000,
                    name="Thrust",
                    key=f"{cpacs.ac_name}_thrust",
                    help="Aircraft thrust.",
                )
        else:
            safe_remove(tixi, xpath=PROPELLER_THRUST_XPATH)
            safe_remove(tixi, xpath=PROPELLER_BLADE_LOSS_XPATH)

    with st.container(
        border=True,
    ):
        su2run_fixed_cl = bool_vartype(
            tixi=tixi,
            xpath=SU2_FIXED_CL_XPATH,
            default_value=False,
            name="Fixed CL",
            key=f"{cpacs.ac_name}_su2run_fixed_cl",
            help="FIXED_CL_MODE parameter for SU2.",
        )

        if su2run_fixed_cl:
            with st.container(
                border=True,
            ):
                st.markdown("**Fixed CL Settings**")

                left_col, mid_col, right_col = st.columns(3)
                with left_col:
                    float_vartype(
                        tixi=tixi,
                        xpath=RANGE_CRUISE_MACH_XPATH,
                        default_value=0.78,
                        name="Cruise Mach",
                        key=f"{cpacs.ac_name}_cruise_mach",
                        help="Aircraft cruise Mach number.",
                    )

                with mid_col:
                    float_vartype(
                        tixi=tixi,
                        xpath=RANGE_CRUISE_ALT_XPATH,
                        default_value=120000.0,
                        name="Cruise Altitude",
                        key=f"{cpacs.ac_name}_cruise_alt",
                        help="Aircraft cruise altitude.",
                    )

                with right_col:
                    float_vartype(
                        tixi=tixi,
                        xpath=SU2_TARGET_CL_XPATH,
                        default_value=1.0,
                        name="Target CL value",
                        key=f"{cpacs.ac_name}_target_cl",
                        help="""
                            Value of CL to achieve to have a
                            level flight with the given conditions.
                        """,
                    )
        else:
            safe_remove(tixi, xpath=RANGE_CRUISE_MACH_XPATH)
            safe_remove(tixi, xpath=RANGE_CRUISE_ALT_XPATH)
            safe_remove(tixi, xpath=SU2_TARGET_CL_XPATH)

    with st.container(
        border=True,
    ):
        su2_dot_derivatives = bool_vartype(
            tixi=tixi,
            xpath=SU2_DYNAMICDERIVATIVES_BOOL_XPATH,
            default_value=False,
            name="Compute Dot derivatives",
            key=f"{cpacs.ac_name}_compute_derivatives",
            help="Computing dot derivatives.",
        )
        if su2_dot_derivatives:
            with st.container(
                border=True,
            ):
                first_col, second_col, third_col, fourth_col = st.columns(4)
                with first_col:
                    int_vartype(
                        tixi=tixi,
                        xpath=SU2_DYNAMICDERIVATIVES_TIMESIZE_XPATH,
                        default_value=20,
                        name="Time Size",
                        key=f"{cpacs.ac_name}_time_size",
                        help="Size of time vector i.e. t = 2pi * (0, 1/n-1, ..., n-2/n-1)",
                    )
                with second_col:
                    float_vartype(
                        tixi=tixi,
                        xpath=SU2_DYNAMICDERIVATIVES_AMPLITUDE_XPATH,
                        default_value=1.0,
                        name="Amplitude",
                        key=f"{cpacs.ac_name}_oscillation_amplitude",
                        help="Oscillation's amplitude: a * sin(w t) and a > 0",
                    )
                with third_col:
                    float_vartype(
                        tixi=tixi,
                        xpath=SU2_DYNAMICDERIVATIVES_FREQUENCY_XPATH,
                        default_value=0.087,
                        name="Angular Frequency",
                        key=f"{cpacs.ac_name}_oscillation_frequency",
                        help="Oscillation's angular frequency (w): a * sin(w t) and w > 0",
                    )
                with fourth_col:
                    int_vartype(
                        tixi=tixi,
                        xpath=SU2_DYNAMICDERIVATIVES_INNERITER_XPATH,
                        default_value=10,
                        name="Max nb of iterations",
                        key=f"{cpacs.ac_name}_inner_iter",
                        help="Maximum number of inner iterations",
                    )
        else:
            safe_remove(tixi, xpath=SU2_DYNAMICDERIVATIVES_TIMESIZE_XPATH)
            safe_remove(tixi, xpath=SU2_DYNAMICDERIVATIVES_AMPLITUDE_XPATH)
            safe_remove(tixi, xpath=SU2_DYNAMICDERIVATIVES_FREQUENCY_XPATH)
            safe_remove(tixi, xpath=SU2_DYNAMICDERIVATIVES_INNERITER_XPATH)

# cpacs_inout.add_input(
#     var_name="n",
#     var_type=float,
#     default_value=33,
#     unit="1/s",
#     descr="Propeller rotational velocity",
#     xpath=PROP_XPATH + "/propeller/rotational_velocity",
#     gui=True,
#     gui_name="Rotational velocity setting",
#     gui_group="Actuator disk",
# )
# cpacs_inout.add_input(
#     var_name="blades_number",
#     var_type=int,
#     default_value=3,
#     unit=None,
#     descr="Number of propeller blades",
#     xpath=PROP_XPATH + "/propeller/bladeNumber",
#     gui=True,
#     gui_name="Propeller blades numbers",
#     gui_group="Actuator disk",
# )
