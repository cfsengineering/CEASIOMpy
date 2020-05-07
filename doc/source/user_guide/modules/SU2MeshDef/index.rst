.. figure:: ../../CEASIOMpy_square_geometry.png
    :width: 180 px
    :align: right
    :alt: CEASIOMpy aerodynamics


SU2MeshDef
==========

:Categories: Mesh deformation, Control surfaces, CFD

SU2 is a CFD code develop by Stanford University. It is also possible to use it to deform Euler unstructured meshes with FFD box and spring analogy. This module can be use to generate new meshes with deflected control surfaces from CPACS file information.


Installation
------------

You must install SU2 on your computer to use the SU2MeshDef module. You can find SU2 for different OS (Windows, Mac, Linus) at the following link: https://su2code.github.io/download.html

Analyses
--------

The module SU2MeshDef get the control surface (Trailing Edge Device) definition from the CPACS file. Then, it creates the corresponding configuration file which allows to generate the new meshes and it runs the "SU2_DEF" routine for all the meshes.

Output
------

New SU2 meshes with deflected control surfaces or other mesh deformation will be save in the Woking directory (WKDIR) in the folder "MESH". This list of available meshes will be saved in the CPACS file.

Required CPACS input and settings
---------------------------------

To create meshes with control surface deflections, those control surface must be correctly define in the CPACS file.

Limitations
-----------

.. warning::

    The FFD box mesh deformation should be use for small deformations, as it strongly deformed the mesh cells it could become difficult to have a converge results on these meshes.


More information
----------------

* **SU2 website** https://su2code.github.io/
* **SU2 on Github** https://github.com/su2code/SU2
* **Trailing Edge Device definition in CPACS** https://www.cpacs.de/documentation/CPACS_3_1_0_Docs/html/36847287-7fc5-f9b4-0d1f-0652cf2eaadc.htm
