"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Test functions for 'utils/ceasiompyfunctions.py'

Python version: >=3.7

| Author : Aidan Jungo
| Creation: 2022-01-21

"""

# =================================================================================================
#   IMPORTS
# =================================================================================================

import os
import pytest
from pathlib import Path
from ceasiompy.utils.ceasiompyfunctions import ModuleToRun, Workflow
from ceasiompy.utils.ceasiompyutils import get_results_directory

MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
CPACS_PATH = os.path.join(MODULE_DIR, "D150_simple.xml")
CPACS_PATH_OUT = os.path.join(MODULE_DIR, "D150_simple_out.xml")

# =================================================================================================
#   CLASSES
# =================================================================================================


class TestModuleToRun:

    wkflow_test = Path.joinpath(Path(MODULE_DIR, "WKFLOW_test"))
    module_works = ModuleToRun("SU2Run", Path(wkflow_test), Path(CPACS_PATH), Path(CPACS_PATH))

    def test_default_values(self):

        assert self.module_works.module_path.exists()
        assert self.module_works.wkflow_dir.exists()
        assert self.module_works.cpacs_in.exists()
        assert self.module_works.cpacs_out.exists()

        assert not self.module_works.is_settinggui
        assert self.module_works.gui_related_modules == []
        assert not self.module_works.is_optim_module
        assert self.module_works.optim_related_modules == []
        assert self.module_works.optim_method is None

    def test_module_name_error(self):

        with pytest.raises(ValueError):
            ModuleToRun("NotExistingModule", "", "", "")

    def test_no_wkflow_error(self):

        with pytest.raises(FileNotFoundError):
            ModuleToRun("SU2Run", Path("./Not_WKFLOW"), Path(CPACS_PATH))

    def test_define_settinggui(self):

        RELATED_MODULE = ["CPACS2SUMO", "SU2Run"]
        self.module_works.define_settinggui(RELATED_MODULE)

        assert self.module_works.gui_related_modules == RELATED_MODULE
        assert self.module_works.is_settinggui

    def test_define_optim_module(self):

        OPTIM_METHOD = ["OPTIM", "DOE"]

        for optim_method in OPTIM_METHOD:
            self.module_works.define_optim_module(optim_method)
            assert self.module_works.optim_method == optim_method
            assert self.module_works.is_optim_module

        with pytest.raises(ValueError):
            self.module_works.define_optim_module("invalid_optim_method")

    def test_create_module_wkflow_dir(self):

        # Remove dir from previous runs
        if Path.joinpath(self.wkflow_test, "01_DOE").exists():
            Path.joinpath(self.wkflow_test, "01_DOE").rmdir()

        if Path.joinpath(self.wkflow_test, "02_SU2Run").exists():
            Path.joinpath(self.wkflow_test, "02_SU2Run").rmdir()

        self.module_works.create_module_wkflow_dir(1)
        assert self.module_works.module_wkflow_path.exists()
        assert self.module_works.module_wkflow_path.stem == "01_DOE"

        self.module_works.optim_method = None
        self.module_works.create_module_wkflow_dir(2)
        assert self.module_works.module_wkflow_path.exists()
        assert self.module_works.module_wkflow_path.stem == "02_SU2Run"

        assert self.module_works.cpacs_out == Path.joinpath(
            self.module_works.module_wkflow_path, "ToolOutput.xml"
        )

    def test_run(self):

        # Remove CPACS output file from privious run
        if Path(CPACS_PATH_OUT).exists():
            Path(CPACS_PATH_OUT).unlink()

        module = ModuleToRun(
            "ModuleTemplate", self.wkflow_test, Path(CPACS_PATH), Path(CPACS_PATH_OUT)
        )
        module.run()

        assert Path(CPACS_PATH_OUT).exists()


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

    def test_from_config_file(self):

        # SHould use Pathlib everywhere ??
        self.workflow.from_config_file(os.path.join(MODULE_DIR, "WKFLOW_test", "ceasiompy.cfg"))

        assert self.workflow.module_to_run == self.MODULE_TO_RUN

        assert self.workflow.module_optim == self.MODULE_OPTIM

        assert self.workflow.optim_method == "OPTIM"

    def test_write_config_file(self):
        pass

    def test_set_workflow(self):
        import shutil

        for dir in Path(MODULE_DIR, "WKFLOW_test").iterdir():
            if dir.is_dir():
                shutil.rmtree(dir, ignore_errors=True)

        self.workflow.set_workflow()

        assert self.workflow.current_wkflow_dir.exists()
        assert self.workflow.cpacs_path.exists()

        assert len(list(self.workflow.current_wkflow_dir.iterdir())) == 7

        assert self.workflow.module_to_run_obj[0].module_name == "SettingsGUI"
        assert self.workflow.module_to_run_obj[1].module_name == "OPTIM"
        assert self.workflow.module_to_run_obj[2].module_name == "PyTornado"
        assert self.workflow.module_to_run_obj[3].module_name == "SettingsGUI"
        assert self.workflow.module_to_run_obj[4].module_name == "PlotAeroCoefficients"

        assert self.workflow.module_to_run_obj[0].is_settinggui
        assert self.workflow.module_to_run_obj[0].gui_related_modules == [
            "SettingsGUI",
            "CPACS2SUMO",
            "CLCalculator",
            "PyTornado",
        ]
        assert self.workflow.module_to_run_obj[0].module_wkflow_path == Path.joinpath(
            self.workflow.current_wkflow_dir, "01_SettingsGUI"
        )

        assert self.workflow.module_to_run_obj[1].is_optim_module
        assert self.workflow.module_to_run_obj[1].optim_method == "OPTIM"
        assert self.workflow.module_to_run_obj[1].module_wkflow_path == Path.joinpath(
            self.workflow.current_wkflow_dir, "02_OPTIM"
        )

        assert not self.workflow.module_to_run_obj[2].is_optim_module
        assert self.workflow.module_to_run_obj[2].optim_method is None
        assert self.workflow.module_to_run_obj[2].module_wkflow_path == Path.joinpath(
            self.workflow.current_wkflow_dir, "03_PyTornado"
        )


def test_get_results_directory():

    results_dir = get_results_directory("ExportCSV")
    assert results_dir == Path(Path.cwd(), "Results", "Aeromaps")

    results_dir = get_results_directory("CPACS2SUMO")
    assert results_dir == Path(Path.cwd(), "Results", "SUMO")

    with pytest.raises(ValueError):
        results_dir = get_results_directory("NotExistingModule")


# =================================================================================================
#   FUNCTIONS
# =================================================================================================


# =================================================================================================
#    MAIN
# =================================================================================================

if __name__ == "__main__":

    print("Test configfile.py")
    print("To run test use the following command:")
    print(">> pytest -v")
