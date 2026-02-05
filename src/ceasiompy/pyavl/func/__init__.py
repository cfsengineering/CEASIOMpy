"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Initialization for PyAVL.func functions.

| Author: Leon Deligny
| Creation: 18-Mar-2025

"""

# Constants

# config.py
FORCE_FILES = ["ft", "fn", "fs", "fe", "st", "sb"]

# results.py
AVL_COEFS = {
    "CLtot": (1, "cl"),
    "CDtot": (1, "cd"),
    "CYtot": (1, "cs"),
    "Cltot": (2, "cmd"),
    "Cmtot": (2, "cms"),
    "Cntot": (2, "cml"),
    "Cma": (1, "cms_a"),
    "Clb": (2, "cmd_b"),
    "Cnb": (2, "cml_b"),
}
