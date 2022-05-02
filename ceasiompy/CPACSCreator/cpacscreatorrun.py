"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

CPACS Creator python launcher

Python version: >=3.7

| Author : Aidan Jungo
| Creation: 2018-10-29

TODO:

    *

"""

# =================================================================================================
#   IMPORTS
# =================================================================================================

import os
from pathlib import Path
import shutil
import platform


from ceasiompy.utils.ceasiomlogger import get_logger
from ceasiompy.utils.moduleinterfaces import get_toolinput_file_path, get_tooloutput_file_path

log = get_logger(__file__.split(".")[0])

MODULE_DIR = Path(__file__).parent
MODULE_NAME = MODULE_DIR.name

# =================================================================================================
#   CLASSES
# =================================================================================================


# =================================================================================================
#   FUNCTIONS
# =================================================================================================


def launch_cpacscreator(cpacs_path, cpacs_out_path):
    """Function to run CPACSCrator with an imput CPACS file

    Function 'launch_cpacscreator' run CPACSCrator with an imput CPACS file and
    put the output CPACS file in the folder /ToolInput. CPACSCreator must be
    installed on your computre to run this function. (If you install CEASIOMpy
    with Conda it should be installed automatically)

    Source :
        * For CPACSCreator https://github.com/cfsengineering/CPACSCreator

    Args:
        cpacs_path (Path): Path to the input CPACS file
        cpacs_out_path (Path): Path to the output CPACS file

    """

    current_os = platform.system()
    log.info("Your current OS is: " + current_os)

    if current_os == "Darwin":
        install_path = shutil.which("CPACS-Creator")

    elif current_os == "Linux":
        install_path = shutil.which("cpacscreator")

    elif current_os == "Windows":
        install_path = shutil.which("CPACSCreator")

    else:
        raise OSError("OS not recognize!")

    # Check if CPACSCreator is installed
    if install_path:
        log.info('"CPACSCreator" is intall at: ' + install_path)
    else:
        raise RuntimeError(
            "'CPACSCreator' is not install on your computer or in your Conda environment!"
        )

    # Empty /tmp directory
    TMP_DIR = Path(MODULE_DIR, "tmp")
    if TMP_DIR.is_dir():
        for tmp_file in TMP_DIR.iterdir():
            tmp_file.unlink()
    else:
        TMP_DIR.mkdir()
    log.info("The /tmp directory has been cleared.")

    # Copy CPACS input file (.xml) in /tmp directory
    cpacs_tmp = Path(MODULE_DIR, "tmp", "cpacsTMP.xml")
    if cpacs_path.is_file():
        shutil.copy(cpacs_path, cpacs_tmp)
        log.info("The input CPACS file has been copied in /tmp ")
    else:
        log.error("The ToolInput (.xml file) cannot be found!")

    # Run 'cpacscreator' with CPACS input
    if current_os == "Darwin":
        os.system("CPACS-Creator " + str(cpacs_tmp))

    elif current_os == "Linux":
        os.system("cpacscreator " + str(cpacs_tmp))

    elif current_os == "Windows":
        os.system("CPACSCreator " + str(cpacs_tmp))

    else:
        raise OSError("OS not recognize!")

    # Copy CPACS temp file (.xml) from the temp directory to /ToolOutput
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
