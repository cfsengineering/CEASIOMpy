Installation
============

General requirements
--------------------

The following packages are required to be able to use |name|

* Python 3.6 or higer
* `Tixi`_ and `Tigl`_ libraries

The easiest way to have all the correct requirements is to use Conda environment (e.g. Anaconda or Miniconda) to simplify the installation. At the root of CEASIOMpy you can find a file called  "environment.yml", with the following line you can create a new environment with it:

.. code::

    >> conda env create -f environment.yml

(for more informaiton about conda environment check out: https://docs.conda.io/projects/conda/en/latest/index.html)


Optional requirements
---------------------

The following software are not required to run all |name| workflows, it is still recommended to have them in order to use the all |name| suite.

* PyTornado: https://github.com/airinnova/pytornado
* SUMO: https://www.larosterna.com/products/open-source
* SU2 v7: https://su2code.github.io/download.html


Setting up your path variables
------------------------------

To use core |name| you just have to download or clone the repository in a directory of your choice. Then, you may have to add this directory to your environment variable `PYTHONPATH`.

**Windows**

If use Windows, you have to add the following line, in your `autoexec.bat` file.

.. code::

    set PYTHONPATH=%PYTHONPATH%;\InstalDir\CEASIOMpy

Alternatively, you can edit the system variable through the *System Properties* (My Computer > Properties > Advanced System Settings > Environment Variables).


**MacOS**

Open the file ~/.bash_profile and add the following lines to the end:

.. code::

    export PYTHONPATH=/InstalDir/CEASIOMpy/:$PYTHONPATH
    export PYTHONPATH


**Linux**

If you use *BASH* you have to add the following line, in your `.bashrc` file

.. code::

    export PYTHONPATH="$PYTHONPATH: /InstalDir/CEASIOMpy/"

If you use *TCSH* you have to add the following line, in your `.tcshrc` file

.. code::

    setenv PYTHONPATH ${PYTHONPATH}: /InstalDir/CEASIOMpy/


Setting up RCE module
---------------------

`RCE`_ is an Open Source distributed, workflow-driven integration environment. It is used by engineers and scientists to design and simulate complex systems (e.g., aircraft, ships, or satellites) by using and integrating their own design and simulation tools.

* RCE environment can be download at: https://rcenvironment.de/pages/download.html

The CEASIOMpy modules could be used via the RCE interface but it is required to add them into the interface.
To do so, you should first execute the following python script:

* /CEASIOMpy/ceasiompy/utils/rce_integration.py

It will create in a folder on you computer (normally in you temp file). In this folder you can see one folder per module, each of them contain a JSON file.
All this folder must be copied where RCE saved your profile information:

* For linux: "home/.rce/default/integration/tools/common/""

Once you restart RCE, all the CEASIOMpy module should appear on left of your screen next to all the default modules.
