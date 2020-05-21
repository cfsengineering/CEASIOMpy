Getting started
===============

Once you finished the installation you could try to run the following test cases to to familiarize yourself with |name|

Without RCE:
------------

If you want to use RCE to create your workflow, you can directly go to the next section.
If you cannot of do not want to install RCE on your computer, you can still use CEASIOMpy through the module 'WorkflowCreator'.


Test Case 1 : Simple workflow
*****************************

The module 'WorkflowCreator' can be found at /CEASIOMpy/ceasiompy/WorkflowCreator/workflowcreator.py you can run it by simply type in your terminal:

.. code::

    cd YourPath/CEASIOMpy/ceasiompy/WorkflowCreator/
    python workflowcreator.py -gui


When you run this module, a GUI will appear. The first thing to do is to chose the CPACS file we want to use for this workflow. Then, we will have the possibility to chose which module to run and in which order. For this first test case, we will use only the tab "Pre". On the left you will see the list of all available modules, when you select one you can add it to the list of module do execute. You can also remove module from this list or change the order with the buttons.
We will create simple workflow with only three modules: SettingsGUI -> WeightConventional -> Range. Once you added these three modules in order you can click "Save & Quit".

The first module to run will be "SettingsGUI", it will show you all the available options for the next modules. All the options are pre-filled with default values. You don't need to change any value for this example, so you can just click "Save & Quit".
The two next modules will be execute automatically without showing anything except some results in the terminal.


Test Case 2 : Aerodynamic database with PyTornado
*************************************************

In this example we will see how to create an aerodynamic database with PyTornado and plot the polar graph. As in test case 1, we will run workflowcreator. In the GUI we will select some modules in the list and place them in this order to create the following workflow:

CPACS_input.xml -> CPACSCreator -> PyTornado -> SkinFriction -> PlotAeroCoefficients



Test Case 3 : ...
*****************

WeightConventional -> CLCalculator -> CPACS2SUMO -> SUMOAutoMesh -> Range


Test Case 4 : Optimising the CL
*******************************

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
*****************

Same case than without RCE

TODO: add picture or video of workflow creation


Test Case 2 : ...
*****************

TODO: CPACS_input.xml -> CPACSCreator -> PyTornado -> SkinFriction -> PlotAeroCoefficients




Module compatibility
--------------------

TODO: Table of or something to visualize which module can be connected to which other modules
