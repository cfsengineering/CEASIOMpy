SU2Config
=========

:Categories: CFD, Configuration

SU2Config generates SU2 configuration files from data in a CPACS file.


Installation
------------

SU2Config will be install automatically with the installation of CEASIOMpy, no further action required. This module can be used even if SU2 is not install on your computer as it just generates the configuration files for SU2.

Analyses
--------

A `default configuration file <https://github.com/cfsengineering/CEASIOMpy/blob/installer/ceasiompy/SU2Config/files/DefaultConfig_v6.cfg>`_ is used and modified with the information found in the CPACS_ file.


Output
------

SU2Config will generates a folder structure with one configuration file for each case.

TODO: add figure of the folder structure


Required CPACS input and settings
---------------------------------

Some data will be found in the CPACS_ file and the missing ones could be ask to the user via the SettingsGUI module.
An AeroMap has to be selected to define which fight state configuration will be created.

Limitations
-----------

SU2Config has not found its limits yet!


More information
----------------

* https://su2code.github.io/docs/Configuration-File/
