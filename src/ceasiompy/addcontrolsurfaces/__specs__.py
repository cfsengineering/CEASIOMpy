"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

GUI Interface of CPACSUpdater.
"""

# Imports
import shutil
import numpy as np
import streamlit as st
import plotly.graph_objects as go

from ceasiompy.utils.plot import get_aircraft_mesh_data
from ceasiompy.utils.geometryfunctions import get_segments
from ceasiompy.addcontrolsurfaces.addcontrolsurfaces import add_control_surfaces
from ceasiompy.utils.guiobjects import (
    add_value,
    add_ctrl_surf_vartype,
)

from pathlib import Path
from cpacspy.cpacspy import CPACS

from ceasiompy.addcontrolsurfaces import (
    MODULE_NAME,
    CONTROL_SURFACES_LIST,
    ADDCONTROLSURFACES_CTRLSURF_XPATH,
)


# Functions
def gui_settings(cpacs: CPACS) -> None:
    """GUI Settings of CPACSUpdater module."""
    tixi = cpacs.tixi
    domain_preview_placeholder = st.empty()
    domain_preview_placeholder.markdown(
        body="<div style='height: 440px;'></div>",
        unsafe_allow_html=True,
    )

    segments_list = get_segments(tixi)
    wings = {}
    for wing_uid, segment_uid in segments_list:
        wings.setdefault(wing_uid, []).append(segment_uid)

    for wing_uid, segment_uids in wings.items():
        st.markdown("---")
        st.markdown(f"**Wing {wing_uid}**")
        for segment_uid in segment_uids:
            add_ctrl_surf_vartype(
                tixi=tixi,
                key=f"control_surface_{wing_uid}_{segment_uid}",
                default_value=CONTROL_SURFACES_LIST,
                name=f"Control Surface for segment {segment_uid} of wing {wing_uid}.",
                help="""
                    Select the type of control surface to add
                    for at specific wing and segment of wing.
                """,
                xpath=ADDCONTROLSURFACES_CTRLSURF_XPATH
                + f"/{wing_uid}/{segment_uid}",
            )

    fig = go.Figure()
    fig.update_layout(height=420, margin=dict(l=10, r=10, t=10, b=10))
    try:
        cpacs_path = Path(cpacs.cpacs_file)
        cpacs_ctrlsurf_path = Path(cpacs_path.parent, cpacs_path.stem + f"_{MODULE_NAME}.xml")
        shutil.copy2(cpacs.cpacs_file, cpacs_ctrlsurf_path)

        cpacs_ctrlsurf = CPACS(cpacs_ctrlsurf_path)
        tixi_ctrlsurf = cpacs_ctrlsurf.tixi

        # Propagate live GUI settings into the copied preview CPACS.
        for wing_uid, segment_uids in wings.items():
            for segment_uid in segment_uids:
                base_xpath = ADDCONTROLSURFACES_CTRLSURF_XPATH + f"/{wing_uid}/{segment_uid}"
                for field in ("ctrlsurf", "deformation_angle", "left_trsl", "right_trsl"):
                    field_xpath = f"{base_xpath}/{field}"
                    if tixi.checkElement(field_xpath):
                        add_value(
                            tixi=tixi_ctrlsurf,
                            xpath=field_xpath,
                            value=tixi.getTextElement(field_xpath),
                        )

        add_control_surfaces(cpacs_ctrlsurf.tixi)
        cpacs_ctrlsurf.save_cpacs(cpacs_ctrlsurf_path, overwrite=True)
        cpacs_ctrlsurf = CPACS(cpacs_ctrlsurf_path)

        output = get_aircraft_mesh_data(cpacs=cpacs_ctrlsurf, force_regenerate=True)
        if output is not None:
            x, y, z, i, j, k = output
            min_x, max_x = np.min(x), np.max(x)
            min_y, max_y = np.min(y), np.max(y)
            min_z, max_z = np.min(z), np.max(z)
            x_range = [min_x, max_x]
            y_range = [min_y, max_y]
            z_range = [min_z, max_z]

            def _axis_values(vmin: float, vmax: float, count: int) -> list[float]:
                if count <= 0:
                    return []
                if count == 1:
                    return [(vmin + vmax) * 0.5]
                step = (vmax - vmin) / (count - 1)
                return [vmin + i * step for i in range(count)]

            x_ticks = _axis_values(x_range[0], x_range[1], 3)
            y_ticks = _axis_values(y_range[0], y_range[1], 3)
            z_ticks = _axis_values(z_range[0], z_range[1], 2)

            fig = go.Figure(
                data=[
                    go.Mesh3d(
                        x=x,
                        y=y,
                        z=z,
                        i=i,
                        j=j,
                        k=k,
                        opacity=1.0,
                        color="#d3d3d3",
                        flatshading=False,
                        lighting=dict(
                            ambient=0.45,
                            diffuse=0.55,
                            specular=0.08,
                            roughness=0.75,
                            fresnel=0.1,
                        ),
                        lightposition=dict(x=8, y=8, z=12),
                    )
                ]
            )
            fig.update_layout(
                margin=dict(l=10, r=10, t=10, b=10),
                height=420,
                font=dict(color="black"),
                uirevision="add_controlsurfaces_domain_preview",
                scene=dict(
                    xaxis=dict(
                        title="X",
                        titlefont=dict(color="black"),
                        tickfont=dict(color="black"),
                        range=x_range,
                        tickmode="array",
                        tickvals=x_ticks,
                        showgrid=True,
                        gridcolor="black",
                        zeroline=False,
                        backgroundcolor="white",
                    ),
                    yaxis=dict(
                        title="Y",
                        titlefont=dict(color="black"),
                        tickfont=dict(color="black"),
                        range=y_range,
                        tickmode="array",
                        tickvals=y_ticks,
                        showgrid=True,
                        gridcolor="black",
                        zeroline=False,
                        backgroundcolor="white",
                    ),
                    zaxis=dict(
                        title="Z",
                        titlefont=dict(color="black"),
                        tickfont=dict(color="black"),
                        range=z_range,
                        tickmode="array",
                        tickvals=z_ticks,
                        showgrid=True,
                        gridcolor="black",
                        zeroline=False,
                        backgroundcolor="white",
                    ),
                    aspectmode="data",
                ),
            )
    except Exception as e:
        st.warning(f"Cannot generate CPACS mesh preview: {e=}")

    domain_preview_placeholder.plotly_chart(
        fig,
        key="add_controlsurfaces_domain_preview",
        width="stretch",
    )
