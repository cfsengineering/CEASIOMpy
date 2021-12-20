"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed for CFS ENGINEERING, 1015 Lausanne, Switzerland

Module interfaces functions to deal with CPACS input and output

Python version: >=3.6

| Author: Aaron Dettmann
| Creation: 2019-08-26
| Last modifiction: 2019-08-26
"""

import importlib
import json
import os
import tempfile

from ceasiompy.utils.moduleinterfaces import get_module_list
import ceasiompy.__init__ as ceasiompy_root

TMPDIR_PREFIX = "CEASIOMpy_"

RCE_CONF_FILE_NAME = "configuration.json"
RCE_GROUP_NAME = "CEASIOMpy"
RCE_CPACS_IN_VAR = "cpacs_in"
RCE_CPACS_OUT_VAR = "cpacs_out"
RCE_PRESCRIPT = 'shutil.copy("${in:cpacs_in}", "${dir:tool}/ToolInput/ToolInput.xml")'
RCE_POSTSCRIPT = '${out:cpacs_out}="${dir:tool}/ToolOutput/ToolOutput.xml"'

# RCE template configuration dictionary
RCE_CONF_DICT = {
    "commandScriptLinux": None,
    "commandScriptWindows": "",
    "copyToolBehavior": "never",
    "deleteWorkingDirectoriesAfterWorkflowExecution": True,
    "documentationFilePath": "",
    "enableCommandScriptLinux": True,
    "enableCommandScriptWindows": False,
    "groupName": RCE_GROUP_NAME,
    "imitationScript": "",
    "imitationToolOutputFilename": "",
    "integrationType": "common",
    "isActive": True,
    "postScript": RCE_POSTSCRIPT,
    "preScript": RCE_PRESCRIPT,
    "setToolDirAsWorkingDir": True,
    "toolDescription": "Add Skin Friction coefficient to Euler calculations",
    "toolIconPath": "",
    "toolIntegrationVersion": 1,
    "toolIntegratorE-Mail": None,
    "toolIntegratorName": None,
    "toolName": None,
    "toolProperties": {"Default": {}},
    "uploadIcon": True,
    "inputs": [
        {
            "inputHandling": "Single",
            "endpointFileName": "",
            "endpointDataType": "FileReference",
            "defaultInputExecutionConstraint": "Required",
            "endpointName": RCE_CPACS_IN_VAR,
            "defaultInputHandling": "Single",
            "inputExecutionConstraint": "Required",
            "endpointFolder": "Input folder",
        }
    ],
    "launchSettings": [
        {
            "limitInstallationInstancesNumber": "10",
            "limitInstallationInstances": "True",
            "rootWorkingDirectory": None,
            "host": "RCE",
            "toolDirectory": None,
            "version": "3.0",
        }
    ],
    "outputs": [
        {
            "inputHandling": "-",
            "endpointFileName": "",
            "endpointDataType": "FileReference",
            "endpointName": RCE_CPACS_OUT_VAR,
            "inputExecutionConstraint": "-",
            "endpointFolder": "",
        }
    ],
}

# 'RCE-key': ('CEASIOMpy-key', <bool, is data required?>, <type, expected type>)
MAPPINGS = {
    "commandScriptLinux": ("exec", True, str),
    "toolName": ("name", True, str),
    "toolDescription": ("description", False, str),
    "toolIntegratorName": ("author", False, str),
    "toolIntegratorE-Mail": ("email", False, str),
}


def create_integration_files():
    """Create RCE configuration files (one for each CEASIOMpy module)

    Notes:
        * RCE configuration will be created in a temporary directory
        * We use the CEASIOMpy library as working and tool directory
    """

    tmp_dir = tempfile.mkdtemp(prefix=TMPDIR_PREFIX)
    ceasiompy_root_dir = os.path.dirname(ceasiompy_root.__file__)

    # Iterate through the CEASIOMpy modules
    for module_name in get_module_list():
        try:
            specs = importlib.import_module(module_name + ".__specs__")
            module_conf = specs.RCE
        except:
            print(f"--> RCE configuration NOT found for '{module_name}'")
            continue

        # Create the configuration file for the current CEASIOMpy submodule
        rce_conf = RCE_CONF_DICT
        for rce_key, (ceasiom_key, data_is_required, dtype) in MAPPINGS.items():
            data = module_conf.get(ceasiom_key, None)

            if data is None and data_is_required:
                raise ValueError(f"Data for key '{ceasiom_key}' required but not found")

            if not isinstance(data, dtype):
                raise TypeError(
                    f"Data for key '{ceasiom_key}' has wrong type:\n"
                    f"Expected '{dtype}', got '{type(data)}'"
                )

            rce_conf[rce_key] = data

        # Set other values
        submodule_name = module_name.split(".")[1]
        working_dir = os.path.join(ceasiompy_root_dir, submodule_name)
        print("Current working directory value : ", working_dir, "\n")
        rce_conf["launchSettings"][0]["rootWorkingDirectory"] = working_dir
        rce_conf["launchSettings"][0]["toolDirectory"] = working_dir

        # Write the JSON config file
        print(f"Writing RCE config for '{module_name}'")
        module_dir = os.path.join(tmp_dir, submodule_name)
        conf_file_name = os.path.join(module_dir, RCE_CONF_FILE_NAME)
        os.makedirs(module_dir)
        with open(conf_file_name, "w") as fp:
            json.dump(rce_conf, fp, indent=4, separators=(",", ":"))

    print(f"\nCreated temporary directory '{tmp_dir}'")

    # TODO:
    # * Copy configuration files to correct RCE locations
    # * Remove temp dir
    #   shutil.rmtree(tmpdir)


if __name__ == "__main__":
    create_integration_files()
