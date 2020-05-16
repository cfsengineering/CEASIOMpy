.. image:: logo.svg
    :target: https://aeroframe.readthedocs.io/
    :width: 200 px
    :align: right
    :alt: Logo

AeroFrame
=========

:Categories: FSI, Aeroelasticity, Aerodynamics, CFD, Structures

*AeroFrame* is a modular framework for partitioned aeroelastic analyses. The framework couples separate solvers for structure and CFD. It coordinates the analysis and the exchange of loads and deformations. Currently, AeroFrame supports *static* aeroelastic analyses.

.. figure:: main.png
    :width: 500 px
    :align: center
    :target: https://aeroframe.readthedocs.io/
    :alt: AeroFrame example

    Wing deformations in a pull-up maneuver. In the shown case, aerodynamics were computed with the vortex-lattice method (VLM) and the structural response with a beam FEM model (image from [Dett19]_).


.. warning::

    This module is in development, it will probably not work correctly if you use it in a workflow.


Installation
------------

The AeroFrame library is installed *automatically* as an external dependency of |name|.

.. seealso::

    AeroFrame documentation: https://aeroframe.readthedocs.io/

Analyses
--------

AeroFrame currently supports *static* aeroelastic analyses. Quasi-static wing deformations in quasi-steady flight manoeuvres can be computed. Such flight-states may be present during *steady climbs* and *descents*, *pull-up manoeuvres* or *steady turns*. AeroFrame has also been used to analyse static stability problems, namely *divergence* and *control reversal*. More details can be found in [Dett19]_ and in the AeroFrame documentation.

Output
------

Not yet defined.

Required CPACS input and settings
---------------------------------

Not yet defined.

Limitations
-----------

.. warning::

    AeroFrame couples a CFD and a structure solver. However, the CFD model and the structure model have to be provided. Methods for automatic sizing of structure models based on beam FEM models are in planning.

.. warning::

    AeroFrame does currently only exchange data for *static* aeroelastic analyses. Extensions for *dynamic* analyses which requires handling of *time*-related data are in planning.

Contributions to the AeroFrame framework are highly welcomed.

More information
----------------

* **Documentation** https://aeroframe.readthedocs.io/
* **Github** https://github.com/airinnova/aeroframe
