Installation
============

General requirements
--------------------

The following packages are required to be able to use |name|

* Python 3.6 or higer
* `Tixi`_ and `Tigl`_ libraries
* `RCE`_ environment

TODO: *Currently, we recommend the use of Anaconda to simplify the installation of TIXI and TIGL libraries*

Optional requirements
---------------------

The following packages are not required to run all |name| workflows, it is still recommended to have them in order to use the all |name| suite.

* PyTornado: https://github.com/airinnova/pytornado
* SUMO: https://www.larosterna.com/products/open-source
* SU2: https://su2code.github.io/download.html


Setting up your path variables
------------------------------

To use core |name| you just have to download or clone the repository in a directory of your choice. Then, you may have to add this directory to your environment variable `PYTHONPATH`.

**Windows**

If use Windows, you have to add the following line, in your `autoexec.bat` file.

.. code::

    set PYTHONPATH=%PYTHONPATH%;\InstalDir\CEASIOMpy

Alternatively, you can edit the system variable through the *System Properties* (My Computer > Properties > Advanced System Settings > Environment Variables).

**MacOS**

TODO: *add PYTHONPATH procedure for MacOS*

**Linux**

If you run `RCE`_ from *BASH* you have to add the following line, in your `.bashrc` file

.. code::

    export PYTHONPATH="$PYTHONPATH: /InstalDir/CEASIOMpy/"

If you use *TCSH* you have to add the following line, in your `.tcshrc` file

.. code::

    setenv PYTHONPATH ${PYTHONPATH}: /InstalDir/CEASIOMpy/


Setting up RCE module
---------------------

TODO: *adding module (.json file) in /.rce/default/integration/tools/common/ and changing path ...*
