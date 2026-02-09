"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Test functions for 'utils/workflowclasses.py'
"""

# Imports

import pytest

from ceasiompy.utils.ceasiompyutils import current_workflow_dir

from pathlib import Path
from ceasiompy.utils.workflowclasses import (
    Workflow,
    ModuleToRun,
)

from ceasiompy.pyavl import MODULE_NAME as PYAVL
from ceasiompy.su2run import MODULE_NAME as SU2RUN
from ceasiompy.staticstability import MODULE_NAME as STATICSTABILITY


MODULE_DIR = Path(__file__).parent
CPACS_PATH = Path(MODULE_DIR.parents[3].parent, "geometries", "cpacsfiles", "d150.xml")
CPACS_PATH_OUT = Path(MODULE_DIR, "d150_out.xml")

# =================================================================================================
#   TESTS
# =================================================================================================


def test_module_name_error():

    with pytest.raises(ValueError):
        ModuleToRun("NotExistingModule", "", "", "")


def test_no_wkflow_error():

    with pytest.raises(FileNotFoundError):
        ModuleToRun(SU2RUN, Path("./Not_WKFLOW"), CPACS_PATH)


class TestModuleToRun:

    # Remove old wkflow_test dir and create an empty one
    wkflow_test = Path(MODULE_DIR, "wkflow_test")
    wkflow_dir = current_workflow_dir()
    module_works = ModuleToRun(SU2RUN, wkflow_dir, CPACS_PATH, CPACS_PATH)

    def test_default_values(self):

        assert self.module_works.module_dir.exists()
        assert self.module_works.wkflow_dir.exists()
        assert self.module_works.cpacs_in.exists()
        assert self.module_works.cpacs_out.exists()
        assert self.module_works.gui_related_modules == []

    def test_create_module_wkflow_dir(self):

        self.module_works.optim_method = "DOE"
        if Path(self.wkflow_test, f"01_{SU2RUN}").exists():
            Path(self.wkflow_test, f"01_{SU2RUN}").rmdir()

        self.module_works.create_module_wkflow_dir(1)
        assert self.module_works.module_wkflow_path.exists()
        assert self.module_works.module_wkflow_path.stem == f"01_{SU2RUN}"


class TestWorkflow:

    workflow = Workflow()
    wkflow_test = Path(MODULE_DIR, "wkflow_test")

    MODULE_TO_RUN = [PYAVL, STATICSTABILITY]
    wkflow_test.mkdir(exist_ok=True)
    cfg_path = wkflow_test / "ceasiompy.cfg"
    if not cfg_path.exists():
        cfg_path.write_text(
            "% File written 2022-01-17 14:46:53.344314\n"
            "CPACS_TOOLINPUT = ./d150.xml\n"
            f"MODULE_TO_RUN = ( {PYAVL}, {STATICSTABILITY} )\n"
        )

    def test_from_config_file(self):
        self.workflow.from_config_file(Path(MODULE_DIR, "wkflow_test", "ceasiompy.cfg"))
        assert self.workflow.modules_list == self.MODULE_TO_RUN

    def test_set_workflow(self):
        # Test all raising errors
        self.workflow.optim_method = "notValidMethod"
        with pytest.raises(ValueError):
            self.workflow.set_workflow()

        self.workflow.working_dir = ""
        with pytest.raises(ValueError):
            self.workflow.set_workflow()

        self.workflow.from_config_file(Path(MODULE_DIR, "wkflow_test", "ceasiompy.cfg"))
        self.workflow.cpacs_in = Path(MODULE_DIR, "NotExistingCPACS.xml")
        with pytest.raises(FileNotFoundError):
            self.workflow.set_workflow()

        # Test normal behavior
        self.workflow = Workflow()
        self.workflow.from_config_file(Path(MODULE_DIR, "wkflow_test", "ceasiompy.cfg"))
        self.workflow.cpacs_in = CPACS_PATH
        self.workflow.set_workflow()

        assert self.workflow.modules[0].module_wkflow_path == Path(
            self.workflow.current_wkflow_dir, f"01_{PYAVL}"
        )

        assert self.workflow.modules[1].module_wkflow_path == Path(
            self.workflow.current_wkflow_dir, f"02_{STATICSTABILITY}"
        )


# Main
if __name__ == "__main__":
    test_module_name_error()
    test_no_wkflow_error()
    test1 = TestModuleToRun()
    test1.test_default_values()
    test1.test_create_module_wkflow_dir()
    test2 = TestWorkflow()
    test2.test_from_config_file()
    test2.test_set_workflow()
    print("Test configfile.py")
    print("To run test use the following command:")
    print(">> pytest -v")
