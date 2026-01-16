"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Extract results from AVL calculations and save them in a CPACS file.
"""

# =================================================================================================
#   IMPORTS
# =================================================================================================

import shutil
import subprocess

from pathlib import Path

from ceasiompy import log

# =================================================================================================
#   FUNCTIONS
# =================================================================================================


def convert_ps_to_pdf(wkdir: Path) -> None:
    """
    Function to convert AVL 'plot.ps' to 'plot.pdf'.
    """

    # Check if plot to convert exists
    if not Path(wkdir, "plot.ps").exists():
        log.warning("File 'plot.ps' does not exist. Nothing to convert.")
        return

    # Check if ps2pdf exists
    if not shutil.which("ps2pdf"):
        log.warning("ps2pdf not available.")
        return None

    # Create the command accordingly
    ps2pdf_cmd = ["ps2pdf", "plot.ps", "plot.pdf"]
    if shutil.which("xvfb-run"):
        ps2pdf_cmd = ["xvfb-run", "-a", *ps2pdf_cmd]
    else:
        log.warning("xfbv-run not available.")

    # Convert 'plot.ps' to 'plot.pdf'
    subprocess.run(
        args=ps2pdf_cmd,
        cwd=wkdir,
    )

    # Remove 'plot.ps'
    subprocess.run(
        args=["rm", "plot.ps"],
        cwd=wkdir,
    )
