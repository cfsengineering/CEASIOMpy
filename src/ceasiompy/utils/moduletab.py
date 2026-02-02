"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed for CFS ENGINEERING, 1015 Lausanne, Switzerland

Streamlit Tabs per module function.
"""

# Imports

import warnings
import importlib
import pandas as pd
import streamlit as st

from ceasiompy.utils.guiobjects import add_value

from typing import Callable
from types import ModuleType
from cpacspy.cpacspy import (
    CPACS,
    AeroMap,
)
from tixi3.tixi3wrapper import (
    ReturnCode,
    Tixi3Exception,
)

from ceasiompy import log
from cpacspy.utils import PARAMS
from ceasiompy.utils.commonxpaths import SELECTED_AEROMAP_XPATH

# ==============================================================================
#   FUNCTIONS
# ==============================================================================


def section_edit_aeromap() -> None:
    """Aeromap Editor and Selector"""

    cpacs: CPACS | None = st.session_state.get("cpacs", None)
    if cpacs is None:
        st.warning("No CPACS file has been selected !")
        return None

    with st.container(border=True):
        st.markdown("#### Selected Aeromap")

        # Create Custom Aeromap
        custom_id = "custom_aeromap"

        try:
            cpacs.get_aeromap_by_uid(custom_id)
        except ValueError:
            custom_aeromap = cpacs.create_aeromap(custom_id)
            custom_aeromap.add_row(
                alt=0.0,
                mach=0.3,
                aos=0.0,
                aoa=3.0,
            )
            custom_aeromap.save()
        except Exception as e:
            raise Exception(f"{cpacs.cpacs_file=} {custom_id=} {e=}")

        aeromap_list = cpacs.get_aeromap_uid_list()
        cached_aeromap_id = st.session_state.get("selected_aeromap_id", None)
        if cached_aeromap_id is not None and cached_aeromap_id in aeromap_list:
            initial_index = aeromap_list.index(cached_aeromap_id)
        else:
            initial_index = len(aeromap_list) - 1  # custom_aeromap id by default

        selected_aeromap_id = st.selectbox(
            "**Selected Aeromap**",
            aeromap_list,
            index=initial_index,
            help="Choose an aeromap",
            label_visibility="collapsed",
            accept_new_options=True,
            key="selected_aeromap",
        )
        add_value(
            tixi=cpacs.tixi,
            xpath=SELECTED_AEROMAP_XPATH,
            value=selected_aeromap_id,
        )

        st.session_state["selected_aeromap_id"] = selected_aeromap_id

        if selected_aeromap_id:
            try:
                selected_aeromap = cpacs.get_aeromap_by_uid(selected_aeromap_id)
            except ValueError:
                st.warning(f"{selected_aeromap_id=} is not a valid aeromap ID.")
                return None

            if not isinstance(selected_aeromap, AeroMap):
                st.warning(f"{selected_aeromap=} is not an AeroMap due to {selected_aeromap_id=}")
                return None

            selected_df = selected_aeromap.df[PARAMS]
            original_df = selected_df.reset_index(drop=True)

            editor_key_version = st.session_state.get("aeromap_editor_key_version", 0)

            with warnings.catch_warnings():
                warnings.filterwarnings(
                    "ignore",
                    message=(
                        "The behavior of DataFrame concatenation with empty or "
                        "all-NA entries is deprecated."
                    ),
                    category=FutureWarning,
                )
                edited_aero_df = st.data_editor(
                    st.session_state.get("aeromap_df", original_df),
                    num_rows="dynamic",
                    hide_index=True,
                    key=f"aeromap_editor_{editor_key_version}",
                    column_config={
                        "altitude": st.column_config.NumberColumn("Altitude", min_value=0.0),
                        "machNumber": st.column_config.NumberColumn("Mach", min_value=1e-2),
                        "angleOfAttack": st.column_config.NumberColumn("α°"),
                        "angleOfSideslip": st.column_config.NumberColumn("β°"),
                    },
                    column_order=["altitude", "machNumber", "angleOfAttack", "angleOfSideslip"],
                )

            edited_aero_df[PARAMS] = edited_aero_df[PARAMS].apply(
                pd.to_numeric,
                errors="coerce",
            )
            edited_aero_df[PARAMS] = edited_aero_df[PARAMS].astype(float)
            cleaned_aero_df = edited_aero_df.drop_duplicates(subset=PARAMS, keep="first")

            invalid_numeric = edited_aero_df.isna().any().any()
            if not invalid_numeric:
                cleaned_aero_df = cleaned_aero_df.reset_index(drop=True)
                st.session_state["aeromap_df"] = cleaned_aero_df

            if not invalid_numeric and not cleaned_aero_df.equals(edited_aero_df):
                # Force the data editor to re-mount with the cleaned data.
                st.session_state["aeromap_editor_key_version"] = editor_key_version + 1
                st.rerun()

            active_rows = cleaned_aero_df[PARAMS].notna().any(axis=1)
            active_df = cleaned_aero_df.loc[active_rows, PARAMS]
            invalid_numeric = active_df.isna().any().any()

            if not invalid_numeric:
                # Only save when its Valid Numeric
                cleaned_df = active_df[PARAMS].reset_index(drop=True)
                if not cleaned_df.equals(original_df):
                    selected_aeromap.df = cleaned_df
                    try:
                        selected_aeromap.save()
                    except Tixi3Exception as exc:
                        if exc.code == ReturnCode.ALREADY_SAVED and selected_aeromap.xpath:
                            for param in PARAMS:
                                param_xpath = f"{selected_aeromap.xpath}/{param}"
                                if selected_aeromap.tixi.checkElement(param_xpath):
                                    selected_aeromap.tixi.removeElement(param_xpath)
                            selected_aeromap.save()
                        else:
                            raise

        st.markdown("#### Import aeromap from CSV or Excel")

        uploaded_csv = st.file_uploader(
            label="Upload a AeroMap file",
            label_visibility="collapsed",
            type=["csv", "xlsx", "xls"],
        )
        if not uploaded_csv:
            st.session_state.pop("last_imported_aeromap_uid", None)
            return None

        uploaded_aeromap_uid = uploaded_csv.name.rsplit(".", 1)[0]
        if st.session_state.get("last_imported_aeromap_uid") == uploaded_aeromap_uid:
            return None

        if uploaded_aeromap_uid in cpacs.get_aeromap_uid_list():
            st.info("Existing aeromap found; overwriting it with the uploaded file.")
            cpacs.delete_aeromap(uploaded_aeromap_uid)

        new_aeromap = cpacs.create_aeromap(uploaded_aeromap_uid)
        if uploaded_csv.name.lower().endswith((".xlsx", ".xls")):
            import_df = pd.read_excel(uploaded_csv, keep_default_na=False)
        else:
            import_df = pd.read_csv(uploaded_csv, keep_default_na=False)

        new_aeromap.df = import_df
        log.info(f"Saving AeroMap ID: {uploaded_aeromap_uid} in CPACS file.")
        new_aeromap.save()
        st.session_state["last_imported_aeromap_uid"] = uploaded_aeromap_uid
        st.rerun()


def checks(session_state, tabs) -> None:
    if "tabs" not in session_state:
        session_state["tabs"] = []

    if "workflow_modules" in session_state and session_state.workflow_modules:
        session_state.tabs = tabs(session_state.workflow_modules)


def add_module_tab(new_file: bool) -> None:
    # Show aeromap section for both 2D and 3D modes
    section_edit_aeromap()

    checks(st.session_state, st.tabs)

    # Load each module iteratively
    for _, (tab, module) in enumerate(
        zip(st.session_state.tabs, st.session_state.workflow_modules)
    ):
        with tab:
            get_settings_of(module_name=module)


def get_settings_of(module_name: str) -> None:
    """Return gui_settings callable from ceasiompy.<module_name>.__specs__ if present."""
    try:
        specs: ModuleType = importlib.import_module(f"ceasiompy.{module_name}.__specs__")
    except ModuleNotFoundError as e:
        raise ModuleNotFoundError(f"Could not import module {module_name=} {e=}")

    if not hasattr(specs, "gui_settings"):
        raise TypeError(f"gui_settings of {module_name=} not found.")

    gui_settings = specs.gui_settings
    if not isinstance(specs.gui_settings, Callable):
        raise TypeError(f"specs.gui_settings of {module_name=} is not Callable.")

    gui_settings(st.session_state.cpacs)
    return None


def process_unit(name: str, unit: str) -> None:
    # TODO: Add constants in __init__ ?
    if unit not in ["[]", "[1]", None]:
        name = f"{name} {unit}"
