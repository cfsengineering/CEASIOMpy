Installation
============

General requirements
--------------------

Step 1: Download |name|
~~~~~~~~~~~~~~~~~~~~~~~

First, you will need to download |name|. You can download the code as a `zip file <https://codeload.github.com/cfsengineeringaa/CEASIOMpy/zip/master>`_ and unpack it, or if you are familiar with the command line tool ``git``, you can clone the repository.

.. code::

    git clone https://github.com/cfsengineering/CEASIOMpy

Place the ``CEASIOMpy`` folder where it is most convenient for you. This folder will be the main working directory when performing analyses.

Step 2: Set up the work environment
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To run analyses with the |name| framework, you will need to install a couple of required packages. To to so, we *highly* recommended you to use a so-called *Conda* environment.

.. hint::

    Think of *Conda* as a separate environment on your computer which does not interfere with your remaining system. If you have not used such an environment before, this may seem unfamiliar. Also note, that you will have to *activate* or *deactivate* this environment using a command line interface (terminal).

You may install either *Anaconda* or *Miniconda* (the latter is a smaller Conda installation with fewer pre-installed packages). Please refer to the Conda documentation for installation instructions.

* *Anaconda*: https://docs.anaconda.com/anaconda/install/
* *Miniconda*: https://docs.conda.io/en/latest/miniconda.html

After you have installed the Conda environment, we will set up the work environment for |name|. In a terminal, navigate to your ``CEASIOMpy`` folder. In this folder there should be a file called ``environment.yml`` which specifies what requirements are needed. With this file, we create a new, specific environment. Run the following line in your terminal:

.. code::

    conda env create -f environment.yml

The installation may take a couple of minutes. Now, you have created a new Conda environment called ``ceasiompy``.

.. hint::

    Whenever you work with |name|, you need to make sure that you are working inside the ``ceasiompy`` environment. You can always explicitely activate the ``cesiompy`` environment with the command:

    .. code::

        conda activate cesiompy

    You will also see a ``(ceasiompy) ... $`` in you terminal prompt which indicates that the ``ceasiompy`` environment is active.

..
    # Perhaps remove this...? It's very hard to use CEASIOMpy without conda

    If you do not use Conda, the following packages are required to be able to use |name|

    * Python 3.6 or higher
    * `Tixi`_ and `Tigl`_ libraries

Optional requirements
---------------------

The following software tools are not required to run all |name| workflows. It is still recommended to install them in order to use the entire |name| suite.

* *PyTornado*: https://github.com/airinnova/pytornado
* *SUMO*: https://www.larosterna.com/products/open-source
* *SU2 v7*: https://su2code.github.io/download.html

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


Setting up RCE
--------------

`RCE`_ is an Open Source distributed, workflow-driven integration environment. It is used by engineers and scientists to design and simulate complex systems (e.g., aircraft, ships, or satellites) by using and integrating their own design and simulation tools.
RCE is not mendatory anymore to use |name|, you can use the module WorkflowCreator instead. However, RCE_ is probably better to understand what is happening in your workflows.

* RCE environment can be download at: https://rcenvironment.de/pages/download.html

The CEASIOMpy modules could be used via the RCE interface but it is required to add them into the interface.
To do so, you should first execute the following python script:

* /CEASIOMpy/ceasiompy/utils/rce_integration.py

It will create in a folder on you computer (normally in you temp file). In this folder you can see one folder per module, each of them contain a JSON file.
All this folder must be copied where RCE saved your profile information:

* For linux: "home/.rce/default/integration/tools/common/""

Once you restart RCE, all the CEASIOMpy module should appear on left of your screen next to all the default modules.
