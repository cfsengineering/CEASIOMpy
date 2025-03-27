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

# ==============================================================================
#   FUNCTIONS
# ==============================================================================


def get_aircrafts_list() -> List:
    """
    Access different aircraft names from "ceasiompy.db".

    Returns:
        (List): Aircraft names.

    """

    # Check if database exists
    if CEASIOMPY_DB_PATH.exists():
        # Go look in database for all different aircraft names among all different tables
        aircrafts = set()

        # Connect to the database
        conn = sqlite3.connect(CEASIOMPY_DB_PATH)
        cursor = conn.cursor()

        try:
            # Get all table names
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()

            for table in tables:
                table_name = table[0]

                # Check if the table has an "aircraft" column
                cursor.execute(f"PRAGMA table_info({table_name})")
                columns = cursor.fetchall()
                if any(column[1] == "aircraft" for column in columns):
                    # Query for distinct aircraft names from the table
                    cursor.execute(f"SELECT DISTINCT aircraft FROM {table_name}")
                    rows = cursor.fetchall()
                    for row in rows:
                        aircrafts.add(row[0])

        except sqlite3.Error as e:
            log.warning(f"An error occurred: {e}.")

        finally:
            conn.close()

        return list(aircrafts)

    else:
        return []


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
    Checks if data is alrady in table.
    """
    # Build the WHERE clause for checking existing data
    where_clause = " AND ".join([f"{col} = ?" for col in columns])
    check_query = f"SELECT 1 FROM {table_name} WHERE {where_clause} LIMIT 1"

    # Check if the data already exists
    unique_values = [data[col] for col in columns]
    cursor.execute(check_query, tuple(unique_values))
    if cursor.fetchone(): return True
    else: return False


def data_to_db(cursor: Cursor, data: Dict, table_name: str) -> None:
    """
    Inserts one line at a time if not already in table.
    """
    # Get the keys that exist in your data dictionary
    columns = list(data.keys())

    if check_in_table(cursor, data, columns, table_name):
        log.info(f"{data.values()} already in {table_name}.")
    else:
        # Create the SQL statement dynamically
        placeholders = ", ".join(["?" for _ in columns])
        columns_str = ", ".join(columns)
        
        query = f"""
                    INSERT INTO {table_name} (
                        {columns_str}
                    ) VALUES (
                        {placeholders}
                    )
                """
        
        # Execute the statement with values
        cursor.execute(query, tuple(data.values()))


# ==============================================================================
#    MAIN
# ==============================================================================


if __name__ == "__main__":
    log.info("Nothing to execute!")
