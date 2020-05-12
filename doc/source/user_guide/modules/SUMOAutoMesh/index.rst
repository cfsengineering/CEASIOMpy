.. figure:: ../../CEASIOMpy_square_geometry.png
    :width: 180 px
    :align: right
    :alt: CEASIOMpy aerodynamics


SUMOAutoMesh
============

:Categories: Geometry, meshing

SUMOAutoMesh gererate automatically a SU2_ mesh from a SUMO_ SMX file.

TODO: add figure

Installation
------------

SUMOAutoMesh is a native |name| module, hence it is available and installed by default. The main module of SUMOAutoMesh can be found in /CEASIOMpy/ceasiompy/SUMOAutoMesh/sumoautomesh.py

Analyses
--------

SUMOAutoMesh ..

Output
------

SUMOAutoMesh outputs a new file called 'ToolOutput.su2', this file is saved in the ToolOutput directory. If the module is used in a workflow it will also be saved in the WKDIR to be used by the other modules further in the process.

Required CPACS input and settings
---------------------------------

??Inputs will be read automatically in the CPCAS file.

Limitations
-----------

Sometimes the mesh can not be created because of an error in the geometry. In this case, the best is to open SUMO_ and try to create a mesh manually and see where the problem comes from.

More information
----------------

* https://www.larosterna.com/products/open-source
* http://wias-berlin.de/software/index.jsp?id=TetGen&lang=1
* https://su2code.github.io/docs_v7/Mesh-File/
