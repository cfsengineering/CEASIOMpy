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

PyTornado supports:

* AeroperformanceMap analyses

Python version: >=3.6

| Author: Aaron Dettmann
| Creation: 2019-08-12
| Last modifiction: 2019-09-06
"""

# TODO
# -- Good to always remove wkdir?
# -- Dict parser --> Cast list/tuple

from functools import partial
from importlib import import_module
from pathlib import Path
import json
import os
import re
import shutil

import xmltodict as xml

from ceasiompy.utils.ceasiomlogger import get_logger
from ceasiompy.utils.moduleinterfaces import check_cpacs_input_requirements
from ceasiompy.ModuleTemplate.__specs__ import cpacs_inout

log = get_logger(__file__.split('.')[0])
dump_pretty_json = partial(json.dump, indent=4, separators=(',', ': '))

REGEX_INT = re.compile(r'^[-+]?[0-9]+$')
REGEX_FLOAT = re.compile(r'^[+-]?(\d+(\.\d*)?|\.\d+)([eE][+-]?\d+)?$')

# ===== Paths =====
DIR_MODULE = os.path.dirname(os.path.abspath(__file__))
DIR_PYT_WKDIR = os.path.join(DIR_MODULE, 'wkdir')
DIR_PYT_AIRCRAFT = os.path.join(DIR_PYT_WKDIR, 'aircraft')
DIR_PYT_SETTINGS = os.path.join(DIR_PYT_WKDIR, 'settings')
FILE_PYT_AIRCRAFT = os.path.join(DIR_PYT_AIRCRAFT, 'ToolInput.xml')
FILE_PYT_SETTINGS = os.path.join(DIR_PYT_SETTINGS, 'cpacs_run.json')


def import_pytornado(module_name):
    """ Try to import PyTornado and return module if succesful

    Args:
        module_name (str): Name of the module

    Returns:
        module: Loaded module

    Raises:
        ModuleNotFoundError: If PyTornado is not found
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


def get_pytornado_settings(cpacs_in_path):
    """ Return a default settings dictionary

    The default PyTornado settings will be used. Settings defined in CPACS will
    be loaded and will overwrite the PyTornado default dictionary.

    Notes:
        * We expect that the CPACS XML has the same structure as the JSON
          settings file (see PyTornado documentation). Note that the structure
          defined in XML will not be checked here. However, PyTornado will
          perform a runtime check.

    Args:
        :cpacs_in_path (str): CPACS file path

    Returns:
        :settings (dict): CPACS settings dictionary
    """

    # ----- Fetch PyTornado's default settings -----
    # Note:
    # * First, get a default settings dictionary from PyTornado
    # * The dictionary is described in the PyTornado documentation, see
    #   --> https://pytornado.readthedocs.io/en/latest/user_guide/input_file_settings.html
    ps = import_pytornado('pytornado.objects.settings')
    settings = ps.get_default_dict(ps.DEFAULT_SETTINGS)

    # ----- Modify the default dict -----
    settings["aircraft"] = "ToolInput.xml"  # Aircraft input file
    settings["state"] = "__CPACS"  # Load aeroperformance map from CPACS
    settings['plot']['results']['show'] = False
    settings['plot']['results']['save'] = False

    # ----- Try to read PyTornado settings from CPACS -----
    with open(cpacs_in_path, "r") as fp:
        cpacs_as_dict = xml.parse(fp.read())
    # Try to get the PyTornado settings
    cpacs_settings = cpacs_as_dict.get('cpacs', {}).get('toolspecific', {}).get('pytornado', None)
    if cpacs_settings is not None:

        def update_settings_from_cpacs(to_update, other_dict, key):
            """Update PyTornado settings dict with CPACS settings"""
            value = other_dict.get(key, None)
            if value is not None:
                if isinstance(value, dict):
                    to_update = to_update[key].update(value)
                else:
                    to_update[key] = value

        # Values that we read from CPACS
        update_settings_from_cpacs(settings, cpacs_settings, 'plot')
        update_settings_from_cpacs(settings, cpacs_settings, 'save_results')
        update_settings_from_cpacs(settings, cpacs_settings, 'vlm_autopanels_c')
        update_settings_from_cpacs(settings, cpacs_settings, 'vlm_autopanels_s')

        parse_pytornado_settings_dict(settings)

    return settings


def parse_pytornado_settings_dict(dictionary):
    """ Parse the PyTornado settings dict

    Note:
        * Parses dictionary recursively
        * Replaces strings 'True' or 'true' with boolean True
        * Replaces strings 'False' or 'false' with boolean False
        * Converts float-like strings to float numbers
        * Converts int-like strings to integer numbers

    Args:
        dictionary (dict): Dictionary to parse
    """

    for k, v in dictionary.items():

        # Parse dictionary recursively
        if isinstance(v, dict):
            parse_pytornado_settings_dict(v)

        # Convert strings to bool, float, int
        elif isinstance(v, str):
            if v.lower() == 'true':
                v = True
            elif v.lower() == 'false':
                v = False
            # First check integer, then float!
            elif REGEX_INT.fullmatch(v):
                v = int(v)
            elif REGEX_FLOAT.fullmatch(v):
                v = float(v)

            # TODO: list/tuple

            dictionary[k] = v

        # -----------
        # Optional settings
        # TODO: improve
        if k == 'opt':
            dictionary[k] = (v,)
        # -----------


def main():
    log.info("Running PyTornado...")

    # ===== Import PyTornado =====
    pytornado = import_pytornado('pytornado.stdfun.run')

    # ===== Clean up from previous analyses =====
    shutil.rmtree(DIR_PYT_WKDIR, ignore_errors=True)

    # ===== Make directories =====
    Path(DIR_PYT_WKDIR).mkdir(parents=True, exist_ok=True)
    Path(DIR_PYT_AIRCRAFT).mkdir(parents=True, exist_ok=True)
    Path(DIR_PYT_SETTINGS).mkdir(parents=True, exist_ok=True)

    # ===== Setup =====
    # check_cpacs_input_requirements(cpacs_path, cpacs_inout, __file__)
    cpacs_in_path = DIR_MODULE + '/ToolInput/ToolInput.xml'
    cpacs_out_path = DIR_MODULE + '/ToolOutput/ToolOutput.xml'
    shutil.copy(src=cpacs_in_path, dst=FILE_PYT_AIRCRAFT)

    # ===== Get PyTornado settings =====
    cpacs_settings = get_pytornado_settings(cpacs_in_path)
    with open(FILE_PYT_SETTINGS, "w") as fp:
        dump_pretty_json(cpacs_settings, fp)

    # ===== PyTornado analysis =====
    pytornado.standard_run(args=pytornado.StdRunArgs(run=FILE_PYT_SETTINGS, verbose=True))

    # ===== Clean up =====
    shutil.copy(src=FILE_PYT_AIRCRAFT, dst=cpacs_out_path)
    log.info("PyTornado analysis completed")


if __name__ == '__main__':
    main()
