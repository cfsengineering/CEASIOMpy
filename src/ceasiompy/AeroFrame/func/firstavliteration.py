"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Runs first AVL iteration.

| Author: Romain Gauthier
| Creation: 2024-06-17

"""

# Imports

import streamlit as st

from pathlib import Path
from cpacspy.cpacspy import CPACS
from unittest.mock import MagicMock

from ceasiompy.PyAVL.pyavl import main as run_avl
from ceasiompy.utils.ceasiompyutils import update_cpacs_from_specs
from cpacspy.cpacsfunctions import get_value

from ceasiompy import log
from ceasiompy.utils.commonxpaths import SELECTED_AEROMAP_XPATH
from ceasiompy.PyAVL import (
    MODULE_NAME as PYAVL_NAME,
    AVL_DISTR_XPATH,
    AVL_NCHORDWISE_XPATH,
    AVL_NSPANWISE_XPATH,
)

# Functions

def run_first_avl_iteration(cpacs: CPACS, results_dir: Path) -> None:
    tixi = cpacs.tixi
    log.info("----- AVL: Calculation 1 -----")

    # You need to first load the default values of AVL
    # Then you add back the ones that you wanted to specify.
    # Run AVL analysis
    st.session_state = MagicMock()
    aeromap_uid = get_value(tixi, SELECTED_AEROMAP_XPATH)
    distribution = get_value(tixi, AVL_DISTR_XPATH)
    nchord = str(get_value(tixi, AVL_NCHORDWISE_XPATH))
    nspan = str(get_value(tixi, AVL_NSPANWISE_XPATH))

    update_cpacs_from_specs(cpacs, PYAVL_NAME, test=True)

    # Update CPACS with the new aeromap
    tixi.updateTextElement(SELECTED_AEROMAP_XPATH, aeromap_uid)
    tixi.updateTextElement(AVL_DISTR_XPATH, distribution)
    tixi.updateTextElement(AVL_NCHORDWISE_XPATH, nchord)
    tixi.updateTextElement(AVL_NSPANWISE_XPATH, nspan)

    run_avl(cpacs, results_dir)
