"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Utils for Database module.

Python version: >=3.8

| Author: Leon Deligny
| Creation: 2025-Mar-03

"""

# ==============================================================================
#   IMPORTS
# ==============================================================================

import sqlite3

from pathlib import Path
from sqlite3 import Cursor

from typing import (
    List,
    Dict,
)

from ceasiompy import log
from ceasiompy.utils.commonpaths import CEASIOMPY_DB_PATH

from ceasiompy.Database.func import (
    ALLOWED_TABLES,
    ALLOWED_COLUMNS,
)

# ==============================================================================
#   FUNCTIONS
# ==============================================================================


def split_line(line: str, index: int) -> float:
    """
    Splits a line with "=" sign and keeps only the value at specified index.
    """
    return float(line.split("=")[index].strip().split()[0])


def create_db(path: Path = CEASIOMPY_DB_PATH) -> None:
    """
    Creates a database at specified path.
    """

    # Make sure parent directory exists
    if not path.parent.is_dir():
        log.info(f"Creating directory at {path.parent}")
        path.parent.mkdir(parents=True, exist_ok=True)

    # Create database if it does not exist
    conn = sqlite3.connect(path)
    conn.close()
    log.info(f"Database created at {path}.")


def check_in_table(cursor: Cursor, data: Dict, columns: List, table_name: str) -> bool:
    """
    Checks if data is already in the table using a raw cursor.
    """
    # Codacy: Table and column names are strictly validated against whitelisted values.
    # Validate table name
    if table_name not in ALLOWED_TABLES:
        raise ValueError(f"Invalid table name: {table_name}")

    # Validate column names
    if not all(col in ALLOWED_COLUMNS[table_name] for col in columns):
        raise ValueError(f"Invalid column name(s): {columns}")

    # Build the WHERE clause dynamically
    where_clause = " AND ".join([f"{col} = ?" for col in columns])
    query = f"SELECT 1 FROM {table_name} WHERE {where_clause} LIMIT 1"  # nosec
    params = tuple(data[col] for col in columns)

    cursor.execute(query, params)
    return cursor.fetchone() is not None


def data_to_db(cursor: Cursor, data: Dict, table_name: str) -> None:
    """
    Inserts one line at a time if not already in table.
    """

    # Table names are validated against ALLOWED_TABLES.
    columns = list(data.keys())

    # Validate table name
    if table_name not in ALLOWED_TABLES:
        raise ValueError(f"Invalid table name: {table_name}")

    # Validate column names
    invalid_columns = [col for col in columns if col not in ALLOWED_COLUMNS[table_name]]
    if invalid_columns:
        raise ValueError(f"Invalid column name(s): {invalid_columns}")

    if check_in_table(cursor, data, columns, table_name):
        log.info(f"{data.values()} already in {table_name}.")
    else:
        # Safely escape table and column names
        escaped_table_name = f'"{table_name}"'
        escaped_columns = ", ".join(f'"{col}"' for col in columns)

        # Create the SQL statement dynamically
        placeholders = ", ".join(["?" for _ in columns])

        # Codacy: Table and column names are strictly validated against whitelisted values.
        query = f"""
                    INSERT INTO {escaped_table_name} (
                        {escaped_columns}
                    ) VALUES (
                        {placeholders}
                    )
                """  # nosec

        # Execute the statement with values
        cursor.execute(query, tuple(data.values()))


# ==============================================================================
#    MAIN
# ==============================================================================


if __name__ == "__main__":
    log.info("Nothing to execute!")
