ceasiompy.CLCalculator
======================

Required CPACS input paths
--------------------------


MTOM (maybe another mass shoud be used, more representative for cruise mass?)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

* **CPACS path** /cpacs/vehicles/aircraft/model/analyses/massBreakdown/designMasses/mTOM/mass
* **Default value** None
* **Unit** kg
* **Variable name** mtom

Cruise speed
~~~~~~~~~~~~

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

Load Factor
~~~~~~~~~~~

* **CPACS path** /cpacs/toolspecific/CEASIOMpy/ranges/loadFactor
* **Default value** 1.05
* **Unit** 1
* **Variable name** load_fact

Reference area
~~~~~~~~~~~~~~

* **CPACS path** /cpacs/vehicles/aircraft/model/reference/area
* **Default value** None
* **Unit** m^2
* **Variable name** ref_area
CPACS output paths
------------------


**ceasiompy.CLCalculator does not write anything back to CPACS** 
