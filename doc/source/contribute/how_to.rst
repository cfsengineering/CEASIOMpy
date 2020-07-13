How to contribute to |name|
===========================

We highly encourage and appreciate any contributions to |name|.

Reporting bugs
--------------

* See `Github_BugReport`_


Writing a new module
--------------------

* First, you should check the code guidelines

* Fork the CEASIOMpy repository on you own Github account

* On your own fork you can now (on your Master branch or another one)

* Copy the module named " ModuleTemplate"

* Rename it as you want

* Write you python module and all the functions it needs to run

* If you use a lot of subfunctions, use the the folder /func to store them

* If your module needs some external file to run (template, configuration file, etc.) put them in the folder /files

* Write its ``__specs__.py`` file, which describes its input/output and RCE integration

* Make all the required tests and validations to be sure the your module outputs the expected results

* Write its test functions, as example you can check: /ceasiompy/test/TestModuleTemplate/

* Write its documentation page, as example you can check: /ceasiompy/doc/source/user_guide/modules/ModuleTemplate/

* Create a "New pull request" to integrate all your changes in the CEASIOMpy main branch


This is what the folder structure of a modules typically looks like:

.. figure:: Modules_dirs.png
    :width: 600 px
    :align: center
    :alt: Module folder structure
