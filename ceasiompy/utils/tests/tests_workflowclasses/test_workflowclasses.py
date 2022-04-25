"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Test functions for 'utils/workflowclasses.py'

Python version: >=3.7

| Author : Aidan Jungo
| Creation: 2022-01-21

"""

# =================================================================================================
#   IMPORTS
# =================================================================================================

import pytest
import shutil
from pathlib import Path
from ceasiompy.utils.workflowclasses import (
    ModuleToRun,
    OptimSubWorkflow,
    Workflow,
    get_gui_related_modules,
)
from ceasiompy.utils.ceasiompyutils import run_module

MODULE_DIR = Path(__file__).parent
CPACS_PATH = Path(MODULE_DIR.parents[3], "test_files", "CPACSfiles", "D150_simple.xml")
CPACS_PATH_OUT = Path(MODULE_DIR, "D150_simple_out.xml")

# =================================================================================================
#   TESTS
# =================================================================================================


def test_module_name_error():

    with pytest.raises(ValueError):
        ModuleToRun("NotExistingModule", "", "", "")


def test_no_wkflow_error():

    with pytest.raises(FileNotFoundError):
        ModuleToRun("SU2Run", Path("./Not_WKFLOW"), CPACS_PATH)


class TestModuleToRun:

    # Remove old WKFLOW_test dir and create an empty one
    wkflow_test = Path(MODULE_DIR, "WKFLOW_test")
    if wkflow_test.exists():
        shutil.rmtree(wkflow_test)
    wkflow_test.mkdir()

    module_works = ModuleToRun("SU2Run", wkflow_test, CPACS_PATH, CPACS_PATH)

    def test_default_values(self):

        assert self.module_works.module_dir.exists()
        assert self.module_works.wkflow_dir.exists()
        assert self.module_works.cpacs_in.exists()
        assert self.module_works.cpacs_out.exists()

        assert not self.module_works.is_settinggui
        assert self.module_works.gui_related_modules == []
        assert not self.module_works.is_optim_module
        assert self.module_works.optim_related_modules == []
        assert self.module_works.optim_method is None

    def test_create_module_wkflow_dir(self):

        self.module_works.is_optim_module = True
        self.module_works.optim_method = "DOE"

        # Remove dir from previous runs
        if Path(self.wkflow_test, "01_DOE").exists():
            Path(self.wkflow_test, "01_DOE").rmdir()

        if Path(self.wkflow_test, "02_SU2Run").exists():
            Path(self.wkflow_test, "02_SU2Run").rmdir()

        self.module_works.create_module_wkflow_dir(1)
        assert self.module_works.module_wkflow_path.exists()
        assert self.module_works.module_wkflow_path.stem == "01_DOE"

        self.module_works.optim_method = None
        self.module_works.create_module_wkflow_dir(2)
        assert self.module_works.module_wkflow_path.exists()
        assert self.module_works.module_wkflow_path.stem == "02_SU2Run"

    def test_run(self):

        # Remove CPACS output file from privious run
        if CPACS_PATH_OUT.exists():
            CPACS_PATH_OUT.unlink()

        module = ModuleToRun("ModuleTemplate", self.wkflow_test, CPACS_PATH, CPACS_PATH_OUT)

        # TODO: how to separate test from workflowclasses.py and ceasiompyutils.py
        run_module(module)

        assert CPACS_PATH_OUT.exists()


@pytest.mark.skip(reason="Not implemented yet")
class TestOptimSubWorkflow:
    pass

    # TODO: When the optim subworkflow is implemented, add tests here


class TestWorkflow:

    workflow = Workflow()

    MODULE_TO_RUN = [
        "SettingsGUI",
        "CPACS2SUMO",
        "CLCalculator",
        "PyTornado",
        "SettingsGUI",
        "PlotAeroCoefficients",
    ]

    MODULE_OPTIM = ["NO", "YES", "YES", "NO", "NO", "NO"]
    MODULE_OPTIM_NOT_CONTIGOUS = ["YES", "NO", "YES", "NO", "NO", "NO"]

    def test_from_config_file(self):

        # Copy config file to WKFLOW_test dir
        shutil.copy(
            Path(MODULE_DIR, "ceasiompy.cfg"), Path(MODULE_DIR, "WKFLOW_test", "ceasiompy.cfg")
        )

        self.workflow.from_config_file(Path(MODULE_DIR, "WKFLOW_test", "ceasiompy.cfg"))

        assert self.workflow.modules_list == self.MODULE_TO_RUN
        assert self.workflow.module_optim == self.MODULE_OPTIM
        assert self.workflow.optim_method == "OPTIM"

    def test_write_config_file(self):
        pass

    def test_set_workflow(self):

        for dir in Path(MODULE_DIR, "WKFLOW_test").iterdir():
            if dir.is_dir():
                shutil.rmtree(dir, ignore_errors=True)

        # Test all raising errors
        self.workflow.optim_method = "notValidMethod"
        with pytest.raises(ValueError):
            self.workflow.set_workflow()

        self.workflow.optim_method = "NONE"
        self.workflow.module_optim = self.MODULE_OPTIM
        with pytest.raises(ValueError):
            self.workflow.set_workflow()

        self.workflow.optim_method = "DOE"
        self.workflow.module_optim = self.MODULE_OPTIM_NOT_CONTIGOUS
        with pytest.raises(ValueError):
            self.workflow.set_workflow()

        self.workflow.module_optim = self.MODULE_OPTIM
        self.workflow.working_dir = ""
        with pytest.raises(ValueError):
            self.workflow.set_workflow()

        self.workflow.from_config_file(Path(MODULE_DIR, "WKFLOW_test", "ceasiompy.cfg"))
        self.workflow.cpacs_in = Path(MODULE_DIR, "NotExistingCPACS.xml")
        with pytest.raises(FileNotFoundError):
            self.workflow.set_workflow()

        # Test nomral behaviour
        self.workflow = Workflow()
        self.workflow.from_config_file(Path(MODULE_DIR, "WKFLOW_test", "ceasiompy.cfg"))
        self.workflow.optim_method = "OPTIM"
        self.workflow.set_workflow()

        assert self.workflow.current_wkflow_dir.exists()
        assert self.workflow.cpacs_in.exists()

        assert len(list(self.workflow.current_wkflow_dir.iterdir())) == 7

        assert self.workflow.modules[0].name == "SettingsGUI"
        assert self.workflow.modules[1].name == "OPTIM"
        assert self.workflow.modules[2].name == "PyTornado"
        assert self.workflow.modules[3].name == "SettingsGUI"
        assert self.workflow.modules[4].name == "PlotAeroCoefficients"

        assert self.workflow.modules[0].is_settinggui
        assert self.workflow.modules[0].gui_related_modules == [
            "SettingsGUI",
            "CPACS2SUMO",
            "CLCalculator",
            "PyTornado",
        ]
        assert self.workflow.modules[0].module_wkflow_path == Path(
            self.workflow.current_wkflow_dir, "01_SettingsGUI"
        )

        assert self.workflow.modules[1].is_optim_module
        assert self.workflow.modules[1].optim_method == "OPTIM"
        assert self.workflow.modules[1].module_wkflow_path == Path(
            self.workflow.current_wkflow_dir, "02_OPTIM"
        )

        assert not self.workflow.modules[2].is_optim_module
        assert self.workflow.modules[2].optim_method is None
        assert self.workflow.modules[2].module_wkflow_path == Path(
            self.workflow.current_wkflow_dir, "03_PyTornado"
        )


def test_get_gui_related_modules():
    """Test 'get_gui_related_modules' function.'"""

    module_list = ["SettingsGUI"]
    assert get_gui_related_modules(module_list) == module_list

    module_list = ["SettingsGUI", "CPACS2SUMO", "CLCalculator", "PyTornado"]
    assert get_gui_related_modules(module_list) == module_list

    module_list = ["SettingsGUI", "CPACS2SUMO", "CLCalculator", "SettingsGUI"]
    assert get_gui_related_modules(module_list) == module_list[:-1]

    module_list = ["SettingsGUI", "CPACS2SUMO", "CLCalculator", "SettingsGUI", "PyTornado"]
    assert get_gui_related_modules(module_list, 3) == module_list[-2:]


# =================================================================================================
#    MAIN
# =================================================================================================

if __name__ == "__main__":

    print("Test configfile.py")
    print("To run test use the following command:")
    print(">> pytest -v")
