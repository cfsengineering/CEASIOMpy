CPACS2SUMO
==========

:Categories: Geometry, meshing

CPACS2SUMO converts CPACS_ XML file into SUMO_ SMX file.

TODO: add figure

Installation
------------

CPACS2SUMO is a native |name| module, hence it is available and installed by default. The main module of CPACS2SUMO can be found in /CEASIOMpy/ceasiompy/CPACS2SUMO/cpacs2sumo.py

Analyses
--------

CPACS2SUMO use the geometric parameters of a CPACS_ aircraft and convert them into the SUMO_ format

Output
------

CPACS2SUMO outputs a new file called 'ToolOutput.smx', this file is saved in the ToolOutput directory. If the module is used in a workflow it will also be saved in the WKDIR to be used by the module SUMOAutoMesh further in the process.

Required CPACS input and settings
---------------------------------

Inputs will be read automatically in the CPCAS file.

Limitations
-----------

It is possible to create some special geometries with the CPACS_ format which are not compatible with SUMO. This is mainly due to the multiple possible transformation on sections (translation,scaling,rotation).
Also the interpolation of surfaces between existing sections may differ. You should always check the SUMO file when it is the first time you convert it.

More information
----------------

* https://cpacs.de/pages/documentation.html
* https://www.larosterna.com/products/open-source
