"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Utility functions for Static stability module.

| Author: Leon Deligny
| Creation: 2025-01-27

"""

# =================================================================================================
#   IMPORTS
# =================================================================================================

from typing import List

from markdownpy.markdownpy import (
    Table,
    MarkdownDoc,
)

from ceasiompy import log

# =================================================================================================
#    MAIN
# =================================================================================================


def markdownpy_to_markdown(md: MarkdownDoc, table: List[List[str]]) -> None:
    """
    Writes a Markdownpy Table to a Markdown object.

    Args:
        table (Markdownpy Table): Table generated from 'generate_stab_table' function.


    """
    if len(table) > 1:
        md.p(Table(table).write())
        md.line()

# =================================================================================================
#    MAIN
# =================================================================================================


if __name__ == "__main__":
    log.info("Nothing to execute.")
