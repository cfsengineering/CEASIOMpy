lib.SkinFriction
================

Required CPACS input paths
--------------------------


Wetted area of the aircraft (calculated by SU2)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

* **CPACS path** /cpacs/toolspecific/CEASIOMpy/geometry/analysis/wettedArea
* **Default value** None
* **Unit** m^2
* **Variable name** wetted_area

Aircraft cruise speed
~~~~~~~~~~~~~~~~~~~~~

* **CPACS path** /cpacs/toolspecific/CEASIOMpy/ranges/cruiseSpeed
* **Default value** 272
* **Unit** m/s
* **Variable name** cruise_speed

Aircraft cruise altitude
~~~~~~~~~~~~~~~~~~~~~~~~

* **CPACS path** /cpacs/toolspecific/CEASIOMpy/ranges/cruiseAltitude
* **Default value** 12000
* **Unit** m
* **Variable name** cruise_alt
CPACS output paths
------------------


Skin friction drag coefficient
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

* **CPACS path** /cpacs/toolspecific/CEASIOMpy/aerodynamics/su2/cd0
* **Default value** None
* **Unit** 1
* **Variable name** cd0
