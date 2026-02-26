# Imports
import shutil
import numpy as np
import streamlit as st
import plotly.graph_objects as go

from cpacspy.cpacsfunctions import get_value
from ceasiompy.utils.plot import get_aircraft_mesh_data
from ceasiompy.utils.guiobjects import (
    add_value,
    float_vartype,
)

from pathlib import Path
from cpacspy.cpacspy import CPACS

from ceasiompy import log
from ceasiompy.utils.commonxpaths import (
    WINGS_XPATH,
    GEOMETRY_MODE_XPATH,
)
from ceasiompy.to3d import (
    MODULE_NAME,
    TO_THREED_SPAN_XPATH,
    TO_THREED_CHORD_XPATH,
    TO_THREED_TWIST_XPATH,
    TO_THREED_SWEEP_XPATH,
    TO_THREED_DIHEDRAL_XPATH,
)


# Function

def gui_settings(cpacs: CPACS) -> None:
    # Input CPACS must be 2D
    tixi = cpacs.tixi
    dim_mode = get_value(
        tixi=tixi,
        xpath=GEOMETRY_MODE_XPATH,
    )

    if dim_mode != "2D":
        raise ValueError(f"CPACS must be 2D to use {MODULE_NAME} module.")

    # Define variables
    domain_preview_placeholder = st.empty()     # Placeholder for the 3D-CPACS geometry
    wing_xpath = WINGS_XPATH + "/wing[1]"
    section_xpath = wing_xpath + "/sections/section[2]/transformation"
    positioning_xpath = wing_xpath + "/positionings/positioning[2]"
    chord_xpath = section_xpath + "/scaling/x"

    cpacs_path = Path(cpacs.cpacs_file)
    cpacs_3d_file = Path(cpacs_path.parent, cpacs_path.stem + f"_{MODULE_NAME}.xml")
    shutil.copy2(cpacs.cpacs_file, cpacs_3d_file)

    log.info(f"airfoil-CPACS: {cpacs.cpacs_file}")
    log.info(f"3D-CPACS: {cpacs_3d_file}")
    cpacs_3d = CPACS(cpacs_3d_file)
    tixi_3d = cpacs_3d.tixi

    airfoil_chord = float(get_value(
        tixi=cpacs.tixi,
        xpath=chord_xpath,
    ))

    # Span/Chord Settings
    left_col, right_col = st.columns(2)

    with left_col:
        span_length = float_vartype(
            tixi=tixi,
            name="Span Length",
            help="Span Length of the first segment.",
            xpath=TO_THREED_SPAN_XPATH,
            default_value=1.5 * airfoil_chord,
            unit="m",
        )
    with right_col:
        chord_length = float_vartype(
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
        twist_angle = float_vartype(
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
        sweep_angle = float_vartype(
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
        dihedral_angle = float_vartype(
            tixi=tixi,
            name="Dihedral",
            help="""Dihedral Angle of the segment. It is the upward angle of
                an aircraft's wings from the horizontal,
                designed to improve lateral stability.""",
            xpath=TO_THREED_DIHEDRAL_XPATH,
            default_value=0.0,
            unit="°",
        )

    twist_xpath = section_xpath + "/rotation/y"
    span_xpath = positioning_xpath + "/length"
    sweep_xpath = positioning_xpath + "/sweepAngle"
    dihedral_xpath = positioning_xpath + "/dihedralAngle"

    add_value(
        tixi=tixi_3d,
        xpath=chord_xpath,
        value=chord_length,
    )
    add_value(
        tixi=tixi_3d,
        xpath=twist_xpath,
        value=twist_angle,
    )

    # Update with variables
    add_value(
        tixi=tixi_3d,
        xpath=span_xpath,
        value=span_length,
    )
    add_value(
        tixi=tixi_3d,
        xpath=sweep_xpath,
        value=sweep_angle,
    )
    add_value(
        tixi=tixi_3d,
        xpath=dihedral_xpath,
        value=dihedral_angle,
    )
    add_value(
        tixi=tixi_3d,
        xpath=GEOMETRY_MODE_XPATH,
        value="3D",
    )
    cpacs_3d.save_cpacs(cpacs_3d_file, overwrite=True)
    cpacs_3d = CPACS(cpacs_3d_file)

    fig = go.Figure()
    try:
        output = get_aircraft_mesh_data(
            cpacs=cpacs_3d,
            force_regenerate=True,
        )
        if output is None:
            st.warning(f"Can not display {cpacs_3d.ac_name=}. Could not retrieve mesh data.")
            return None

        x, y, z, i, j, k = output

        # Compute bounds and cube size
        min_x, max_x = np.min(x), np.max(x)
        min_y, max_y = np.min(y), np.max(y)
        min_z, max_z = np.min(z), np.max(z)
        center_x = (min_x + max_x) / 2
        center_y = (min_y + max_y) / 2
        center_z = (min_z + max_z) / 2
        max_range = max(max_x - min_x, max_y - min_y, max_z - min_z) / 2
        zoom_out_factor = 1.5
        max_range *= zoom_out_factor

        # Set axis limits so the mesh is centered in a cube
        x_range = [center_x - max_range, center_x + max_range]
        y_range = [center_y - max_range, center_y + max_range]
        z_range = [center_z - max_range, center_z + max_range]

        fig = go.Figure(
            data=[
                go.Mesh3d(
                    x=x, y=y, z=z,
                    i=i, j=j, k=k,
                    opacity=1.0,
                    color='lightgrey',
                    flatshading=False,
                    lighting=dict(
                        ambient=0.5,
                        diffuse=0.2,
                        specular=0.3,
                        roughness=0.2,
                    ),
                    lightposition=dict(
                        x=0,
                        y=100,
                        z=0,
                    ),
                )
            ]
        )

        fig.update_layout(
            margin=dict(l=0, r=0, t=0, b=0),
            scene=dict(
                xaxis=dict(range=x_range),
                yaxis=dict(range=y_range),
                zaxis=dict(range=z_range),
                aspectmode="cube",
            ),
        )

    except Exception as e:
        st.warning(f"Cannot generate CPACS mesh preview: {e=}")

    domain_preview_placeholder.plotly_chart(
        fig,
        key="to_3d_domain_preview",
        width="stretch",
    )
