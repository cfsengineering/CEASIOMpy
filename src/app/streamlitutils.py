"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed for CFS ENGINEERING, 1015 Lausanne, Switzerland

Streamlit utils functions for CEASIOMpy
"""

# Imports

import os
import re
import numpy as np
import streamlit as st
import plotly.graph_objects as go

from streamlit_float import float_init
from assistant import get_assistant_response

from stl import mesh
from PIL import Image
from pathlib import Path
from cpacspy.cpacspy import CPACS
from tigl3.tigl3wrapper import Tigl3
from tixi3.tixi3wrapper import Tixi3

from ceasiompy.utils.commonpaths import CEASIOMPY_LOGO_PATH

# Functions


def save_cpacs_file():
    """Save Settings in selected_cpacs.xml"""
    saved_cpacs_file = Path(st.session_state.workflow.working_dir, "selected_cpacs.xml")

    if "cpacs" not in st.session_state:
        st.warning("No CPACS file has been selected!")
        return None

    st.session_state.cpacs.save_cpacs(saved_cpacs_file, overwrite=True)
    st.session_state.workflow.cpacs_in = saved_cpacs_file
    st.session_state.cpacs = CPACS(saved_cpacs_file)


def color_cell(cell):
    if cell.strip() == "Stable":
        return '<td style="background-color:#d4edda;color:#155724;">Stable</td>'
    elif cell.strip() == "Unstable":
        return '<td style="background-color:#f8d7da;color:#721c24;">Unstable</td>'
    else:
        return f"<td>{cell}</td>"


def md_table_to_html(table_md):
    lines = [line for line in table_md.strip().split("\n") if line.strip()]
    if len(lines) < 2:  # Not a valid table
        return table_md
    header = lines[0].split("|")[1:-1]
    rows = [line.split("|")[1:-1] for line in lines[2:]]
    html = (
        "<table><thead><tr>"
        + "".join(f"<th>{h.strip()}</th>" for h in header)
        + "</tr></thead><tbody>"
    )
    for row in rows:
        html += "<tr>" + "".join(color_cell(cell) for cell in row) + "</tr>"
    html += "</tbody></table>"
    return html


def highlight_stability(md):
    # Regex to find markdown tables
    table_pattern = re.compile(r"((?:\|.*\n)+)")
    # Replace all markdown tables with colored HTML tables
    return table_pattern.sub(lambda m: md_table_to_html(m.group(1)), md)


def get_last_workflow():
    """Get the last workflow of the working directory"""

    if "workflow" not in st.session_state:
        st.warning("No workflow to show the result yet.")
        return

    last_workflow_nb = 0

    for dir_ in Path(st.session_state.workflow.working_dir).iterdir():
        if "Workflow_" in str(dir_):
            last_workflow_nb = max(last_workflow_nb, int(str(dir_).split("_")[-1]))

    if last_workflow_nb == 0:
        return None

    return Path(st.session_state.workflow.working_dir, f"Workflow_{last_workflow_nb:03}")


def close_cpacs_handles(cpacs: CPACS | None, *, detach: bool = True) -> None:
    """Best-effort close of CPACS (TIXI/TIGL) resources.

    Some CPACS wrappers close underlying C handles again in their destructor; to
    avoid double-close heap corruption, this helper can optionally detach the
    closed handles from the CPACS instance.
    """

    if cpacs is None:
        return

    tixi: Tixi3 | None = getattr(cpacs, "tixi", None)
    if tixi is not None:
        tixi.close()

    tigl: Tigl3 | None = getattr(cpacs, "tigl", None)
    if tigl is not None:
        tigl.close()

    if detach:
        setattr(cpacs, "tixi", None)
        setattr(cpacs, "tigl", None)


def build_default_upload(cpacs_path: Path):
    """Create a lightweight file-like object compatible with the upload flow."""

    if not cpacs_path.exists():
        st.error(f"CPACS file not found: {cpacs_path}")
        return None

    class _DefaultUploadedFile:
        def __init__(self, path: Path) -> None:
            self.name = path.name
            self._data = path.read_bytes()

        def getbuffer(self):
            return self._data

    return _DefaultUploadedFile(cpacs_path)


def create_sidebar(how_to_text, page_title="CEASIOMpy"):
    """Create side bar with a text explaining how the page should be used."""

    im = Image.open(CEASIOMPY_LOGO_PATH)
    st.set_page_config(
        page_title=page_title,
        page_icon=im,
        layout="centered",
    )
    st.markdown(
        """
        <style>
        section[data-testid="stSidebar"] {
            min-width: 220px;
            width: 220px;
            padding-top: 1rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
    st.sidebar.image(im)
    st.sidebar.markdown(how_to_text)
    contact_text = (
        "✉️ **Contact Us**\n\n"
        "Want to collaborate, request a feature ? \n \n"
        "Share ideas at [mail](mailto:ceasiompy@gmail.com)."
    )
    st.sidebar.info(contact_text)
    render_floating_ai_assistant()


def render_floating_ai_assistant(
    disabled: bool = True,
) -> None:
    """Render a floating, bottom-left chat assistant on every page."""

    if os.environ.get("CEASIOMPY_CLOUD", "False").lower() not in {"1", "true", "yes"}:
        return None

    if st.session_state.get("ai_assistant_disabled", False):
        return None

    if disabled:
        float_init()
        placeholder = st.container()
        with placeholder:
            st.markdown("**AI Assistant**")
            st.info("Coming soon.")
        placeholder.float(
            "bottom: 40px; right: 40px; width: 320px; max-height: 60vh; "
            "overflow-y: auto; border: 1px solid #d7d7d7; background: white; "
            "border-radius: 10px; padding: 12px; "
            "box-shadow: 2px 2px 10px rgba(0,0,0,0.1);"
        )
        return None

    if "ai_assistant_messages" not in st.session_state:
        st.session_state.ai_assistant_messages = [{
            "role": "assistant",
            "content": """Hi! I can help explain how to use CEASIOMpy,
                or summarize your latest CFD results.
            """,
        }]

    float_init()

    chat_container = st.container()
    with chat_container:
        header_cols = st.columns([3, 1])
        with header_cols[0]:
            st.markdown("**AI Assistant**")
        with header_cols[1]:
            if st.button(
                label="Clear",
                key="ai_assistant_clear",
                width="stretch",
            ):
                st.session_state.pop("ai_assistant_messages")
                st.rerun()

        for message in st.session_state.ai_assistant_messages:
            with st.chat_message(message["role"]):
                st.write(message["content"])

        prompt = st.chat_input("Ask about code or CFD results...")
        if prompt:
            st.session_state.ai_assistant_messages.append(
                {"role": "user", "content": prompt}
            )
            response = get_assistant_response(prompt)
            st.session_state.ai_assistant_messages.append(
                {"role": "assistant", "content": response}
            )
            st.rerun()

    chat_container.float(
        "bottom: 40px; right: 40px; width: 400px; max-height: 60vh; "
        "overflow-y: auto; border: 1px solid #d7d7d7; background: white; "
        "border-radius: 10px; padding: 12px; "
        "box-shadow: 2px 2px 10px rgba(0,0,0,0.1);"
    )


def st_directory_picker(initial_path=Path()):
    """Workaround to be able to select a directory with Streamlit. Could be remove when this
    function will be integrated into Streamlit."""

    if "path" not in st.session_state:
        st.session_state.path = initial_path.absolute().resolve()

    manual_input = st.text_input("Selected directory:", st.session_state.path)

    manual_input = Path(manual_input)
    if manual_input != st.session_state.path:
        st.session_state.path = manual_input
        st.rerun()

    _, col1, col2, col3, _ = st.columns([3, 1, 3, 1, 3])

    with col1:
        st.markdown("<div class='nav-button-container'>", unsafe_allow_html=True)
        if st.button("⬅️") and "path" in st.session_state:
            st.session_state.path = st.session_state.path.parent
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    with col2:
        subdirectroies = [
            f.stem
            for f in st.session_state.path.iterdir()
            if f.is_dir() and (not f.stem.startswith(".") and not f.stem.startswith("__"))
        ]
        if subdirectroies:
            st.session_state.new_dir = st.selectbox("Subdirectories", sorted(subdirectroies))
        else:
            st.markdown("<div style='margin-top: 32px;'>", unsafe_allow_html=True)
            st.markdown("<font color='#FF0000'>No subdir</font>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

    with col3:
        if subdirectroies:
            st.markdown("<div class='nav-button-container'>", unsafe_allow_html=True)
            if st.button("➡️") and "path" in st.session_state:
                st.session_state.path = Path(st.session_state.path, st.session_state.new_dir)
                st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

    return st.session_state.path


def plot_airfoil_2d(x_coords, y_coords, title="Airfoil Profile"):
    """
    Plot 2D airfoil coordinates using plotly.

    Args:
        x_coords: Array or list of X coordinates
        y_coords: Array or list of Y coordinates
        title: Plot title
    """
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=x_coords,
        y=y_coords,
        mode='lines+markers',
        line=dict(color='blue', width=2),
        marker=dict(size=3, color='blue'),
        fill='toself',
        fillcolor='rgba(0, 100, 200, 0.2)',
        name='Airfoil'
    ))

    fig.update_layout(
        title=title,
        xaxis_title="x/c",
        yaxis_title="y/c",
        width=900,
        height=500,
        showlegend=False,
        yaxis=dict(scaleanchor="x", scaleratio=1),
        margin=dict(l=50, r=50, t=50, b=50),
        hovermode='closest'
    )

    st.plotly_chart(fig, width='stretch')


def section_3D_view(
    cpacs: CPACS | None = None,
    *,
    force_regenerate: bool = False,
    height: int | None = None,
) -> None:
    """
    Shows a 3D view of the aircraft by exporting a STL file.
    """

    if cpacs is None:
        cpacs = st.session_state.get("cpacs", None)

    if cpacs is None:
        return None

    # 3D mode - generate STL preview
    stl_file = Path(st.session_state.workflow.working_dir, "aircraft.stl")
    if not force_regenerate and stl_file.exists():
        pass
    elif hasattr(cpacs, "aircraft") and hasattr(
        cpacs.aircraft, "tigl"
    ):
        with st.spinner("Meshing geometry (STL export)..."):
            cpacs.aircraft.tigl.exportMeshedGeometrySTL(str(stl_file), 0.01)
    else:
        st.error("Cannot generate 3D preview (missing TIGL geometry handle).")
        return None

    your_mesh = mesh.Mesh.from_file(stl_file)
    triangles = your_mesh.vectors.reshape(-1, 3)
    vertices, indices = np.unique(triangles, axis=0, return_inverse=True)
    i, j, k = indices[0::3], indices[1::3], indices[2::3]
    x, y, z = vertices.T

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

    fig = go.Figure(data=[go.Mesh3d(x=x, y=y, z=z, i=i, j=j, k=k, color="orange", opacity=0.5)])
    fig.update_layout(
        margin=dict(l=0, r=0, t=0, b=0),
        scene=dict(
            xaxis=dict(range=x_range),
            yaxis=dict(range=y_range),
            zaxis=dict(range=z_range),
            aspectmode="cube",
        ),
    )

    if height is not None:
        fig.update_layout(height=height)

    st.plotly_chart(fig, width='stretch')
