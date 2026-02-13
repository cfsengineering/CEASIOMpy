"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed for CFS ENGINEERING, 1015 Lausanne, Switzerland

Streamlit Tabs per module function.
"""

# Imports

import warnings
import importlib

import numpy as np
import pandas as pd
import streamlit as st

from ceasiompy.utils.guiobjects import update_value

from typing import Callable
from types import ModuleType
from pandas import DataFrame
from datetime import datetime
from smt.sampling_methods import LHS
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


# Functions

def section_edit_aeromap() -> None:
    """Aeromap Editor and Selector"""

    cpacs = _get_cpacs()
    if cpacs is None:
        return None

    _reset_aeromap_state_if_cpacs_changed(cpacs)

    with st.container(border=True):
        st.markdown("#### Selected Aeromap")
        _ensure_custom_aeromap(cpacs)

        selected_aeromap_id = _select_aeromap_id(cpacs)
        if selected_aeromap_id:
            _edit_selected_aeromap(cpacs, selected_aeromap_id)

        with st.popover(
            label="Create a new Aeromap",
            help="Create a new aeromap from different sampling methods in a selected range.",
            width="stretch",
        ):
            with st.container(
                border=True,
            ):
                st.markdown("**Sampling**")
                left_col, right_col = st.columns(
                    spec=2,
                    vertical_alignment="bottom",
                )
                with left_col:
                    sampling_method = st.radio(
                        label="Sampling Method",
                        options=["LHS", "Grid"],
                        help="Latin Hypercube Sampling (LHS) vs Grid (Regular Grid Sampling)",
                        horizontal=True,
                        label_visibility="collapsed",
                        key="aeromap_sampling_method",
                        width="stretch",
                    )
                with right_col:
                    if sampling_method == "LHS":
                        left_col, right_col = st.columns(
                            spec=2,
                            vertical_alignment="bottom",
                        )
                        with left_col:
                            nb_samples = st.number_input(
                                label="Samples",
                                help="Total number of samples created with LHS method.",
                                min_value=1,
                                value=8,
                                max_value=100,
                            )
                        with right_col:
                            random_state = st.number_input(
                                label="Seed",
                                help="Random Seed used by the LHS method.",
                                min_value=1,
                                max_value=100,
                                value=42,
                                step=1,
                            )

                    if sampling_method == "Grid":
                        nb_samples = st.number_input(
                            label="Samples per Dimension",
                            help="Samples per Dimension, i.e. total number of samples = 4^n.",
                            min_value=1,
                            value=3,
                            max_value=10,
                        )

            with st.container(
                border=True,
            ):
                st.markdown("**Ranges**")
                alt_range = st.slider(
                    label="Altitude [m]",
                    min_value=0.0,
                    max_value=50_000.0,     # Max altitude aircraft
                    value=(0.0, 1000.0),
                    step=100.0,
                )
                mach_range = st.slider(
                    label="Mach [Ma]",
                    min_value=0.1,
                    max_value=25.0,
                    value=(0.1, 1.0),       # Keep small for low-fidelity solvers
                    step=0.1,
                )
                aoa_range = st.slider(
                    label="α° [deg]",
                    min_value=-10.0,
                    max_value=20.0,
                    value=(-2.0, 10.0),
                    step=0.5,
                )
                aos_range = st.slider(
                    label="β° [deg]",
                    min_value=0.0,
                    max_value=25.0,         # Assume symmetry around x-z
                    value=(0.0, 10.0),
                    step=0.5,
                )

            submit_create = st.button(
                label="Create Aeromap",
                width="stretch",
                key="create_aeromap_button",
            )

            if submit_create:
                date_time = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
                base_uid = f"created_{date_time}"
                aeromap_uid = base_uid
                suffix = 1
                while True:
                    try:
                        cpacs.get_aeromap_by_uid(aeromap_uid)
                    except ValueError:
                        break
                    aeromap_uid = f"{base_uid}_{suffix}"
                    suffix += 1
                log.info(f"Clicked on create an aeromap button: {aeromap_uid}")
                created_aeromap = cpacs.create_aeromap(aeromap_uid)

                ranges = {
                    "altitude": alt_range,
                    "machNumber": mach_range,
                    "angleOfAttack": aoa_range,
                    "angleOfSideslip": aos_range,
                }

                if sampling_method == "LHS":
                    n_samples = int(nb_samples)
                    log.info(f"Generating LHS sampling for {n_samples=}")
                    xlimits = np.stack(
                        arrays=[
                            [ranges[param][0] for param in PARAMS],
                            [ranges[param][1] for param in PARAMS],
                        ],
                        axis=1,
                    ).astype(float)
                    sampling = LHS(
                        xlimits=xlimits,
                        criterion="ese",
                        random_state=random_state,
                    )
                    samples = sampling(n_samples)
                else:
                    n_per_dim = int(nb_samples)
                    grid_axes = [
                        np.linspace(
                            ranges[param][0],
                            ranges[param][1],
                            n_per_dim,
                            dtype=float,
                        )
                        for param in PARAMS
                    ]
                    mesh = np.meshgrid(*grid_axes, indexing="ij")
                    samples = np.stack(mesh, axis=-1).reshape(-1, len(PARAMS))

                aeromap_df = (
                    DataFrame(samples, columns=PARAMS)
                    .drop_duplicates(subset=PARAMS)
                    .reset_index(drop=True)
                )
                created_aeromap.df = aeromap_df
                created_aeromap.save()
                update_value(
                    tixi=cpacs.tixi,
                    xpath=SELECTED_AEROMAP_XPATH,
                    value=aeromap_uid,
                )
                aeromap_cache = st.session_state.get("aeromap_df_by_uid", {})
                aeromap_cache[aeromap_uid] = aeromap_df
                st.session_state["aeromap_df_by_uid"] = aeromap_cache
                st.session_state["created_aeromap_uid"] = aeromap_uid
                st.session_state["selected_aeromap_id"] = aeromap_uid
                st.session_state["aeromap_df"] = aeromap_df
                editor_key_version = st.session_state.get("aeromap_editor_key_version", 0)
                st.session_state["aeromap_editor_key_version"] = editor_key_version + 1
                st.rerun()


def _get_cpacs() -> CPACS | None:
    cpacs: CPACS | None = st.session_state.get("cpacs", None)
    if cpacs is None:
        st.warning("No CPACS file has been selected !")
    return cpacs


def _ensure_custom_aeromap(cpacs: CPACS, custom_id: str = "custom_aeromap") -> None:
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


def _reset_aeromap_state_if_cpacs_changed(cpacs: CPACS) -> None:
    current_cpacs_key = str(cpacs.cpacs_file)
    previous_cpacs_key = st.session_state.get("aeromap_cpacs_key")

    if previous_cpacs_key == current_cpacs_key:
        return None

    for key in (
        "selected_aeromap_id",
        "selected_aeromap",
        "created_aeromap_uid",
        "last_selected_aeromap_id",
        "aeromap_df",
        "aeromap_df_by_uid",
        "aeromap_editor_key_version",
    ):
        st.session_state.pop(key, None)

    st.session_state["aeromap_cpacs_key"] = current_cpacs_key


def _select_aeromap_id(cpacs: CPACS) -> str:
    aeromap_list = cpacs.get_aeromap_uid_list()
    created_aeromap_uid = st.session_state.pop("created_aeromap_uid", None)
    if created_aeromap_uid is not None:
        if created_aeromap_uid not in aeromap_list:
            aeromap_list.append(created_aeromap_uid)
        st.session_state["selected_aeromap_id"] = created_aeromap_uid
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
    update_value(
        tixi=cpacs.tixi,
        xpath=SELECTED_AEROMAP_XPATH,
        value=selected_aeromap_id,
    )
    st.session_state["selected_aeromap_id"] = selected_aeromap_id
    return selected_aeromap_id


def _edit_selected_aeromap(cpacs: CPACS, selected_aeromap_id: str) -> None:
    selected_aeromap = _load_selected_aeromap(cpacs, selected_aeromap_id)
    if selected_aeromap is None:
        return None

    last_selected = st.session_state.get("last_selected_aeromap_id")
    if last_selected != selected_aeromap_id:
        aeromap_cache = st.session_state.get("aeromap_df_by_uid", {})
        if selected_aeromap_id in aeromap_cache:
            st.session_state["aeromap_df"] = aeromap_cache[selected_aeromap_id]
        else:
            st.session_state["aeromap_df"] = selected_aeromap.df[PARAMS].reset_index(drop=True)
        editor_key_version = st.session_state.get("aeromap_editor_key_version", 0)
        st.session_state["aeromap_editor_key_version"] = editor_key_version + 1
        st.session_state["last_selected_aeromap_id"] = selected_aeromap_id

    original_df = selected_aeromap.df[PARAMS].reset_index(drop=True)
    edited_aero_df = _render_aeromap_editor(original_df)
    cleaned_aero_df, invalid_numeric = _normalize_aeromap_df(edited_aero_df)
    if not invalid_numeric:
        _maybe_rerun_editor(edited_aero_df, cleaned_aero_df)
    _maybe_save_aeromap(selected_aeromap, cleaned_aero_df, original_df)


def _load_selected_aeromap(cpacs: CPACS, selected_aeromap_id: str) -> AeroMap | None:
    try:
        selected_aeromap = cpacs.get_aeromap_by_uid(selected_aeromap_id)
    except ValueError:
        st.warning(f"{selected_aeromap_id=} is not a valid aeromap ID.")
        return None

    if not isinstance(selected_aeromap, AeroMap):
        st.warning(f"{selected_aeromap=} is not an AeroMap due to {selected_aeromap_id=}")
        return None

    return selected_aeromap


def _render_aeromap_editor(original_df: pd.DataFrame) -> pd.DataFrame:
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
        return st.data_editor(
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


def _normalize_aeromap_df(edited_aero_df: pd.DataFrame) -> tuple[pd.DataFrame, bool]:
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

    return cleaned_aero_df, invalid_numeric


def _maybe_rerun_editor(edited_aero_df: pd.DataFrame, cleaned_aero_df: pd.DataFrame) -> None:
    if cleaned_aero_df.equals(edited_aero_df):
        return None

    editor_key_version = st.session_state.get("aeromap_editor_key_version", 0)
    # Force the data editor to re-mount with the cleaned data.
    st.session_state["aeromap_editor_key_version"] = editor_key_version + 1
    st.rerun()


def _maybe_save_aeromap(
    selected_aeromap: AeroMap,
    cleaned_aero_df: pd.DataFrame,
    original_df: pd.DataFrame,
) -> None:
    active_rows = cleaned_aero_df[PARAMS].notna().any(axis=1)
    active_df = cleaned_aero_df.loc[active_rows, PARAMS]
    if active_df.isna().any().any():
        return None

    # Only save when its Valid Numeric
    cleaned_df = active_df[PARAMS].reset_index(drop=True)
    if cleaned_df.equals(original_df):
        return None

    selected_aeromap.df = cleaned_df
    try:
        selected_aeromap.save()
        aeromap_cache = st.session_state.get("aeromap_df_by_uid", {})
        aeromap_cache[selected_aeromap.uid] = cleaned_df
        st.session_state["aeromap_df_by_uid"] = aeromap_cache
    except Tixi3Exception as exc:
        if exc.code == ReturnCode.ALREADY_SAVED and selected_aeromap.xpath:
            for param in PARAMS:
                param_xpath = f"{selected_aeromap.xpath}/{param}"
                if selected_aeromap.tixi.checkElement(param_xpath):
                    selected_aeromap.tixi.removeElement(param_xpath)
            selected_aeromap.save()
        else:
            raise


def checks(session_state, tabs) -> None:
    if "tabs" not in session_state:
        session_state["tabs"] = []

    if "workflow_modules" in session_state and session_state.workflow_modules:
        session_state.tabs = tabs(session_state.workflow_modules)


def add_module_tab() -> None:
    # Show aeromap section for both 2D and 3D modes
    section_edit_aeromap()

    checks(st.session_state, st.tabs)

    # Load each module iteratively
    for _, (tab, module) in enumerate(
        zip(st.session_state.tabs, st.session_state.workflow_modules)
    ):
        with tab:
            get_settings_of(module)


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
