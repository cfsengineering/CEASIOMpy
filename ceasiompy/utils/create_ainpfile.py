"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by Airinnova AB, Stockholm, Sweden

Module to run M-Edge Calculation in CEASIOMpy
Create M-Edge ainp file from template

Python version: >=3.8

| Author : Mengmeng Zhang
| Creation: 2024-01-05

TODO:



"""

# =================================================================================================
#   IMPORTS
# =================================================================================================

import re
from ceasiompy.EdgeRun.func.edgeutils import get_edge_ainp_template

# =================================================================================================
#   CLASSES
# =================================================================================================


class CreateAinp:
    def __init__(self):
        self.template_file = get_edge_ainp_template()

    def _write_file(self, content, output_file_withpath):
        # output_file_path = os.path.join(output_folder, 'Edge.ainp')
        with open(output_file_withpath, "w") as f:
            f.write(content)

    def create_ainp(
        self,
        UFREE,
        VFREE,
        WFREE,
        TFREE,
        PFREE,
        SREF,
        CREF,
        BREF,
        IXMP,
        IDCLP,
        IDCDP,
        IDCCP,
        IDCMP,
        IDCNP,
        IDCRP,
        NPART,
        ITMAX,
        INSEUL,
        NGRID,
        CFL,
        output_folder,
    ):
        # template_file_path = get_edge_ainp_template()
        with open(self.template_file, "r") as f:
            template_content = f.read()

        # Define a dictionary for keyword-value pairs
        replacements = {
            "__UFREE__": str(UFREE),
            "__VFREE__": str(VFREE),
            "__WFREE__": str(WFREE),
            "__TFREE__": str(TFREE),
            "__PFREE__": str(PFREE),
            "__SREF__": str(SREF),
            "__CREF__": str(CREF),
            "__BREF__": str(BREF),
            "__IXMP__": f"{IXMP[0]} {IXMP[1]} {IXMP[2]}",
            "__IDCLP__": IDCLP,
            "__IDCDP__": IDCDP,
            "__IDCCP__": IDCCP,
            "__IDCMP__": IDCMP,
            "__IDCNP__": IDCNP,
            "__IDCRP__": IDCRP,
            "__NPART__": str(NPART),
            "__ITMAX__": str(ITMAX),
            "__INSEUL__": str(INSEUL),
            "__NGRID__": str(NGRID),
            "__CFL__": str(CFL),
        }

        # Use regular expression to replace keywords with their corresponding values
        edge_content = template_content
        for keyword, value in replacements.items():
            edge_content = re.sub(re.escape(keyword), value, edge_content)

        self._write_file(edge_content, output_folder)
