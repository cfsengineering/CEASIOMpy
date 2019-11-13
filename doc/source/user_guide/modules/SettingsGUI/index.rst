SettingsGUI
===========

:Categories: Settings, GUI

The *SettingsGUI* provides a simple graphical user interface (GUI) to define settings for each module in a |name| workflow. The SettingsGUI is usually run as the first module in a |name| workflow.

.. figure:: main.png
    :width: 400 px
    :align: center
    :alt: SettingsGUI

    SettingsGUI interface

Installation
------------

*SettingsGUI* is installed by default with the |name| installation.


Analyses
--------

*SettingsGUI* does not perform any analyses. However, it will use information contain in all the __specs__ file to create one tab per module. The user can filled all the inputs and when the button "Save & Quit" is push, all the data will be save at the correct place in the CPACS file.
It can also be used to manage the aeroMaps contained in the CPACS file.

Output
------

The input CPACS_ file will be updated according to the settings in the GUI.


Required CPACS input and settings
---------------------------------

No specific CPACS input is required to run the SettingsGUI editor.

..
    Limitations
    -----------

    TODO

..
    More information
    ----------------

    TODO
