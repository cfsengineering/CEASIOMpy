"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Test functions for Database module.

| Author: Leon Deligny
| Creation: 25 March 2025

"""

# =================================================================================================
#   IMPORTS
# =================================================================================================

from ceasiompy.utils.decorators import log_test

from ceasiompy.Database.func.utils import (
    create_db,
    data_to_db,
)

from pathlib import Path
from unittest import main
from ceasiompy.Database.func.storing import CeasiompyDb
from ceasiompy.utils.ceasiompytest import CeasiompyTest

from ceasiompy import log
from ceasiompy.PyAVL import MODULE_NAME as PYAVL_NAME
from ceasiompy.utils.commonpaths import TESTCEASIOMPY_DB_PATH

# =================================================================================================
#   CLASSES
# =================================================================================================


class TestDatabase(CeasiompyTest):

    @classmethod
    def setUpClass(cls: 'TestDatabase') -> None:
        cls.testceasiompy_db_path: Path = TESTCEASIOMPY_DB_PATH

    @log_test
    def test_create_db(self: 'TestDatabase') -> None:
        create_db(path=self.testceasiompy_db_path)
        self.assertTrue(self.testceasiompy_db_path.exists(), "Database file was not created")

        # Remove if exists
        if self.testceasiompy_db_path.exists():
            self.testceasiompy_db_path.unlink()

    @log_test
    def test_data_to_db(self: 'TestDatabase') -> None:
        # Define constants
        module_name = PYAVL_NAME  # test on AVL module
        data = {
            "aircraft": "test_aircraft",
            "mach": 0.0, "alpha": 0.0, "beta": 0.0,
            "pb_2V": 0.0, "qc_2V": 0.0, "rb_2V": 0.0,
            "flap": 0.0, "aileron": 0.0, "elevator": 0.0, "rudder": 0.0,
            "xref": 0.0, "yref": 0.0, "zref": 0.0,
            "cd": 0.0, "cs": 0.0, "cl": 0.0,
            "cmd": 0.0, "cms": 0.0, "cml": 0.0,
            "cmd_a": 0.0, "cms_a": 0.0, "cml_a": 0.0,
            "cmd_b": 0.0, "cms_b": 0.0, "cml_b": 0.0,
        }

        testceasiompy_db = CeasiompyDb(db_path=self.testceasiompy_db_path)
        table_name = testceasiompy_db.connect_to_table(module_name)

        data_to_db(testceasiompy_db.cursor, data, table_name)
        log.info(f"Successfully stored data in table {table_name}.")

        testceasiompy_db.commit()
        testceasiompy_db.close()

# =================================================================================================
#    MAIN
# =================================================================================================


if __name__ == "__main__":
    main(verbosity=0)
