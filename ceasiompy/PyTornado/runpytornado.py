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


# ===== CPACS paths (specific for CEASIOMpy) =====
class XPATHS:
    TOOLSPEC = '/cpacs/toolspecific/pytornado'

    # TODO


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


def get_pytornado_default_settings():
    """
    TODO
    """

    ps = import_pytornado('pytornado.objects.settings')
    default_dict = ps.get_default_dict(ps.DEFAULT_SETTINGS)

    default_dict["aircraft"] = "ToolInput.xml"
    default_dict["state"] = "__CPACS"
    default_dict['plot']['results']['show'] = False
    default_dict['plot']['geometry']['save'] = True

    return default_dict


def import_pytornado(module_name):
    """
    Try to import PyTornado and return module if succesful

    Args:
        module: Name of the module

    Raises:
        ModuleNotFoundError: If PyTornado not found
    """

    try:
        module_name = import_module(module_name)
    except ModuleNotFoundError:
        err_msg = """\n
        | PyTornado was not found. CEASIOMpy cannot run an analysis.
        | Make sure that PyTornado is correctly installed. Please refer to:
        |
        | * https://github.com/airinnova/pytornado
        """
        log.error(err_msg)
        raise ModuleNotFoundError(err_msg)

    return module_name


def main():
    log.info("Running PyTornado...")

    # ===== Import PyTornado =====
    pytornado = import_pytornado('pytornado.stdfun.run')

    # ===== Make directories =====
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
            cpacs_settings = get_pytornado_default_settings()
            dump_pretty_json(cpacs_settings, fp)

    # ===== PyTornado analysis =====
    pytornado.standard_run(args=pytornado.StdRunArgs(run=FILE_PYT_SETTINGS,verbose=True))

    # ===== Clean up =====
    shutil.copy(src=FILE_PYT_AIRCRAFT, dst=cpacs_out_path)
    log.info("PyTornado analysis completed")


if __name__ == '__main__':
    main()
