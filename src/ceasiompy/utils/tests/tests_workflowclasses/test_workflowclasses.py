"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Test functions for 'utils/workflowclasses.py'
"""

# =================================================================================================
#   IMPORTS
# =================================================================================================

import pytest

from ceasiompy.utils.ceasiompyutils import run_module, current_workflow_dir

from pathlib import Path
from ceasiompy.utils.workflowclasses import ModuleToRun, Workflow


MODULE_DIR = Path(__file__).parent
CPACS_PATH = Path(
    MODULE_DIR.parents[3].parent, "test_files", "CPACSfiles", "D150_simple.xml"
)
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
    wkflow_dir = current_workflow_dir()
    module_works = ModuleToRun("SU2Run", wkflow_dir, CPACS_PATH, CPACS_PATH)

    def test_default_values(self):

        assert self.module_works.module_dir.exists()
        assert self.module_works.wkflow_dir.exists()
        assert self.module_works.cpacs_in.exists()
        assert self.module_works.cpacs_out.exists()
        assert self.module_works.gui_related_modules == []

    def test_create_module_wkflow_dir(self):

        self.module_works.optim_method = "DOE"
        if Path(self.wkflow_test, "01_SU2Run").exists():
            Path(self.wkflow_test, "01_SU2Run").rmdir()

        self.module_works.create_module_wkflow_dir(1)
        assert self.module_works.module_wkflow_path.exists()
        assert self.module_works.module_wkflow_path.stem == "01_SU2Run"

    def test_run(self):

        # Remove CPACS output file from privious run
        if CPACS_PATH_OUT.exists():
            CPACS_PATH_OUT.unlink()

        module = ModuleToRun(
            "ModuleTemplate", self.wkflow_dir, CPACS_PATH, CPACS_PATH_OUT)

        # TODO: how to separate test from workflowclasses.py and ceasiompyutils.py
        run_module(module)

        assert CPACS_PATH_OUT.exists()


class TestWorkflow:

    workflow = Workflow()
    wkflow_test = Path(MODULE_DIR, "WKFLOW_test")

    MODULE_TO_RUN = [
        "CLCalculator",
        "PyAVL",
        "SaveAeroCoefficients",
    ]

    def test_from_config_file(self):
        self.workflow.from_config_file(
            Path(MODULE_DIR, "WKFLOW_test", "ceasiompy.cfg")
        )
        assert self.workflow.modules_list == self.MODULE_TO_RUN

    def test_set_workflow(self):
        # Test all raising errors
        self.workflow.optim_method = "notValidMethod"
        with pytest.raises(ValueError):
            self.workflow.set_workflow()

        self.workflow.working_dir = ""
        with pytest.raises(ValueError):
            self.workflow.set_workflow()

        self.workflow.from_config_file(Path(MODULE_DIR, "WKFLOW_test", "ceasiompy.cfg"))
        self.workflow.cpacs_in = Path(MODULE_DIR, "NotExistingCPACS.xml")
        with pytest.raises(FileNotFoundError):
            self.workflow.set_workflow()

        # Test normal behavior
        self.workflow = Workflow()
        self.workflow.from_config_file(Path(MODULE_DIR, "WKFLOW_test", "ceasiompy.cfg"))
        self.workflow.cpacs_in = CPACS_PATH
        self.workflow.set_workflow()

        assert self.workflow.modules[0].module_wkflow_path == Path(
            self.workflow.current_wkflow_dir, "01_CLCalculator"
        )

        assert self.workflow.modules[1].module_wkflow_path == Path(
            self.workflow.current_wkflow_dir, "02_PyAVL"
        )


# =================================================================================================
#    MAIN
# =================================================================================================

if __name__ == "__main__":
    test_module_name_error()
    test_no_wkflow_error()
    test1 = TestModuleToRun()
    test1.test_default_values()
    test1.test_create_module_wkflow_dir()
    test1.test_run()
    test2 = TestWorkflow()
    test2.test_from_config_file()
    test2.test_set_workflow()
    print("Test configfile.py")
    print("To run test use the following command:")
    print(">> pytest -v")
