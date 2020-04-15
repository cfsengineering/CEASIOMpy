StabilityDynamic
================

:Categories: Mission analysis, Stability

This module is made to check the dynamic stability of an aircraft and how it is able to handle the different modes (phughoid, short period, spiral, dutch roll).

Installation
------------

StabilityDynamic is a native |name| module, hence it is available and installed by default.

Analyses
--------

StabilityDynamic check dynamic stabilities in the tree main directions: longitudinal, lateral and directional.

Output
------

A lot of graph are produce and saved in /ToolOutput.

Required CPACS input and settings
---------------------------------

The CPACS must contains an aeroMap with: (to complete)
* angle of angle of attack
* angle of sideslip
* damping derivatives
* control surface deflections


Limitations
-----------

.. warning::

    StabilityDynamic is not complete and has not been completely tested. It is more a developement version.

.. warning::

    Notation used and sign conventions should be checked very carefully, there are a lot of different notations. The one use in this modules comes from a book and my differ from the CPACS notation.


More information
----------------

* Loïc thesis link ...
* Link to book ...
