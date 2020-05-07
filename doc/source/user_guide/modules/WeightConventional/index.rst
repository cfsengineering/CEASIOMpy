.. figure:: ../../CEASIOMpy_square_weights.png
    :width: 180 px
    :align: right
    :alt: CEASIOMpy weights


WeightConventional
==================

:Categories: Weight, estimation

This module can estimate some of the main aircraft weights for a conventional aircraft.


Installation
------------

WeightConventional is a native |name| module, hence it is available and installed by default.


Analyses
--------

Weight conventional module for preliminary design of conventional aircraft evaluates:

* the maximum take-off mass
* the operating empty mass
* the zero fuel mass
* the maximum amount of fuel
* the maximum number of passengers
* the maximum amount of fuel with max passengers
* the number of crew members needed
* the number of lavatories
* the seating disposition

To do so, this software uses the main geometrical data of the aircraft, which are found automatically in the CPACS file:

* wing area
* wing span
* fuselage length
* fuselage width


Output
------

WeightConventional module generates and outputs CPACS file with all the calculated data, but you can also find these information in some text file saved in the ToolOutput folder of the module.


Required CPACS input and settings
---------------------------------

A lot of options can be set in the CPACS file or via SettingsGUI, but default value will be set in case you don't know these options.


Limitations
-----------

WeightConventional is based on interpolation base on existing aircraft, it will not be able to take into account if the aircraft you design uses new technologies or materials.


More information
----------------

* Master thesis about Weight & Balance modules [Picc19]_
