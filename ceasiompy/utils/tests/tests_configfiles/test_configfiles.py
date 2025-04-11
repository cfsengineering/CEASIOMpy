"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Test functions for 'lib/SkinFriction/skinfriction.py'



| Author : Aidan Jungo
| Creation: 2021-12-13

"""

# ==============================================================================
#   IMPORTS
# ==============================================================================

from pathlib import Path

import pytest
from ceasiompy.utils.configfiles import ConfigFile

MODULE_DIR = Path(__file__).parent

# =================================================================================================
#   CLASSES
# =================================================================================================


# =================================================================================================
#   FUNCTIONS
# =================================================================================================


def test_configfiles():
    """Test the class 'ConfigFile'"""

    # Test Simple ConfigFile class not from a file
    CONFIG_0 = Path(MODULE_DIR, "config_test0.cfg")
    CONFIG_OUT_0 = Path(MODULE_DIR, "config_test0_out.cfg")

    config0 = ConfigFile()
    config0["TEXT"] = "text"
    config0["NUMBER"] = 4
    config0["LIST_OF_TEXT"] = ["abc", "def", "hij"]
    config0["LIST_OF_NUM"] = [1, 2.71, 3.1416]

    config0.write_file(CONFIG_OUT_0, overwrite=True)

    with open(CONFIG_0, "r") as c, open(CONFIG_OUT_0, "r") as cout:
        assert c.readlines() == cout.readlines()

    # Test ConfigFile from a Path object instead of string
    file_path = Path(CONFIG_0)
    config0_path = ConfigFile(file_path)
    assert config0["LIST_OF_NUM"] == config0_path["LIST_OF_NUM"]

    # Check if ValueError is raised when trying read a file with wrong extension
    with pytest.raises(ValueError):
        ConfigFile(Path("config_test0.wrong"))

    # Check if ValueError is raised when trying read a non existing file
    with pytest.raises(FileNotFoundError):
        ConfigFile(Path("config_test1000.cfg"))

    # Read a config file modifing it and write it back
    CONFIG_1 = Path(MODULE_DIR, "config_test1.cfg")
    CONFIG_OUT_1 = Path(MODULE_DIR, "config_test1_out.cfg")

    config1 = ConfigFile(CONFIG_1)
    config1["NEWLINE"] = "text"
    config1["VALUE1"] = 4
    config1["comment_6"] = "Test comment"

    config1.write_file(CONFIG_OUT_1, overwrite=True)

    assert config1["VALUE1"] == 4
    assert config1["VALUE2"] is None
    assert config1["LIST"] == ["a", "b", "c"]
    assert config1["DIFFENT_LIST"] == ["( 1, 1.0 | a )", "( 2, 2.0 | b )", "( 3, 3.0 | c )"]
    assert config1["NEWLINE"] == "text"
    assert config1["comment_6"] == "Test comment"

    with open(CONFIG_OUT_1, "r") as cout:
        lines = cout.readlines()

    assert lines[1] == "% Comment 2\n"
    assert lines[2] == "VALUE1 = 4\n"
    assert lines[3] == "VALUE2 = NONE\n"
    assert lines[5] == "LIST = ( a, b, c )\n"
    assert lines[6] == "DIFFENT_LIST = ( 1, 1.0 | a ); ( 2, 2.0 | b ); ( 3, 3.0 | c )\n"
    assert lines[7] == "NEWLINE = text\n"
    assert lines[8] == "% Test comment\n"

    with pytest.raises(FileExistsError):
        config1.write_file(CONFIG_OUT_1, overwrite=False)

    CONFIG_2 = Path(MODULE_DIR, "config_test2.cfg")

    with pytest.raises(ValueError):
        ConfigFile(CONFIG_2)

    # Remove output files
    if CONFIG_OUT_0.exists():
        CONFIG_OUT_0.unlink()

    if CONFIG_OUT_1.exists():
        CONFIG_OUT_1.unlink()


# =================================================================================================
#    MAIN
# =================================================================================================

if __name__ == "__main__":

    print("Test configfile.py")
    print("To run test use the following command:")
    print(">> pytest -v")
