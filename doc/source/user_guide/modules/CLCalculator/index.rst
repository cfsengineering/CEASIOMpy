CLCalculator
============

:Categories: Aerodynamics, Cruise flight

Installation
------------

CLCalculator will be install automatically with the installation of CEASIOMpy, no further action required.


Analyses
--------

CLCalculator determine the Lift coefficient :math:`C_L` required to fly with the set of following conditions:

    * Mass of the aircraft: :math:`M [kg]`
    * Mach number: :math:`Ma [-]`
    * Load Factor: :math:`LF [-]`
    * Reference surface area: :math:`S_{ref} [m^2]`
    * Static pressure: :math:`P_S [Pa]`
    * Acceleration of gravity: :math:`g [m/s^2]`

In CEASIOMpy :math:`P_S` and  :math:`g` can be obtained from the altitude value by using the standard atmosphere function.


The Lift force of an aircraft is given by:

.. math::

   L = \frac{1}{2} \cdot q \cdot S_{ref} \cdot C_L

Dynamic pressure can be calculated as:

.. math::

   q = \frac{1}{2} \cdot \gamma \cdot P_s \cdot M^2


and we know the lift force must be compensate the weight of the aircraft (time the load factor), so :math:`L=M \cdot g \cdot LF`. With the first equation, we obtain:

.. math::

    C_L = \frac{M \cdot g \cdot LF}{q \cdot S_{ref}}


Output
------

The output of CLCalculator will be the target CL value to achieve, SU2 can use this value as input to make a fixed CL calculation where the angle of attack will be varied to find the correct CL.


Required CPACS input and settings
---------------------------------

Some inputs will be read automatically in the CPCAS file, other could be enter via the SettingsGUI module.

Limitations
-----------

This calculation take into account only on mass (MTOM) which is not representative of the mass of the aircraft during all the flight which will vary a lot.

More information
----------------

* https://en.wikipedia.org/wiki/Lift_coefficient
