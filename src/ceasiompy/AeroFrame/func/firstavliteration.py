"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Runs first AVL iteration.

| Author: Romain Gauthier
| Creation: 2024-06-17

"""

# ==============================================================================
#   IMPORTS
# ==============================================================================

import streamlit as st

from cpacspy.cpacsfunctions import get_value
from ceasiompy.PyAVL.pyavl import main as run_avl

from pathlib import Path
from cpacspy.cpacspy import CPACS
from unittest.mock import MagicMock
from ceasiompy.utils.guisettings import GUISettings

from ceasiompy import log
from ceasiompy.PyAVL import (
    MODULE_NAME as PYAVL_NAME,
    AVL_PLOT_XPATH,
    AVL_DISTR_XPATH,
    AVL_NCHORDWISE_XPATH,
    AVL_NSPANWISE_XPATH,
    AVL_AEROMAP_UID_XPATH,
)

# =================================================================================================
#   FUNCTIONS
# =================================================================================================


def run_first_avl_iteration(
    cpacs: CPACS,
    gui_settings: GUISettings,
    results_dir: Path,
) -> None:
    log.info("----- AVL: Calculation 1 -----")

    # You need to first load the default values of AVL
    # Then you add back the ones that you wanted to specify.
    # Run AVL analysis
    st.session_state = MagicMock()
    aeromap_uid = get_value(gui_settings.tixi, AVL_AEROMAP_UID_XPATH)
    distribution = get_value(gui_settings.tixi, AVL_DISTR_XPATH)
    nchord = str(get_value(gui_settings.tixi, AVL_NCHORDWISE_XPATH))
    nspan = str(get_value(gui_settings.tixi, AVL_NSPANWISE_XPATH))
    plot = str(get_value(gui_settings.tixi, AVL_PLOT_XPATH))

    gui_settings.update_from_specs(
        modules_list=[PYAVL_NAME],
        test=True,
    )

    # Update CPACS with the new aeromap
    gui_settings.tixi.updateTextElement(AVL_AEROMAP_UID_XPATH, aeromap_uid)
    gui_settings.tixi.updateTextElement(AVL_DISTR_XPATH, distribution)
    gui_settings.tixi.updateTextElement(AVL_NCHORDWISE_XPATH, nchord)
    gui_settings.tixi.updateTextElement(AVL_NSPANWISE_XPATH, nspan)
    gui_settings.tixi.updateTextElement(AVL_PLOT_XPATH, plot)

    gui_settings.save()

    run_avl(
        cpacs=cpacs,
        gui_settings=gui_settings,
        results_dir=results_dir,
    )
