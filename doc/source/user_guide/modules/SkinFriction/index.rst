SkinFriction
============

:Categories: Aerodynamic, drag, empirical

This module adds skin friction drag to an Aeromap calculated without it.


Installation
------------

SkinFriction is a native |name| module, hence it is available and installed by default. The main module of SkinFriction can be found in /CEASIOMpy/ceasiompy/SkinFriction/skinfriction.py.


Analyses
--------

The aerodynamic coefficients calculated with pyTornado or Euler methods (SU2) do not depend on atmospheric parameters and do not include the skin friction drag. It means that for different altitudes as input you will get the same aerodynamic coefficients. Furthermore, the drag calculated with these methods is generally underestimated. You can use this module to estimate the skin friction drag from empirical formula and add it to the selected aeroMap.

The formula used to estimate the skin friction drag is from the paper "Rapid Estimation of the Zero-Lift Drag Coefficient of Transport Aircraft" by Gerard W. H. van Es


With the Wetted aera :math:`S_{wet}`, the span :math:`b`, the aircraft velocity :math:`V` and kinematic viscosity :math:`\nu` we can calculate the Reynolds number:

.. math::

   Re = (S_{wet}/b) \cdot V / \nu

We can now compute the skin friction coefficient from the linear regression found in the paper:

.. math::

   C_{fe} = 0.00258 + 0.00102 \cdot exp(-6.28\cdot10^{-9} \cdot Re) + 0.00295 \cdot exp(-2.01 \cdot 10^{-8} \cdot Re)


And finally, we can calculate the zero-lift drag coefficient with the following formula:

.. math::

   C_{D0} = C_{fe} \cdot S_{wet} / S

Then, this coefficient is added to the drag coefficient Cd already calculated.


Output
------

The output of this module is a CPACS with a new aeroMap which include skin friction drag.


Required CPACS input and settings
---------------------------------

To use the SkinFriction module you will need the wetted area of the aircraft (:math:`S_{wet}`). For now, the only way to calculate it is by using SU2. When SU2 reads the mesh it will calculate the wetted area from it and this value is automatically saved in the CPACS file. If you never ran the SU2 module with this aircraft you can also set this value manually (or through the SettingsGUI) but it could be a bit difficult to know this value, except if you know it from a different source.



Limitations
-----------

This module only uses empirical formula to approximate the skin friction drag, it does not take into account the exact form of the aircraft or the surface roughness.

The equation used above should be valid in the following ranges of values:

:math:`Re (based \, on \, Swet=b):  35-390 \cdot 10^6`

:math:`S_{wet}: 120-3400 \:  m^2`

:math:`S_{ref}: 20-580 \:  m^2`

:math:`b: 10–68 \: m`



More information
----------------

* Gerard W. H. van Es.  "Rapid Estimation of the Zero-Lift Drag Coefficient of Transport Aircraft", Journal of Aircraft, Vol. 39, No. 4 (2002), pp. 597-599. https://doi.org/10.2514/2.2997
