"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

GUI Interface of SU2Run.
"""

# Imports

import streamlit as st

from cpacspy.cpacsfunctions import get_value
from ceasiompy.utils.ceasiompyutils import safe_remove
from ceasiompy.utils.guiobjects import (
    int_vartype,
    list_vartype,
    bool_vartype,
    float_vartype,
    dataframe_vartype,
)

from cpacspy.cpacspy import CPACS

from ceasiompy.CPACS2GMSH import HAS_PENTAGROW
from ceasiompy.SU2Run import (
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
    GEOMETRY_MODE_XPATH,
)


# Functions
def gui_settings(cpacs: CPACS) -> None:
    tixi = cpacs.tixi

    if get_value(tixi, GEOMETRY_MODE_XPATH) == "3D":
        with st.container(
            border=True,
        ):
            default_value = EULER_OR_RANS if HAS_PENTAGROW else ["EULER"]
            list_vartype(
                tixi=tixi,
                default_value=default_value,
                xpath=SU2_CONFIG_RANS_XPATH,
                name="Euler or RANS simulation",
                key="su2run_euler_or_rans",
                description="Running Euler or RANS calculation.",
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
            key="max_iter",
            description="Maximum number of iterations.",
        )

        with st.container(
            border=True,
        ):
            su2_run_damping_der = bool_vartype(
                tixi=tixi,
                xpath=SU2_DAMPING_DER_XPATH,
                default_value=False,
                name="Damping Derivatives",
                key="su2_run_damping_der",
                description="To check if damping derivatives should be calculated or not.",
            )
            if su2_run_damping_der:
                float_vartype(
                    tixi=tixi,
                    xpath=SU2_ROTATION_RATE_XPATH,
                    default_value=1.0,
                    name="Damping Der. rotation rate",
                    key="damping_derivatives_rotation_rate",
                    description="Rotation rate use to calculate damping derivatives.",
                )
            else:
                safe_remove(tixi, xpath=SU2_ROTATION_RATE_XPATH)

        with st.container(
            border=True,
        ):
            st.markdown("#### CFL Settings")
            float_vartype(
                tixi=tixi,
                xpath=SU2_CFL_NB_XPATH,
                default_value=1.0,
                name="CFL Number",
                key="cfl_nb",
                description="CFL Number, Courant–Friedrichs–Lewy condition.",
            )

            float_vartype(
                tixi=tixi,
                xpath=SU2_CFL_MIN_XPATH,
                default_value=0.5,
                name="CFL Minimum Value",
                key="cfl_min",
                description="CFL Minimum Value.",
            )

            float_vartype(
                tixi=tixi,
                xpath=SU2_CFL_MAX_XPATH,
                default_value=100,
                name="CFL Maximum Value",
                key="cfl_max",
                description="CFL Maximum Value.",
            )

            su2run_cfl_adapt = bool_vartype(
                tixi=tixi,
                xpath=SU2_CFL_ADAPT_XPATH,
                default_value=False,
                name="CFL Adaptation",
                key="su2run_cfl_adapt",
                description="CFL Adaptation.",
            )

            if su2run_cfl_adapt:
                with st.container(
                    border=True,
                ):
                    st.markdown("#### CFL Adaptation Settings")

                    float_vartype(
                        tixi=tixi,
                        xpath=SU2_CFL_ADAPT_PARAM_DOWN_XPATH,
                        default_value=0.5,
                        name="CFL Adaptation Factor Down",
                        key="cfl_adapt_param_down",
                        description="CFL Adaptation Factor Down.",
                    )

                    float_vartype(
                        tixi=tixi,
                        xpath=SU2_CFL_ADAPT_PARAM_UP_XPATH,
                        default_value=1.5,
                        name="CFL Adaptation Factor Up",
                        description="CFL Adaptation Factor Up.",
                        key="cfl_adapt_param_up",
                    )
            else:
                safe_remove(tixi, xpath=SU2_CFL_ADAPT_PARAM_DOWN_XPATH)
                safe_remove(tixi, xpath=SU2_CFL_ADAPT_PARAM_UP_XPATH)

        bool_vartype(
            tixi=tixi,
            xpath=SU2_EXTRACT_LOAD_XPATH,
            default_value=False,
            name="Extract loads",
            key="extract_loads",
            description="Option to extract loads (forces in each point) from results.",
        )

        int_vartype(
            tixi=tixi,
            xpath=SU2_MG_LEVEL_XPATH,
            default_value=3,
            name="Multigrid Level",
            key="mg_level",
            description="Multi-grid level (0 = no multigrid)",
        )

        bool_vartype(
            tixi=tixi,
            xpath=SU2_UPDATE_WETTED_AREA_XPATH,
            default_value=True,
            name="Update Wetted Area",
            key="update_wetted_area",
            description="Option to update the wetted area from the latest SU2 result.",
        )

    with st.container(
        border=True,
    ):
        su2run_control_surf = bool_vartype(
            tixi=tixi,
            xpath=SU2_CONTROL_SURF_BOOL_XPATH,
            default_value=False,
            name="Control Surfaces",
            key="su2run_control_surf",
            description="To check if control surfaces deflections should be calculated.",
        )

        if su2run_control_surf:
            dataframe_vartype(
                tixi=tixi,
                xpath=SU2_CONTROL_SURF_ANGLE_XPATH,
                description="Rotation angle of control surface.",
                default_value=[0.0],
                name="Control Surface",
                key="su2run_ctrl_surf_deflection",
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
            key="include_actuator_disk",
            description="To check if actuator disk(s) should be included.",
        )

        if include_actuator_disk:
            float_vartype(
                tixi=tixi,
                xpath=PROPELLER_THRUST_XPATH,
                default_value=3000,
                name="Thrust",
                key="thrust",
                description="Aircraft thrust.",
            )
            bool_vartype(
                tixi=tixi,
                xpath=PROPELLER_BLADE_LOSS_XPATH,
                default_value=False,
                name="Tip loss correction",
                key="prandtl",
                description="Enable or disable the tip loss correction of Prandtl.",
            )

    with st.container(
        border=True,
    ):
        su2run_fixed_cl = bool_vartype(
            tixi=tixi,
            xpath=SU2_FIXED_CL_XPATH,
            default_value=False,
            name="Fixed CL",
            key="su2run_fixed_cl",
            description="FIXED_CL_MODE parameter for SU2.",
        )

        if su2run_fixed_cl:
            with st.container(
                border=True,
            ):
                st.markdown("#### Fixed CL Settings")

                float_vartype(
                    tixi=tixi,
                    xpath=RANGE_CRUISE_MACH_XPATH,
                    default_value=0.78,
                    name="Cruise Mach",
                    key="cruise_mach",
                    description="Aircraft cruise Mach number.",
                )

                float_vartype(
                    tixi=tixi,
                    xpath=RANGE_CRUISE_ALT_XPATH,
                    default_value=120000.0,
                    name="Cruise Altitude",
                    key="cruise_alt",
                    description="Aircraft cruise altitude.",
                )

                float_vartype(
                    tixi=tixi,
                    xpath=SU2_TARGET_CL_XPATH,
                    default_value=1.0,
                    name="Target CL value",
                    key="target_cl",
                    description="""
                        Value of CL to achieve to have a level flight with the given conditions.
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
            key="compute_derivatives",
            description="Computing dot derivatives.",
        )
        if su2_dot_derivatives:
            with st.container(
                border=True,
            ):
                int_vartype(
                    tixi=tixi,
                    xpath=SU2_DYNAMICDERIVATIVES_TIMESIZE_XPATH,
                    default_value=20,
                    name="Time Size",
                    key="time_size",
                    description="Size of time vector i.e. t = 2pi * (0, 1/n-1, ..., n-2/n-1)",
                )
                float_vartype(
                    tixi=tixi,
                    xpath=SU2_DYNAMICDERIVATIVES_AMPLITUDE_XPATH,
                    default_value=1.0,
                    name="Oscillation's amplitude",
                    key="oscillation_amplitude",
                    description="Oscillation: a * sin(w t) and a > 0",
                )
                float_vartype(
                    tixi=tixi,
                    xpath=SU2_DYNAMICDERIVATIVES_FREQUENCY_XPATH,
                    default_value=0.087,
                    name="Oscillation's angular frequency (w)",
                    key="oscillation_frequency",
                    description="Oscillation: a * sin(w t) and w > 0",
                )
                int_vartype(
                    tixi=tixi,
                    xpath=SU2_DYNAMICDERIVATIVES_INNERITER_XPATH,
                    default_value=10,
                    name="Maximum number of inner iterations",
                    key="inner_iter",
                    description="Maximum number of inner iterations",
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
