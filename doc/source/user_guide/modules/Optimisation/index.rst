Optimisation
==============

:Categories: Optimisation module

This module launches a loop with a workflow routine and an optimiser based on the Openmdao library.

Installation
------------

The optimisation module is a native |name| module, hence it is available and installed by default.

Analyses
--------

The optimisation module enhances the design of the plane to find an optimum for a user-specified parameter, given a list of design variables and constrains.

Output
------

Optimisation module outputs nothing (directly).

Required CPACS input and settings
---------------------------------

 * No CPACS inputs required as it only launches a workflow routine
 * Optimiser parameters : Including the design variables, the target parameter and the constrains.

Limitations
-----------

 * The geometric modification of the fuselage is not available for now.

More information
----------------

* https://openmdao.org/
