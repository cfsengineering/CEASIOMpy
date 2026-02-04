"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed for CFS ENGINEERING, 1015 Lausanne, Switzerland

Streamlit page to create a CEASIOMpy workflow.
"""

# Imports

import streamlit as st

from streamlit_flow import streamlit_flow
from streamlitutils import create_sidebar
from ceasiompy.utils.moduleinterfaces import (
    get_module_list,
    get_init_for_module,
)

from streamlit_flow import (
    StreamlitFlowEdge,
    StreamlitFlowNode,
    StreamlitFlowState,
)

from constants import BLOCK_CONTAINER
from ceasiompy.PyAVL import MODULE_NAME as PYAVL
from ceasiompy.SU2Run import MODULE_NAME as SU2RUN
from ceasiompy.SMTrain import MODULE_NAME as SMTRAIN
from ceasiompy.CPACS2GMSH import MODULE_NAME as CPACS2GMSH
from ceasiompy.StaticStability import MODULE_NAME as STATICSTABILITY


# Constants

PAGE_NAME = "Workflow"

HOW_TO_TEXT = (
    "### Create a workflow \n"
    "1. Select a predefined workflow and modify it \n"
    "1. Or Build from scratch\n"
    "1. Go to the *Settings*\n"
)


# Functions


def section_predefined_workflow() -> None:
    """
    Where to define the Pre-defined workflows.
    """

    st.markdown("#### Predefined Workflows")

    active_modules = set(get_module_list(only_active=True))

    predefine_workflows = [
        [SMTRAIN],
        [PYAVL, STATICSTABILITY],
        [CPACS2GMSH, SU2RUN],
    ]

    for workflow in predefine_workflows:
        available = all(module in active_modules for module in workflow)

        button_label = " → ".join(workflow)
        button_key = f"predefined_workflow_{button_label}"

        if st.button(button_label, key=button_key, disabled=not available):
            st.session_state.workflow_modules = workflow
            st.session_state.pop("workflow_flow_state", None)
            st.session_state.pop("workflow_flow_modules", None)
            st.rerun()


def section_add_module() -> None:
    """
    Where to select the workflow.
    """

    st.markdown("#### Add Modules to your Workflow")

    if "workflow_modules" not in st.session_state:
        st.session_state["workflow_modules"] = []

    module_list = get_module_list(only_active=True)
    module_type_order = {
        "PreProcessing": 0,
        "Mesher": 1,
        "Solver": 2,
        "PostProcessing": 3,
        "MetaModule": 4,
    }
    module_type_icon = {
        "PreProcessing": "Pre",
        "Mesher": "Mesh",
        "Solver": "CFD",
        "PostProcessing": "Post",
        "MetaModule": "Meta",
        "Other": "NA",
    }

    if not module_list:
        st.warning("No modules available...")
        return None

    module_type_map = {}
    for module_name in module_list:
        init = get_init_for_module(module_name, raise_error=False)
        module_type = getattr(init, "MODULE_TYPE", "Other")
        module_type_map[module_name] = module_type

    available_module_list = sorted(
        module_list,
        key=lambda name: (
            module_type_order.get(module_type_map.get(name, "Other"), 99),
            module_type_map.get(name, "Other"),
            name,
        ),
    )
    available_module_set = set(available_module_list)
    selected_modules = set(st.session_state.get("workflow_modules", []))
    selectable_module_list = [
        name for name in available_module_list if name not in selected_modules
    ]

    def insert_module_in_workflow(modules, new_module):
        return normalize_workflow_modules(modules + [new_module])

    def normalize_workflow_modules(modules):
        grouped = {}
        for name in modules:
            module_type = module_type_map.get(name, "Other")
            grouped.setdefault(module_type, [])
            if name not in grouped[module_type]:
                grouped[module_type].append(name)

        ordered = []
        for module_type, _ in sorted(
            module_type_order.items(), key=lambda item: item[1]
        ):
            ordered.extend(grouped.pop(module_type, []))
        for module_type in sorted(grouped.keys()):
            ordered.extend(grouped[module_type])
        return ordered

    left_col, right_col = st.columns([0.5, 0.5])

    with left_col:
        col_add_label, col_add_button = st.columns([0.4, 0.2])

        with col_add_label:
            def format_module_label(name: str) -> str:
                module_type = module_type_map.get(name, "Other")
                icon = module_type_icon.get(module_type, module_type_icon["Other"])
                return f"{icon} · {name}"

            if selectable_module_list:
                module = st.selectbox(
                    "Module to add to the workflow:",
                    selectable_module_list,
                    format_func=format_module_label,
                )
            else:
                st.markdown("<div style='margin-top: 20px;'></div>", unsafe_allow_html=True)
                st.info("No more modules.")
                module = None

        with col_add_button:
            # Add vertical spacing to match the label height of selectbox
            st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)
            if st.button(
                "Add",
                width="stretch",
                help="Add this module to the workflow",
                disabled=module is None,
            ):
                if module is not None:
                    st.session_state.workflow_modules = insert_module_in_workflow(
                        st.session_state.workflow_modules,
                        module,
                    )
                st.rerun()

    with right_col:
        col_remove_label, col_remove_button = st.columns([0.4, 0.2])
        with col_remove_label:
            module_to_remove = st.selectbox(
                "Module to remove",
                options=st.session_state.workflow_modules,
                key="workflow_remove_select",
            )
        with col_remove_button:
            # Add vertical spacing to match the label height of selectbox
            st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)
            if st.button(
                "Remove",
                help="Remove selected module",
                width="stretch",
                disabled=st.session_state.workflow_modules == [],
            ):
                st.session_state.workflow_modules = [
                    module
                    for module in st.session_state.workflow_modules
                    if module != module_to_remove
                ]
                st.rerun()

    if st.session_state.workflow_modules:
        filtered_modules = [
            module
            for module in st.session_state.workflow_modules
            if module in available_module_set
        ]
        if len(filtered_modules) != len(st.session_state.workflow_modules):
            st.session_state.workflow_modules = filtered_modules
            st.info("Some modules are no longer available and were removed from the workflow.")
    else:
        st.warning("No module(s) have been added in the workflow.")

    if st.session_state.workflow_modules:
        def build_flow_state(modules):
            nodes = []
            edges = []
            x_gap = 150
            y_gap = 100
            row_idx = 0
            col_idx = 0
            last_type = None
            for idx, module_name in enumerate(modules):
                node_id = f"module_{idx}"
                module_type = module_type_map.get(module_name, "Other")
                content_html = (
                    "<div style='position:relative; line-height:0.1;'>"
                    f"<span style='position:absolute; top:2px; right:0px; "
                    "font-size:6px; color:#7a7a7a; background:#ffffff; "
                    "padding:0 2px;'>"
                    f"{module_type}</span>"
                    f"<div>{module_name}</div>"
                    "</div>"
                )
                if last_type is not None and module_type != last_type:
                    row_idx += 1
                    col_idx = 0
                nodes.append(
                    StreamlitFlowNode(
                        id=node_id,
                        pos=(col_idx * x_gap, row_idx * y_gap),
                        data={
                            "content": content_html,
                            "module_name": module_name,
                            "module_type": module_type,
                        },
                        node_type="default",
                        source_position="right",
                        target_position="left",
                        selectable=False,
                        draggable=True,
                        connectable=False,
                        style={
                            "border": "1px solid #e6e0d6",
                            "borderRadius": "8px",
                            "padding": "6px 10px",
                            "backgroundColor": "#ffffff",
                            "color": "#1b1b1b",
                        },
                    )
                )
                col_idx += 1
                last_type = module_type
                if idx > 0:
                    edges.append(
                        StreamlitFlowEdge(
                            id=f"edge_{idx - 1}_{idx}",
                            source=f"module_{idx - 1}",
                            target=node_id,
                            edge_type="smoothstep",
                            marker_end={"type": "arrowclosed"},
                        )
                    )
            return StreamlitFlowState(nodes, edges)

        def count_rows(modules):
            if not modules:
                return 0
            row_idx = 0
            col_idx = 0
            last_type = None
            for module_name in modules:
                module_type = module_type_map.get(module_name, "Other")
                if last_type is not None and module_type != last_type:
                    row_idx += 1
                    col_idx = 0
                col_idx += 1
                last_type = module_type
            return row_idx + 1

        if (
            "workflow_flow_state" not in st.session_state
            or st.session_state.get("workflow_flow_modules")
            != st.session_state.workflow_modules
        ):
            st.session_state.workflow_flow_state = build_flow_state(
                st.session_state.workflow_modules
            )
            st.session_state.workflow_flow_modules = list(
                st.session_state.workflow_modules
            )

        rows = count_rows(st.session_state.workflow_modules)
        flow_height = max(260, 120 + rows * 170)
        flow_state = streamlit_flow(
            "workflow_flow",
            st.session_state.workflow_flow_state,
            height=flow_height,
            fit_view=True,
            show_controls=False,
            show_minimap=False,
            allow_new_edges=False,
        )
        st.session_state.workflow_flow_state = flow_state

        if flow_state.nodes:
            ordered_nodes = sorted(
                flow_state.nodes,
                key=lambda node: (node.position["x"], node.position["y"]),
            )
            ordered_modules = [
                node.data.get("module_name", node.data.get("content", ""))
                for node in ordered_nodes
            ]
            if ordered_modules != st.session_state.workflow_modules:
                normalized_modules = normalize_workflow_modules(ordered_modules)
                st.session_state.workflow_modules = normalized_modules
                st.session_state.workflow_flow_modules = list(normalized_modules)


# Main

if __name__ == "__main__":
    # Define interface
    create_sidebar(HOW_TO_TEXT)

    # Custom CSS
    st.markdown(
        """
        <style>
        """
        + BLOCK_CONTAINER
        + """
        .css-1awtkze {
            border-radius:3px;
            background-color:#ff7f2a;
            padding: 6px;
        }
        .css-1awtkze:after {
        content:'';
        position: absolute;
        top: 100%;
        left: 50%;
        margin-left: -20px;
        margin-top: 2px;
        width: 0;
        height: 0;
        border-top: solid 10px #9e9e93;
        border-left: solid 10px transparent;
        border-right: solid 10px transparent;
        }
        .stButton > button {
            border-radius:10px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.title(PAGE_NAME)

    st.markdown("---")

    section_predefined_workflow()

    st.markdown("---")

    section_add_module()

    # Add last_page
    st.session_state.last_page = PAGE_NAME
