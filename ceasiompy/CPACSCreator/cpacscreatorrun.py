"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

CPACS Creator python launcher

Python version: >=3.8

| Author : Aidan Jungo
| Creation: 2018-10-29

TODO:

    *

"""

# =================================================================================================
#   IMPORTS
# =================================================================================================


import shutil
from pathlib import Path

from ceasiompy.utils.ceasiomlogger import get_logger
from ceasiompy.utils.ceasiompyutils import (
    SoftwareNotInstalled,
    get_install_path,
    get_results_directory,
    run_software,
)
from ceasiompy.utils.moduleinterfaces import get_toolinput_file_path, get_tooloutput_file_path

log = get_logger()

MODULE_DIR = Path(__file__).parent
MODULE_NAME = MODULE_DIR.name

# =================================================================================================
#   CLASSES
# =================================================================================================


# =================================================================================================
#   FUNCTIONS
# =================================================================================================


def launch_cpacscreator(cpacs_path, cpacs_out_path):
    """Function to run CPACSCrator with an input CPACS file

    Function 'launch_cpacscreator' run CPACSCrator with an input CPACS file and
    put the output CPACS file in the folder /ToolInput. CPACSCreator must be
    installed on your computer to run this function. (If you install CEASIOMpy
    with Conda it should be installed automatically)

    Source :
        * For CPACSCreator https://github.com/cfsengineering/CPACSCreator

    Args:
        cpacs_path (Path): Path to the input CPACS file
        cpacs_out_path (Path): Path to the output CPACS file

    """

    # Get the name of CPACSCreator (several names exists, depending on the OS and the version)
    cpacscreator_names = ["cpacscreator", "CPACS-Creator", "CPACSCreator"]

    for name in cpacscreator_names:
        install_path = get_install_path(name)
        if install_path is not None:
            software_name = name
            break

    if install_path is None:
        raise SoftwareNotInstalled("CPACSCreator is not installed on your computer")

    # Create a temporary directory to run CPACSCreator
    results_dir = get_results_directory(MODULE_NAME)
    results_dir.mkdir(parents=True, exist_ok=True)
    tmp_dir = Path(results_dir, "tmp")
    tmp_dir.mkdir()
    log.info(f"A tmp directory has been create at: {tmp_dir}")

    # Copy CPACS input file (.xml) in /tmp directory
    cpacs_tmp = Path(tmp_dir, "cpacsTMP.xml")
    shutil.copy(cpacs_path, cpacs_tmp)
    log.info("The input CPACS file has been copied in tmp directory")

    # Run CPACSCreator
    run_software(software_name=software_name, arguments=[str(cpacs_tmp)], wkdir=tmp_dir)

    # Copy CPACS tmp file (.xml) from the temp directory to /ToolOutput
    if cpacs_tmp.is_file():
        shutil.copy(cpacs_tmp, cpacs_out_path)
        log.info("The output CPACS file has been copied in /ToolOutput")
    else:
        log.error("The Output CPACS file cannot be found!")


# TODO: create a new function to export screenshots ...
# # Run cpacscreator with a script to save a screenshot
# # Problem: TIGLViewer in not close after the script in the shell
# os.system('cpacscreator ' + cpacs_tmp + ' --script test_script.js')

# =================================================================================================
#    MAIN
# =================================================================================================


def main(cpacs_path, cpacs_out_path):

    log.info("----- Start of " + MODULE_NAME + " -----")

    launch_cpacscreator(cpacs_path, cpacs_out_path)

    log.info("----- End of " + MODULE_NAME + " -----")


if __name__ == "__main__":

    cpacs_path = get_toolinput_file_path(MODULE_NAME)
    cpacs_out_path = get_tooloutput_file_path(MODULE_NAME)

    main(cpacs_path, cpacs_out_path)
