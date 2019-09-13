CPACS2SUMO
==========

ModuleTemplate
==============

:Categories: Geometry, meshing

CPACS2SUMO converts CPACS XML file into SUMO SMX file.

#.. figure:: https://upload.wikimedia.org/wikipedia/commons/9/96/Spirit_of_St._Louis.jpg
#    :width: 300 px
#    :align: center
#    :alt: Example

TODO: add picture

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

Some special geometry are possible with CPACS but not with SUMO. This is mainly due to the multible possible tranfomation on section (translation,scaling,rotation).
Also the interpolation of surfaces between existing sections may differ. You sould always check the SUMO file when it is the first time you convert it.

More information
----------------

* https://cpacs.de/pages/documentation.html
* https://www.larosterna.com/products/open-source
