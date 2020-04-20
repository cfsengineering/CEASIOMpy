Getting started
===============

Once you finished the installation you could try to run the following test cases to to familiarize yourself with |name|

Without RCE:
------------

If you want to use RCE to create your workflow, you can directly go to the next section.
If you cannot of do not want to install RCE on your computer, you can still use CEASIOMpy through the module 'WorkflowCreator'.


Test Case 1 : Simple workflow
*****************************

The module 'WorkflowCreator' can be found at /CEASIOMpy/ceasiompy/WorkflowCreator/workflowcreator.py
You can open it and modify the list 'module_pre', which is the list of modules to execute before running an optimization, in this fist case we will disable the optimization for now, so these modules will be the only ones to be executed. You can write:

.. code::

    module_pre = ['WeightConventional','Range']

In this example two modules will be executed, in order, first 'WeightConventional' which estimates masses of a conventional aircraft and 'Range' which estimates the range of the aircraft for different flight configurations. Each module input and output a CPACS file, all the data should be read and written into this CPACS file during the process.



Test Case 2 : Aerodynamic database with PyTornado
*************************************************

In this example we will see how to create an aerodynamic database with PyTornado and plot it by using the following workflow:

CPACS_input.xml -> CPACSCreator -> PyTornado -> SkinFriction -> PlotAeroCoefficients

.. code::

    module_pre = ['CPACSCreator','PyTornado','SkinFriction','PlotAeroCoefficients']


Then you can run the WorkflowCreator module.


Test Case 3 : ...
*****************************

WeightConventional -> CLCalculator -> CPACS2SUMO -> SUMOAutoMesh -> Range


Test Case 4 : Optimising the CL
*****************************

When launching an optimisation routine, enter the desired parameter that you want to optimise in the "optim_var" variable.
.. code::
    optim_var = 'cl'

Then select the modules you want to be run in the routine, for example :

.. code::
    module_optim = ['WeightConventional', 'CPACS2SUMO','SUMOAutoMesh', 'SU2Run', 'SkinFriction']
    
The optimisation will create a new directory in the WKDIR folder and each iteration result (CPACS file + problem variables) will be saved in the Optimisation module.


With RCE:
---------

Test Case 1 : ...
*****************************

Same case than without RCE

TODO: add picture or video of workflow creation


Test Case 2 : ...
*****************************

TODO: CPACS_input.xml -> CPACSCreator -> PyTornado -> SkinFriction -> PlotAeroCoefficients




Module compatibility
--------------------

TODO: Table of or something to visualize which module can be connected to which other modules
