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
| Last modification: 2021-10-01


TODO:

    * Dict parser --> Cast list/tuple

"""

# ==============================================================================
#   IMPORTS
# ==============================================================================

from functools import partial
from importlib import import_module
from pathlib import Path
import json
import os
import re
import shutil
from datetime import datetime
from glob import glob
import numpy as np
import pandas as pd
import xmltodict as xml

from cpacspy.cpacsfunctions import open_tixi, get_value_or_default
import ceasiompy.utils.ceasiompyfunctions as ceaf
import ceasiompy.utils.moduleinterfaces as mi

from ceasiompy.utils.ceasiomlogger import get_logger


log = get_logger(__file__.split(".")[0])
dump_pretty_json = partial(json.dump, indent=4, separators=(",", ": "))

REGEX_INT = re.compile(r"^[-+]?[0-9]+$")
REGEX_FLOAT = re.compile(r"^[+-]?(\d+(\.\d*)?|\.\d+)([eE][+-]?\d+)?$")

DIR_MODULE = os.path.dirname(os.path.abspath(__file__))
MODULE_NAME = os.path.basename(os.getcwd())


# ==============================================================================
#   CLASSES
# ==============================================================================


# ==============================================================================
#   FUNCTIONS
# ==============================================================================


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

    ps = import_pytornado("pytornado.objects.settings")
    settings = ps.get_default_dict(ps.DEFAULT_SETTINGS)

    # ----- Modify the default dict -----
    settings["aircraft"] = "ToolInput.xml"  # Aircraft input file
    settings["state"] = "__CPACS"  # Load aeroperformance map from CPACS
    settings["plot"]["results"]["show"] = False
    settings["plot"]["results"]["save"] = False

    # ----- Try to read PyTornado settings from CPACS -----
    cpacs_settings = get_pytornado_settings_from_CPACS(cpacs_in_path)
    if cpacs_settings is not None:
        update_dict(settings, cpacs_settings)
        parse_pytornado_settings_dict(settings)
    return settings


def get_pytornado_settings_from_CPACS(cpacs_in_path):
    """ Try to read PyTornado settings from CPACS

    Note:
        * Returns None if PyTornado settings not found in CPACS

    Args:
        cpacs_in_path (str): Path to CPACS file

    Returns:
        cpacs_settings (dict): PyTornado settings dictionary read from CPACS
    """

    with open(cpacs_in_path, "r") as fp:
        cpacs_as_dict = xml.parse(fp.read())
    cpacs_settings = cpacs_as_dict.get("cpacs", {}).get("toolspecific", {}).get("pytornado", None)
    parse_pytornado_settings_dict(cpacs_settings)
    return cpacs_settings


def update_dict(to_update, other_dict):
    """Update 'to_update' dict with 'other_dict' recursively

    Note:
        * Entries from 'other_dict' are only updated if they exist in 'to_update'

    Args:
        to_update (dict): Dictionary which is to be updated
        other_dict (dict): Dictionary with new values
    """

    for key, value in other_dict.items():
        if isinstance(value, dict):
            update_dict(to_update.get(key, {}), value)
        elif to_update.get(key, None) is not None:
            to_update[key] = value


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
            if v.lower() == "true":
                v = True
            elif v.lower() == "false":
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
        # if k == 'opt':
        #     dictionary[k] = (v,)
        # -----------


def _get_load_fields(pytornado_results, dir_pyt_results):
    """
    Return load fields from PyTornado results (only extract load from last results)
    (TODO: Maybe this function could integrated to Tornado...?)
    Args:
        :pytornado_results: (obj) PyTornado results data structure
        :dir_pyt_results: (str): Path to the results dir
    Returns:
        :load_fields: (dict) AeroFrame load fields
    """

    vlmdata = pytornado_results["vlmdata"]
    lattice = pytornado_results["lattice"]

    # PyTornado API provides access to loads on main wing and on mirrored side
    bookkeeping_lists = (
        (lattice.bookkeeping_by_wing_uid, ""),
        (lattice.bookkeeping_by_wing_uid_mirror, "_m"),
    )

    frames = []

    load_fields = {}
    for (bookkeeping_list, suffix) in bookkeeping_lists:
        for wing_uid, panellist in bookkeeping_list.items():
            # Count number of panels
            num_pan = 0
            for entry in panellist:
                num_pan += len(entry.pan_idx)

            # Add a first row of zeros in order to use 'append' method (will be removed below)
            load_field = np.zeros((1, 6))
            for entry in panellist:
                # pan_idx: Panel index in PyTornado book keeping system
                for pan_idx in entry.pan_idx:
                    load_field_entry = np.zeros((1, 6))
                    # load_field_entry[0, 0:3] = self.points_of_attack_undeformed[pan_idx]
                    load_field_entry[0, 0:3] = lattice.bound_leg_midpoints[
                        pan_idx
                    ]  # TODO: correct to use this field as coordinates??
                    load_field_entry[0, 3] = vlmdata.panelwise["fx"][pan_idx]
                    load_field_entry[0, 4] = vlmdata.panelwise["fy"][pan_idx]
                    load_field_entry[0, 5] = vlmdata.panelwise["fz"][pan_idx]
                    load_field = np.append(load_field, load_field_entry, axis=0)

            # # Write one CSV file per Wing
            load_fields[wing_uid + suffix] = load_field[1:, :]
            df = pd.DataFrame(load_field[1:, :])
            df.columns = ["x", "y", "z", "fx", "fy", "fz"]
            df["wing_uid"] = wing_uid + suffix
            frames.append(df)

    # Write aircraft load in a CSV file
    df_tot = pd.concat(frames)
    csv_path = os.path.join(dir_pyt_results, "aircraft_loads.csv")
    print(csv_path)
    df_tot.to_csv(csv_path, sep=",", index=False)


def main():

    log.info("Running PyTornado...")

    # ===== CPACS inout and output paths =====
    # MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
    cpacs_in_path = mi.get_toolinput_file_path(MODULE_NAME)
    cpacs_out_path = mi.get_tooloutput_file_path(MODULE_NAME)

    # ===== Delete old working directories =====
    settings_from_CPACS = get_pytornado_settings_from_CPACS(cpacs_in_path)
    if settings_from_CPACS is not None:
        if settings_from_CPACS.get("deleteOldWKDIRs", False):
            wkdirs = glob(os.path.join(DIR_MODULE, "wkdir_*"))
            for wkdir in wkdirs:
                shutil.rmtree(wkdir, ignore_errors=True)

    # ===== Paths =====
    dir_pyt_wkdir = os.path.join(DIR_MODULE, "wkdir_temp")

    dir_pyt_aircraft = os.path.join(dir_pyt_wkdir, "aircraft")
    dir_pyt_settings = os.path.join(dir_pyt_wkdir, "settings")
    dir_pyt_results = os.path.join(dir_pyt_wkdir, "_results")
    file_pyt_aircraft = os.path.join(dir_pyt_aircraft, "ToolInput.xml")
    file_pyt_settings = os.path.join(dir_pyt_settings, "cpacs_run.json")

    # ===== Make directories =====
    Path(dir_pyt_wkdir).mkdir(parents=True, exist_ok=True)
    Path(dir_pyt_aircraft).mkdir(parents=True, exist_ok=True)
    Path(dir_pyt_settings).mkdir(parents=True, exist_ok=True)
    Path(dir_pyt_results).mkdir(parents=True, exist_ok=True)

    # ===== Setup =====
    shutil.copy(src=cpacs_in_path, dst=file_pyt_aircraft)
    mi.check_cpacs_input_requirements(cpacs_in_path)

    # ===== Get PyTornado settings =====
    cpacs_settings = get_pytornado_settings(cpacs_in_path)
    with open(file_pyt_settings, "w") as fp:
        dump_pretty_json(cpacs_settings, fp)

    # ===== PyTornado analysis =====
    pytornado = import_pytornado("pytornado.stdfun.run")
    # pytornado.standard_run(args=pytornado.StdRunArgs(run=file_pyt_settings, verbose=True))
    results = pytornado.standard_run(
        args=pytornado.StdRunArgs(run=file_pyt_settings, verbose=True)
    )

    # ===== Extract load =====
    tixi = open_tixi(cpacs_in_path)
    extract_loads_xpath = "/cpacs/toolspecific/pytornado/save_results/extractLoads"
    extract_loads = get_value_or_default(tixi, extract_loads_xpath, False)

    if extract_loads:
        _get_load_fields(results, dir_pyt_results)

    # ===== Clean up =====
    shutil.copy(src=file_pyt_aircraft, dst=cpacs_out_path)

    wkdir = ceaf.get_wkdir_or_create_new(tixi)
    dst_pyt_wkdir = os.path.join(
        wkdir, "CFD", "PyTornado", f"wkdir_{datetime.strftime(datetime.now(), '%F_%H%M%S')}"
    )
    shutil.copytree(src=dir_pyt_wkdir, dst=dst_pyt_wkdir)
    shutil.rmtree(dir_pyt_wkdir, ignore_errors=True)

    log.info("PyTornado analysis completed")


# ==============================================================================
#    MAIN
# ==============================================================================

if __name__ == "__main__":

    main()
