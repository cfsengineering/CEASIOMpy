Installation
============

Gereral requirements
--------------------

The following packages are required to be able to use |name|

* `Tigl`_ and `Tixi`_
* `RCE`_

TODO: *Currently, we recommend the use of Anaconda...*

Optional requirements
---------------------

TODO: *Note about optional requirements, PyTornado, SU2, etc...*

Setting up your path variables
------------------------------

To use core |name| you just have to download or clone the repository in a directory of your choice. Then, you may have to add this directory to your environment variable `PYTHONPATH`.

**Windows**

If use Windows, you have to add the following line, in your `autoexec.bat` file.

.. code::

    set PYTHONPATH=%PYTHONPATH%;\InstalDir\CEASIOMpy

Alternatively, you can edit the system variable through the *System Properties* (My Computer > Properties > Advanced System Settings > Environment Variables).

**Linux**

If you run `RCE`_ from *BASH* you have to add the following line, in your `.bashrc` file

.. code::

    export PYTHONPATH="$PYTHONPATH: /InstalDir/CEASIOMpy/"

If you use *TCSH* you have to add the following line, in your `.tcshrc` file

.. code::

    setenv PYTHONPATH ${PYTHONPATH}: /InstalDir/CEASIOMpy/
