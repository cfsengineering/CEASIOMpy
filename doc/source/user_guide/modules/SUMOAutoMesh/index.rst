.. figure:: ../../CEASIOMpy_square_geometry.png
    :width: 180 px
    :align: right
    :alt: CEASIOMpy aerodynamics


SUMOAutoMesh
============

:Categories: Geometry, meshing

SUMOAutoMesh generate automatically a SU2_ mesh from a SUMO_ SMX file.

.. warning::

    This module do not work on MacOS for now, because SUMO cannot be run in batch as on Linux. If you place this module in a workflow anyway, it will just open SUMO in GUI.


Installation
------------

SUMOAutoMesh is a native |name| module, hence it is available and installed by default. The main module of SUMOAutoMesh can be found in /CEASIOMpy/ceasiompy/SUMOAutoMesh/sumoautomesh.py

Analyses
--------

SUMOAutoMesh do automatically operation that can also be done with SUMO with GUI. That is to say, creating the surface mesh and then using Tetgen to create the volume mesh.

.. figure:: sumo_fig.png
    :width: 500 px
    :align: center
    :alt: SUMO in GUI version


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
