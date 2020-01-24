Getting started
===============

Once you finished the installation you could try to run the following test cases to to familiarize yourself with |name|

Without RCE:
------------

If you cannot of do not want to install RCE on your computer, you can still use CEASIOMpy through the module 'WorkflowCreator'.

The module 'WorkflowCreator' can be found at /CEASIOMpy/ceasiompy/WorkflowCreator/workflowcreator.py
You can open it and modify the list 'module_pre', which is the list of module to execute before to run an optimization, in this fist case will will disable the optimization for now, so these modules will be the only ones to be executed. You can write:

.. code::

    module_pre = ['SettingsGUI','WeightConventional','Range']

In this example three modules will be executed, in order, first 'SettingsGUI' which is a user interface to set options of oder modules, then 'WeightConventional' which estimates masses of a conventionl aircraft and finally estimates 'Range' the rage of the aircraft for different flight configurations.



Test Case 1 : Simple workflow
*****************************


TODO: somthing like: Input -> WeightConventional -> Range


Test Case 2 : ...
*****************************

TODO


Test Case 3 : ...
*****************************


TODO


With RCE:
---------



Module compatibility
--------------------

TODO: Table of or something to visualize which module can be connected to which other modules
