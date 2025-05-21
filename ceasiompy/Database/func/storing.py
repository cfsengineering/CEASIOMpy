"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Store data from workflow modules.

| Author: Leon Deligny
| Creation: 2025-Mar-03

"""

# ==============================================================================
#   IMPORTS
# ==============================================================================

from sqlite3 import connect
from ceasiompy.Database.func.utils import create_db
from ceasiompy.Database.func.pyavl import store_pyavl_data
from ceasiompy.Database.func.su2run import store_su2run_data
from ceasiompy.utils.ceasiompyutils import get_results_directory
from ceasiompy.Database.func.cpacs2gmsh import store_cpacs2gmsh_data
from ceasiompy.Database.func.dynamicstability import store_dynstab_data

from pathlib import Path
from sqlite3 import Cursor
from sqlite3 import Connection
from tixi3.tixi3wrapper import Tixi3

from typing import (
    List,
    Tuple,
    Callable,
)

from ceasiompy import log
from ceasiompy.PyAVL import MODULE_NAME as PYAVL_NAME
from ceasiompy.SU2Run import MODULE_NAME as SU2RUN_NAME
from ceasiompy.utils.commonpaths import CEASIOMPY_DB_PATH
from ceasiompy.CPACS2GMSH import MODULE_NAME as CPACS2GMSH_NAME
from ceasiompy.DynamicStability import MODULE_NAME as DYNSTAB_NAME
from ceasiompy.Database.func import (
    TABLE_DICT,
    ALLOWED_TABLES,
    ALLOWED_COLUMNS,
)

# ==============================================================================
#   CLASS
# ==============================================================================


class CeasiompyDb:
    """ceasiompy.db class manager"""

    # Load constants
    table_dict = TABLE_DICT

    def __init__(self: 'CeasiompyDb', db_path: Path = CEASIOMPY_DB_PATH) -> None:
        # Initialize constants
        self.db_path = db_path
        self.db_name = self.db_path.name

        # Create db if not exists
        if not self.db_path.exists():
            create_db(self.db_path)

        self.connection: Connection = connect(self.db_path)
        self.cursor: Cursor = self.connection.cursor()

        log.info(
            f"Connecting to database {self.db_name} at path {self.db_path}")

    def connect_to_table(self, module_name: str) -> str:
        table_name, table_schema = self.get_table_parameters(module_name)
        # Codacy: Table and column names are strictly validated against whitelisted values.
        # Table names are validated against ALLOWED_TABLES.

        # Validate table name
        if table_name not in ALLOWED_TABLES:
            raise ValueError(f"Invalid table name: {table_name}")

        create_table_query = f"""
            CREATE TABLE IF NOT EXISTS {table_name} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                {table_schema}
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """

        self.cursor.execute(create_table_query)
        self.commit()

        return table_name

    def get_table_name(self, module_name: str) -> str:
        return self.table_dict[module_name][0]

    def get_table_schema(self, module_name: str) -> str:
        return self.table_dict[module_name][1]

    def get_table_parameters(self, module_name: str) -> Tuple[str, str]:
        return self.get_table_name(module_name), self.get_table_schema(module_name)

    def commit(self) -> None:
        self.connection.commit()

    def close(self) -> None:
        log.info(f"Closing connection to database {self.db_name}.")
        self.connection.close()

    def get_data(
        self,
        table_name: str,
        columns: List[str],
        db_close=False,
        filters: List[str] = None,
    ) -> List[Tuple]:
        # Codacy: Table and column names are strictly validated against whitelisted values.
        # Table and column names are validated against ALLOWED_TABLES and ALLOWED_COLUMNS.

        # Validate table name
        if table_name not in ALLOWED_TABLES:
            raise ValueError(f"Invalid table name: {table_name}")

        # Validate column names
        if not all(col in ALLOWED_COLUMNS[table_name] for col in columns):
            raise ValueError(f"Invalid column name(s): {columns}")

        # Safely construct the query
        columns_str = ", ".join([f"`{col}`" for col in columns])  # Escape column names
        query = f"SELECT {columns_str} FROM `{table_name}`"  # nosec

        # Handle filters
        params = []
        if filters is not None:
            filter_clauses = []
            for filter_condition in filters:
                filter_clauses.append(filter_condition)
            query += " WHERE " + " AND ".join(filter_clauses)

        # Execute the query with parameters
        self.cursor.execute(query, params)

        data = self.cursor.fetchall()

        if db_close:
            self.close()

        return data

# ==============================================================================
#   FUNCTIONS
# ==============================================================================


def call_store_data(
    tixi: Tixi3,
    store2db: Callable[[Cursor, Path, Tixi3, str], None],
    wkdir: Path,
    module_name: str,
) -> None:
    """
    Stores data in correct table.
    """

    # Connect to db
    ceasiompy_db = CeasiompyDb()
    table_name = ceasiompy_db.connect_to_table(module_name)

    # Store data
    store2db(ceasiompy_db.cursor, wkdir, tixi, table_name)
    log.info(f"Finished storing data in table {table_name}.")

    # Commit changes and close the connection
    ceasiompy_db.commit()
    ceasiompy_db.close()


def store_data(tixi: Tixi3) -> None:
    """
    Looks at the workflow and stores data.
    Implemented for modules:
        - 'PyAVL': Aerodynamic Coefficients.
        - 'CPACS2GMSH': .su2 file.
        - 'DynamicStability': Dot-derivatives coefficients from PanelAero.
        - 'SU2Run': Forces, moments and dot-derivatives.
    """

    # You do not want to create a results directory "PyAVL"
    # with get_results_dir("PyAVL") if it does not exist.
    # Only access the path and then check if it exists.
    avl_dir: Path = get_results_directory(PYAVL_NAME, create=False)
    gmsh_dir: Path = get_results_directory(CPACS2GMSH_NAME, create=False)
    dynstab_dir: Path = get_results_directory(DYNSTAB_NAME, create=False)
    su2_dir: Path = get_results_directory(SU2RUN_NAME, create=False)

    if avl_dir.is_dir():
        call_store_data(tixi, store_pyavl_data, avl_dir, PYAVL_NAME)
    if gmsh_dir.is_dir():
        call_store_data(tixi, store_cpacs2gmsh_data, gmsh_dir, CPACS2GMSH_NAME)
    if dynstab_dir.is_dir():
        call_store_data(tixi, store_dynstab_data, dynstab_dir, DYNSTAB_NAME)
    if su2_dir.is_dir():
        call_store_data(tixi, store_su2run_data, su2_dir, SU2RUN_NAME)
        log.warning("Not implemented yet.")


# ==============================================================================
#    MAIN
# ==============================================================================


if __name__ == "__main__":
    log.info("Nothing to execute!")
