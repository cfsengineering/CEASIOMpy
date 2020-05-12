.. figure:: ../../CEASIOMpy_square_geometry.png
    :width: 180 px
    :align: right
    :alt: CEASIOMpy aerodynamics


CPACSCreator
============

:Categories: CPACS, Aircraft modeling, CAO

This module is just a launcher for CPACSCrator_ [Drou18]_.

.. figure:: https://dlr-sc.github.io/tigl/doc/cpacscreator-0.1/tuto_scratch_23.png
    :width: 600 px
    :align: center
    :alt: Example

    CPACSCrator_ can be use to create or modify existing CPACS_ file aircraft.

Installation
------------

If you use the Conda installation as describes in the installation procedure. CPACSCreator_ will be install automatically in your Conda environment. If not, you can follow the procedure: https://dlr-sc.github.io/tigl/doc/cpacscreator-0.1/tigl_installation.html


Analyses
--------

CPACSCreator computes nothing, however it allows you to create an aircraft from scratch or modifying an existing one.

https://dlr-sc.github.io/tigl/doc/cpacscreator-0.1/tuto.html#tuto_create_from_scratch


Output
------

A CPACS file with all your modifications will be created in the ToolOutput folder. Do not forget to save the aircraft before you close CPACSCreator.


Required CPACS input and settings
---------------------------------

No CPACS input is required.


Limitations
-----------

Some special shape could be difficult to model due to some constraints inherent to the CPACS_ format.


More information
----------------

* https://dlr-sc.github.io/tigl/doc/cpacscreator-0.1/index.html
* Master thesis about CPACSCreator [Drou18]_
