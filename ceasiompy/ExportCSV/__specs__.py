#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from ceasiompy.utils.moduleinterfaces import CPACSInOut
from ceasiompy.utils.xpath import EXPORT_XPATH


# ===== RCE integration =====

RCE = {
    "name": "ExportCSV",
    "description": "Module to export Aeromap to CSV",
    "exec": "pwd\npython exportcsv.py",
    "author": "Aidan Jungo",
    "email": "aidan.jungo@cfse.ch",
}

# ===== CPACS inputs and outputs =====

cpacs_inout = CPACSInOut()

include_gui = False

# ----- Input -----

cpacs_inout.add_input(
    var_name='',
    var_type=list,
    default_value=None,
    descr='List of aeroMap to plot',
    xpath=EXPORT_XPATH + '/aeroMapToExport',
    gui=True,
    gui_name='__AEROMAP_CHECHBOX',
    # gui_group='Multipe aeromap'
)

# ----- Output -----
