CPACS2SUMO
==========

ModuleTemplate
==============

:Categories: Geometry, meshing

CPACS2SUMO converts CPACS XML file into SUMO SMX file.

TODO: add figure

Installation
------------

ModuleTemplate is a native |name| module, hence it is available and installed by default.

Analyses
--------

ModuleTemplate computes nothing.

Output
------

ModuleTemplate outputs a new file called `ToolOutput.smx.

Required CPACS input and settings
---------------------------------

Inputs will be read automatically in the CPCAS file.

Limitations
-----------

Some special geometries are possible with CPACS but not with SUMO. This is mainly due to the multible possible tranfomation on section (translation,scaling,rotation).
Also the interpolation of surfaces between existing sections may differ. You should always check the SUMO file when it is the first time you convert it.

More information
----------------

* https://cpacs.de/pages/documentation.html
* https://www.larosterna.com/products/open-source
