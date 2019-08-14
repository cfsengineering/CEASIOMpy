ceasiompy.SU2Config
===================

Required CPACS input paths
--------------------------


Reference length of the aircraft
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

* **CPACS path** /cpacs/vehicles/aircraft/model/reference/length
* **Default value** None
* **Unit** m
* **Variable name** ref_len

Reference area of the aircraft
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

* **CPACS path** /cpacs/vehicles/aircraft/model/reference/area
* **Default value** None
* **Unit** m^2
* **Variable name** ref_area

Aircraft cruise altitude
~~~~~~~~~~~~~~~~~~~~~~~~

* **CPACS path** /cpacs/toolspecific/CEASIOMpy/aerodynamics/su2/cruise_alt
* **Default value** 12000
* **Unit** m
* **Variable name** cruise_alt

Aircraft cruise Mach number
~~~~~~~~~~~~~~~~~~~~~~~~~~~

* **CPACS path** /cpacs/toolspecific/CEASIOMpy/aerodynamics/su2/cruise_mach
* **Default value** 0.78
* **Unit** 1
* **Variable name** cruise_mach

Value of CL to achieve to have a level flight with the given conditions
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

* **CPACS path** /cpacs/toolspecific/CEASIOMpy/aerodynamics/su2/targetCL
* **Default value** 1.0
* **Unit** 1
* **Variable name** target_cl

FIXED_CL_MODE parameter for SU2
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

* **CPACS path** /cpacs/toolspecific/CEASIOMpy/aerodynamics/su2/fixedCL
* **Default value** YES
* **Unit** -
* **Variable name** fixed_cl

Maximum number of iterations performed by SU2
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

* **CPACS path** /cpacs/toolspecific/CEASIOMpy/aerodynamics/su2/maxIter
* **Default value** 10
* **Unit** -
* **Variable name** max_iter

CPACS output paths
------------------


**ceasiompy.SU2Config does not write anything back to CPACS** 
