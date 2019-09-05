"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

This is a wrapper module for PyTornado. PyTornado allows to perform aerodynamic
analyses using the vortex-lattice method (VLM). Note that PyTornado is being
developed in a separate repository on Github. For installation guides and
general documentation refer to:

* https://github.com/airinnova/pytornado

Please report any issues with PyTornado or this wrapper here:

* https://github.com/airinnova/pytornado/issues

PyTornado support:

* AeroperformanceMap analyses

Python version: >=3.6

| Author: Aaron Dettmann
| Creation: 2019-08-12
| Last modifiction: 2019-08-23
"""

import os
import shutil
from importlib import import_module
import json
from functools import partial
from pathlib import Path

from ceasiompy.utils.ceasiomlogger import get_logger
from ceasiompy.utils.moduleinterfaces import check_cpacs_input_requirements
from ceasiompy.ModuleTemplate.__specs__ import cpacs_inout

log = get_logger(__file__.split('.')[0])
dump_pretty_json = partial(json.dump, indent=4, separators=(',', ': '))

# ===== Paths =====
DIR_MODULE = os.path.dirname(os.path.abspath(__file__))
DIR_PYT_WKDIR = os.path.join(DIR_MODULE, 'wkdir')
DIR_PYT_AIRCRAFT = os.path.join(DIR_PYT_WKDIR, 'aircraft')
DIR_PYT_SETTINGS = os.path.join(DIR_PYT_WKDIR, 'settings')
FILE_PYT_AIRCRAFT = os.path.join(DIR_PYT_AIRCRAFT, 'ToolInput.xml')
FILE_PYT_SETTINGS = os.path.join(DIR_PYT_SETTINGS, 'cpacs_run.json')

# ===== DEFAULT SETTINGS =====
DEFAULT_SETTINGS = {
    "aircraft": "ToolInput.xml",
    "state": "__CPACS",
    "deformation": None,
    "vlm_autopanels_c": 5,
    "vlm_autopanels_s": 20,
    "save_results": {
        "global": True,
        "panelwise": True,
        "aeroperformance": True
    },
    "plot": {
        "geometry": {
            "opt": [],
            "show": False,
            "save": True
        },
        "lattice": {
            "opt": [],
            "show": False,
            "save": False
        },
        "matrix_downwash": {
            "opt": [],
            "show": False,
            "save": False
        },
        "results": {
            "opt": ["cp"],
            "show": False,
            "save": False
        }
    }
}


def fetch_settings_from_CPACS(cpacs_in_path):
    """
    Try to fetch settings from CPACS

    Args:
        :cpacs_in_path: CPACS file path

    Returns:
        * CPACS settings dictionary if settings in CPACS, otherwise None
    """

    # TODO
    return None


def main():
    log.info("Running PyTornado...")

    try:
        pytornado = import_module('pytornado.stdfun.run')
    except ModuleNotFoundError:
        err_msg = """\n
        | PyTornado was not found. CEASIOMpy cannot run an analysis.
        | Make sure that PyTornado is correctly installed. Please refer to:
        |
        | * https://github.com/airinnova/pytornado
        """
        log.error(err_msg)
        raise ModuleNotFoundError(err_msg)

    # ===== Make dirs =====
    Path(DIR_PYT_WKDIR).mkdir(parents=True, exist_ok=True)
    Path(DIR_PYT_AIRCRAFT).mkdir(parents=True, exist_ok=True)
    Path(DIR_PYT_SETTINGS).mkdir(parents=True, exist_ok=True)

    # ===== Setup =====
    # check_cpacs_input_requirements(cpacs_path, cpacs_inout, __file__)
    cpacs_in_path = DIR_MODULE + '/ToolInput/ToolInput.xml'
    cpacs_out_path = DIR_MODULE + '/ToolOutput/ToolOutput.xml'
    shutil.copy(src=cpacs_in_path, dst=FILE_PYT_AIRCRAFT)

    # ===== Get/update PyTornado settings =====
    cpacs_settings = fetch_settings_from_CPACS(cpacs_in_path)
    if cpacs_settings is not None:
        with open(FILE_PYT_SETTINGS, "w") as fp:
            dump_pretty_json(cpacs_settings, fp)

    if not os.path.exists(FILE_PYT_SETTINGS):
        with open(FILE_PYT_SETTINGS, "w") as fp:
            dump_pretty_json(DEFAULT_SETTINGS, fp)

    # ===== PyTornado analysis =====
    pytornado.standard_run(args=pytornado.StdRunArgs(run=FILE_PYT_SETTINGS,verbose=True))

    # ===== Clean up =====
    shutil.copy(src=FILE_PYT_AIRCRAFT, dst=cpacs_out_path)
    log.info("PyTornado analysis completed")


if __name__ == '__main__':
    main()
