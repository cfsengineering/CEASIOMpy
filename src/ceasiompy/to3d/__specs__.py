# Imports
import streamlit as st
import plotly.graph_objects as go

from cpacspy.cpacsfunctions import get_value
from ceasiompy.utils.plot import get_aircraft_mesh_data
from ceasiompy.utils.guiobjects import (
    float_vartype,
)

from cpacspy.cpacspy import CPACS

from ceasiompy.utils.commonxpaths import GEOMETRY_MODE_XPATH
from ceasiompy.to3d import (
    MODULE_NAME,
    TO_THREED_SPAN_XPATH,
    TO_THREED_CHORD_XPATH,
    TO_THREED_TWIST_XPATH,
    TO_THREED_SWEEP_XPATH,
    TO_THREED_DIHEDRAL_XPATH,
)


# Methods

def _get_chord(cpacs: CPACS) -> float:
    """Get Chord Length of current airfoil-CPACS (2D)."""
    return 0.0


# Function

def gui_settings(cpacs: CPACS) -> None:
    # Define variables
    tixi = cpacs.tixi
    domain_preview_placeholder = st.empty()     # Placeholder for the 3D-CPACS geometry

    # Input CPACS must be 2D.
    dim_mode = get_value(
        tixi=tixi,
        xpath=GEOMETRY_MODE_XPATH,
    )

    if dim_mode != "2D":
        raise ValueError(f"CPACS must be 2D to use {MODULE_NAME} module.")

    airfoil_chord = _get_chord(cpacs)

    # Span/Chord Settings
    left_col, right_col = st.columns(2)

    with left_col:
        float_vartype(
            tixi=tixi,
            name="Span Length",
            help="Span Length of the first segment.",
            xpath=TO_THREED_SPAN_XPATH,
            default_value=1.0,
        )
    with right_col:
        float_vartype(
            tixi=tixi,
            name="Chord Length",
            help="Chord Length of the second section.",
            xpath=TO_THREED_CHORD_XPATH,
            default_value=airfoil_chord,
            min_value=0.01 * airfoil_chord,
            max_value=airfoil_chord,
        )

    # Angles
    left_col, mid_col, right_col = st.columns(3)
    with left_col:
        float_vartype(
            tixi=tixi,
            name="Twist",
            help="""Twist Angle (also called washout) is the intentional reduction
                of a wing's angle of incidence from the root to the tip,
                typically by 2 to 5 degrees.""",
            xpath=TO_THREED_TWIST_XPATH,
            default_value=3.0,
            unit="°",
        )
    with mid_col:
        float_vartype(
            tixi=tixi,
            name="Sweep",
            help="""Sweep Angle of the segment. Designed primarily to delay the onset
                of wave drag and compressibility effects
                at high subsonic and supersonic speeds.""",
            xpath=TO_THREED_SWEEP_XPATH,
            default_value=0.0,
            unit="°",
        )
    with right_col:
        float_vartype(
            tixi=tixi,
            name="Dihedral",
            help="""Dihedral Angle of the segment. It is the upward angle of
                an aircraft's wings from the horizontal,
                designed to improve lateral stability.""",
            xpath=TO_THREED_DIHEDRAL_XPATH,
            default_value=0.0,
            unit="°",
        )

    # Convert to 3D cpacs
    cpacs_file_3d = cpacs.cpacs_file + "_3d"
    cpacs.save_cpacs(cpacs_file_3d)

    cpacs_3d = CPACS(cpacs_file_3d)
    fig = go.Figure()
    try:
        output = get_aircraft_mesh_data(cpacs_3d)
        if output is None:
            st.warning(f"Can not display {cpacs.ac_name=}. Could not retrieve mesh data.")
            return None

        x, y, z, i, j, k = output
        fig.add_trace(
            go.Mesh3d(
                x=x,
                y=y,
                z=z,
                i=i,
                j=j,
                k=k,
                opacity=0.9,
                color="lightgrey",
                flatshading=False,
                lighting=dict(
                    ambient=0.5,
                    diffuse=0.2,
                    specular=0.3,
                    roughness=0.2,
                ),
                lightposition=dict(x=0, y=100, z=0),
                name="CPACS geometry",
                showscale=False,
            )
        )
    except Exception as e:
        st.warning(f"Cannot generate CPACS mesh preview: {e=}")

    domain_preview_placeholder.plotly_chart(
        fig,
        key="to_3d_domain_preview",
        width="stretch",
    )
