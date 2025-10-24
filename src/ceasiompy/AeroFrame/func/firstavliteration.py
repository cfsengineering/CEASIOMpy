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

from pathlib import Path
from cpacspy.cpacspy import CPACS
from unittest.mock import MagicMock

from ceasiompy.PyAVL.pyavl import main as run_avl
from ceasiompy.utils.ceasiompyutils import update_gui_settings_from_specs
from cpacspy.cpacsfunctions import get_value

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


def run_first_avl_iteration(cpacs: CPACS, results_dir: Path) -> None:
    tixi = cpacs.tixi
    log.info("----- AVL: Calculation 1 -----")

    # You need to first load the default values of AVL
    # Then you add back the ones that you wanted to specify.
    # Run AVL analysis
    st.session_state = MagicMock()
    aeromap_uid = get_value(tixi, AVL_AEROMAP_UID_XPATH)
    distribution = get_value(tixi, AVL_DISTR_XPATH)
    nchord = str(get_value(tixi, AVL_NCHORDWISE_XPATH))
    nspan = str(get_value(tixi, AVL_NSPANWISE_XPATH))
    plot = str(get_value(tixi, AVL_PLOT_XPATH))

    update_gui_settings_from_specs(cpacs, PYAVL_NAME, test=True)

    # Update CPACS with the new aeromap
    tixi.updateTextElement(AVL_AEROMAP_UID_XPATH, aeromap_uid)
    tixi.updateTextElement(AVL_DISTR_XPATH, distribution)
    tixi.updateTextElement(AVL_NCHORDWISE_XPATH, nchord)
    tixi.updateTextElement(AVL_NSPANWISE_XPATH, nspan)
    tixi.updateTextElement(AVL_PLOT_XPATH, plot)

    run_avl(cpacs, results_dir)
