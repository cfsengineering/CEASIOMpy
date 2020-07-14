Getting started
===============

Once you finished the installation you could try to run the following test cases to familiarize yourself with |name|

Without RCE:
------------

If you want to use RCE to create your workflow, you can directly go to the next section.
If you cannot or do not want to install RCE on your computer, you can still use CEASIOMpy through the module 'WorkflowCreator'.


Test Case 1 : Simple workflow
*****************************

The module 'WorkflowCreator' can be found at /CEASIOMpy/ceasiompy/WorkflowCreator/workflowcreator.py you can run it by simply type in your terminal:

.. code::

    cd YourPath/CEASIOMpy/ceasiompy/WorkflowCreator/
    python workflowcreator.py -gui


.. hint::

    If you use a Linux you can easily set an alias in you .bashrc file to run these command with a shortcut of your choice.


When you run this module, a GUI will appear. The first thing to do is to chose the CPACS file we will use for this analysis, click on "Browse" and select "D150_simple.xml", it is a test aircraft similar to an A320 . Then, we will have the possibility to chose which module to run and in which order. For this first test case, we will use only the tab "Pre". On the left you will see the list of all available modules, when you select one you can add it to the list of module to execute. You can also remove module from this list or change the order with the buttons.
We will create a simple workflow with only three modules:

SettingsGUI -> WeightConventional -> Range.

.. figure:: getting_started_fig/TestCase1_WorkflowCreator.png
    :width: 400 px
    :align: center
    :alt: CEASIOMpy - WorkflowCreator - Test case 1

Once you added these three modules in order you can click "Save & Quit". The first module to run will be "SettingsGUI", it will show you all the available options for the next modules. All the options are pre-filled with default values. You don't need to change any value for this example, so you can just click "Save & Quit".
The two next modules will be executed automatically without showing anything except some results in the terminal.


Test Case 2 : Aerodynamic database with PyTornado
*************************************************

In this example we will see how to create an aerodynamic database with PyTornado and plot them on a graph.
As in test case 1, we will run 'WorkflowCreator'. In the GUI, after selecting the same D150_simple.xml CPACS file, we will select some modules in the list and place them in order to create the following workflow:

CPACSCreator -> SettingsGUI -> PyTornado -> PlotAeroCoefficients

.. figure:: getting_started_fig/TestCase2_WorkflowCreator.png
    :width: 400 px
    :align: center
    :alt: CEASIOMpy - WorkflowCreator - Test case 2

Then, you can click "Save & Quit". The first module to be executed will be CPACSCreator, with this module you can modify the geometry of the aircraft. We won't made changes now, but if you want to learn how to use CPACSCreator, you can follow the link bellow:

https://dlr-sc.github.io/tigl/doc/cpacscreator-0.1/tuto.html#tuto_create_from_scratch

If you apply some changes, save your modifications and close the CPACSCreator windows. Now, the SettingsGUI windows will appear, and first, we will import a new AeroMap.  Now, click on 'Import CSV' to add a new AeroMap, select 'Aeromap_4points_aoa.csv' and 'OK'.

.. figure:: getting_started_fig/TestCase2_ImportAeroMap.png
    :width: 400 px
    :align: center
    :alt: CEASIOMpy - Import AeroMap - Test case 2

You can also click on the 'aeromap_empty' and delete it with the buttons. You must click on the button 'Update' to make the new AeroMap available for all modules.

Now, you can click on the 'PyTornado' Tab, the AeroMap selected should be the one you imported before. We will not change the other option and just click 'Save & Quit'.

The software should run for a few seconds and when the calculation are done, a plot of the aerodynamic coefficient should appear.


Test Case 3 : SU2 at fixed CL and Range
***************************************

For this test case you can try to run the following workflow with the same aircraft. It will calculate the after performing a CFD analysis at fixed CL.

SettingsGUI -> WeightConventional -> CLCalculator -> CPACS2SUMO -> SUMOAutoMesh -> SU2Run -> SkinFriction -> Range


Test Case 4 : Optimising the CL
*******************************

When launching an optimisation routine, enter the desired parameter that you want to optimise in the "optim_var" variable.

.. code::

    optim_var = 'cl'

Then select the modules you want to be run in the routine, for example :

.. code::

    module_optim = ['WeightConventional', 'CPACS2SUMO','SUMOAutoMesh', 'SU2Run', 'SkinFriction']

The optimisation will create a new directory in the WKDIR folder and each iteration result (CPACS file + problem variables) will be saved in the Optimisation module.


Test Case 5 : Surrogate model for SU2
*************************************

TODO


With RCE:
---------

To run the following workflow you need to have a running version of RCE with the CEASIOMpy module installed. For more information check out the Step 3 of the installation page.

Test Case 1 : Simple workflow
*****************************

We will create a simple workflow which contains a CPACS input and three modules.

CPACS input -> SettingsGUI -> WeightConventional -> Range

Your workflow should look like that:

.. figure:: CEASIOMpy_RCE_TC1.png
    :width: 630 px
    :align: center
    :alt: CEASIOMpy - RCE - Test case 1


Test Case 2 : Aerodynamic database with PyTornado
*************************************************

CPACS input -> CPACSCreator -> PyTornado -> SkinFriction -> PlotAeroCoefficients


Test Case 3 : SU2 at fixed CL and Range
***************************************

CPACS input -> SettingsGUI -> WeightConventional -> CLCalculator -> CPACS2SUMO -> SUMOAutoMesh -> SU2Run -> SkinFriction -> Range


Module compatibility
--------------------

Visualization of which module can be connected to which other modules:

in development...
