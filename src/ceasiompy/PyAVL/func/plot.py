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
    if not Path(wkdir, "plot.ps").exists():
        log.warning("File 'plot.ps' does not exist. Nothing to convert.")
        return

    ps2pdf_cmd = ["ps2pdf", "plot.ps", "plot.pdf"]
    xvfb_run = shutil.which("xvfb-run")
    if xvfb_run:
        log.info(f'XVFB at {xvfb_run=}')
        ps2pdf_cmd = ["xvfb-run", "-a", *ps2pdf_cmd]
    else:
        log.warning(f"{xvfb_run=} not available.")

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
