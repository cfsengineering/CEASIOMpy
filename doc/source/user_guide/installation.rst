Installation
============

.. warning::

  CEASIOMpy is not a One-Click installation. As it gathers several different software, it required to have some computer knowledge and a little patience.

Also some software are optional and you don't need ton install them if you don't plan to use them.


Ubuntu20.04
-----------

Miniconda
~~~~~~~~~

Miniconda is an open source minimal package management system and environment management system.
You will need it to install all the python program of CEASIOMpy.

* Miniconda can be download at: https://docs.conda.io/en/latest/miniconda.html
Choose the “Python 3.8 Miniconda3 Linux 64-bit” version

Open a terminal (Ctrl+Alt+T) and type the following lines:

.. code::

  >> cd /PathToTheMinicondaDirectory
  >> sudo chmod +x Miniconda3-latest-Linux-x86_64.sh
  >> ./Miniconda3-latest-Linux-x86_64.sh

Press Enter several times (to the end)
Type “yes”
Press Enter
Type “yes”


CEASIOMpy
~~~~~~~~~

Open a new terminal and go in the repository where you want to install CEASIOMpy,
install git and download CEASIOMpy from Github with the following lines:

.. code::

  >> cd /PathToYourRepository
  >> sudo apt install git
  >> git clone https://github.com/cfsengineering/CEASIOMpy.git


Then, create the virtual Conda environment for CEASIOMpy (it may take a few minutes to download and install all the libraries):

.. code::

  >> cd CEASIOMpy
  >> conda env create -f environment.yml
  >> pip install -e .


.. warning::

  **Possible error**

  If during the installation you get an error with SMT installation (gcc missing), try:

  .. code::

      >> sudo apt-get install g++

  and redo the previous step.


To test if it works, you can open a new terminal and type:

.. code::

  >> conda activate ceasiompy
  >> cpacscreator

It should launch CPACSCreator in a new window, if it is the case, you can close it and continue the installation.


.. warning::

  **Possible error**

  If during the installation you get the following error:

  cpacscreator: error while loading shared libraries: libtbb.so.2: cannot open shared object file: No such file or directory

  try:

  .. code::

      >> sudo apt-get install libtbb2

  and redo the previous step.


**Update your paths**

Go in your /home folder and open the (hidden) file “.bashrc” with your favorite text editor.
Add the following lines and take care to replace all the "yourPathToCEASIOMPy" by the corresponding path on your computer.

.. code::

  alias ceasiompy='source activate ceasiompy && cd /yourPathToCEASIOMPy/CEASIOMpy/ceasiompy'
  alias ceasiomgui='cd /yourPathToCEASIOMPy/CEASIOMpy/ceasiompy/WorkflowCreator && python workflowcreator.py -gui'


Now you just have to type "ceasiompy" to activate the conda environment and "ceasiomgui" to start using CEASIOMpy with the GUI.


PyTornado (optional)
~~~~~~~~~~~~~~~~~~~~

Before installing PyTronado, make sure you are in the Conda environment you just create, by typing in a terminal:

.. code::

  >> conda activate ceasiompy

Navigate to the repertory where you want to install PyTornado (e.g. next to the CEASIOMpy repository), create a repository for it, download PyTornado and install it:

.. code::

  >> mkdir PyTornado
  >> cd PyTornado
  >> git clone https://github.com/airinnova/pytornado.git
  >> cd pytornado
  >> pip install --user .

To test if the installation was a success you can type “pytornado” in a terminal, you should get the default help message.


SUMO (optional)
~~~~~~~~~~~~~~~

* SUMO can be download at: https://www.larosterna.com/products/open-source
Choose the Linux Standalone package.

Right-click on the folder you just download and extract it.

Try to run SUMO from a terminal, by typing:

.. code::

  >> cd /sumo-standalone-Qt4-2.7.9/sumo-2.7.9/bin/
  >> ./dwfsumo


.. warning::

    **Possible error**

    If you get the error “sumo: error while loading shared libraries: libgfortran.so.3: cannot open shared object file: No such file or directory”:
    In a terminal, try to type :

    .. code::

        >> sudo apt-get install libgfortran3


    If you get the error “E: Unable to locate package...”

    In the terminal:

    .. code::

        >> cd /etc/apt/
        >> sudo vi sources.list

    Add the following lines:
    (the VI command is "i" to insert something and "esc" to quit the insert mode)

    ``deb http://ubuntu.ethz.ch/ubuntu/ bionic universe``
    ``deb http://ubuntu.ethz.ch/ubuntu/ bionic-updates universe``

    Save and quit (the VI command is ":wq")

    Type in a terminal:

    .. code::

        >> sudo apt-get update
        >> sudo apt-get install libgfortran3 



.. warning::

    **Possible error**

    If you get the error “sumo: error while loading shared libraries: libpng12: cannot open shared object file: No such file or directory”:

    Type in a terminal:

    .. code::

        >> sudo apt-get install libpng12

    If you get the error “E: Unable to locate package…”:

    Download the “libpng.12.so.0” library with the following link :download:`libpng12 <file/libpng12.so.0>`

    And copy it in your library with the following line:

    .. code::

        >> sudo cp libpng12.so.0 /usr/lib/x86_64-linux-gnu/.


Now you should be able to run SUMO from the terminal with:

.. code::

  >> cd /sumo-standalone-Qt4-2.7.9/sumo-2.7.9/bin/
  >> ./dwfsumo

To make it easier to run and possible to launch via CEASIOMpy you must create a symbolic link, with the following line:

.. code::

    >> sudo ln -s /YourPathToSUMO/sumo-standalone-Qt4-2.7.9/sumo-2.7.9/bin/dwfsumo /usr/bin/sumo


SU2 (optional)
~~~~~~~~~~~~~~

* SU2 can be download at: https://su2code.github.io/download.html
Choose the "SU2 Linux MPI" version.

Right-click on the folder you just download and extract it. You can place the extracted folder anywhere you want on your computer but will need to remember the path to it for the next step.


**Update your paths**

Go in your /home folder and open the (hidden) file “.bashrc” with your favorite text editor.

Add it the following lines:

.. code::

  export SU2_RUN="/yourPathToSU2/SU2-v7.0.7-linux64-mpi/bin"
  export SU2_HOME="/yourPathToSU2/SU2-v7.0.7-linux64-mpi"
  export PYTHONPATH=$PYTHONPATH:$SU2_RUN
  export PATH="$PATH:$SU2_RUN"

You can save and quit.


MPICH (optional)
~~~~~~~~~~~~~~~~

MPICH is only useful to run SU2 in parallel (several procs at the same time)

In a terminal type the following line:

.. code::

  >> sudo apt-get install -y mpich


Paraview (optional)
~~~~~~~~~~~~~~~~~~~

Paraview is not yet connected to CEASIOMpy but you can still use it to visualize manually the results from your SU2 calculations.

* Paraview can be download at: https://www.paraview.org/download/
Choose the latest Linux version.

Create a symbolic link as for SUMO:

.. code::

  >> sudo ln -s  /YourPathToParaview/ParaView-5.9.0-RC1-MPI-Linux-Python3.8-64bit/bin/paraview  /usr/bin/paraview


RCE (optional)
~~~~~~~~~~~~~~

`RCE`_ is an open source distributed, workflow-driven integration environment. It is used by engineers and scientists to design and simulate complex systems (e.g. aircraft, ships, or satellites) by using and integrating their own design and simulation tools.

RCE is not mandatory any more to use |name|. Instead, you can use the module ``WorkflowCreator`` to set up your analysis. However, RCE_ is probably still a good tool to understand what is happening in your workflow. But beware that this tools also has a learning curve.

* RCE environment can be download at: https://rcenvironment.de/pages/download.html
Download the version 10 (.deb) and install it on your computer.

To use the CEASIOMpy modules in the RCE interface it is necessary to make them available to RCE. To do so, you should first execute the following Python script:

.. code::

    >> python ceasiompy/utils/rce_integration.py

This will create in a folder on you computer in you temp directory. In this folder you can see one folder per module, each of them contain a JSON file. All of these folders must be copied where RCE saved your profile information:

* ``$HOME/.rce/default/integration/tools/common/``

Once you restart RCE, all the CEASIOMpy modules should appear on left of your screen next to all the default modules.



Windows 10
----------

.. warning::

    |name| has not been tested on Windows yet, so you may encounter some unexpected issues, do not hesitate to report them on Github.


This installation procedure is not complete yet.

Miniconda
~~~~~~~~~

To run analyses with the |name| framework, you will need to install a couple of required packages. To to so, we *highly* recommended you to use a so-called *Conda* environment.

.. hint::

    Think of *Conda* as a separate installation and work environment on your computer which does not interfere with your remaining system. If you have not used such an environment before, this may seem unfamiliar. Also note, that you will have to *activate* or *deactivate* this environment using a command line interface (terminal).

You may install either *Anaconda* or *Miniconda* (the latter is a smaller Conda installation with fewer pre-installed packages). Please refer to the Conda documentation for installation instructions.

* *Anaconda*: https://docs.anaconda.com/anaconda/install/
* *Miniconda*: https://docs.conda.io/en/latest/miniconda.html




CEASIOMpy
~~~~~~~~~

First, you will need to download |name|. You can download the code as a `zip file <https://codeload.github.com/cfsengineeringaa/CEASIOMpy/zip/master>`_ and unpack it, or if you are familiar with the command line tool ``git``, you can clone the repository.

.. code::

    git clone https://github.com/cfsengineering/CEASIOMpy

Place the ``CEASIOMpy`` folder where it is most convenient for you. This folder will be the main working directory when performing analyses.

After you have installed the Conda environment and downloaded |name|, you will set up the work environment. In a terminal, navigate to your ``CEASIOMpy`` folder. In this folder there should be a file called ``environment.yml`` which specifies what requirements are needed. With this file, you can create a new, specific environment. Run the following line in your terminal:

.. code::

    conda env create -f environment.yml

The installation may take a couple of minutes. Now, you have created a new Conda environment called ``ceasiompy``.

.. hint::

    Whenever you work with |name|, you need to make sure that you are working inside the ``ceasiompy`` environment. You can always explicitely activate the ``ceasiompy`` environment with the command:

    .. code::

        conda activate ceasiompy

    You will also see a ``(ceasiompy) ... $`` in you terminal prompt which indicates that the ``ceasiompy`` environment is active.


**Update your paths**

To automatically update your paths the following command should work.

.. code::

pip install -e .

Alternative platform independent method, is to use "conda develop ." However, this might require installation of the "conda build" package.
https://docs.conda.io/projects/conda-build/en/latest/resources/commands/conda-develop.html

You have to add the following line, in your `autoexec.bat` file.

.. code::

set PYTHONPATH=%PYTHONPATH%;\InstalDir\CEASIOMpy

Alternatively, you can edit the system variable through the *System Properties* (My Computer > Properties > Advanced System Settings > Environment Variables).



PyTornado (optional)
~~~~~~~~~~~~~~~~~~~~

Before installing PyTronado, make sure you are in the Conda environment you just create, by typing in a terminal:

.. code::

  >> conda activate ceasiompy

Navigate to the repertory where you want to install PyTornado (e.g. next to the CEASIOMpy repository), create a repository for it, download PyTornado and install it:

.. code::

  >> mkdir PyTornado
  >> cd PyTornado
  >> git clone https://github.com/airinnova/pytornado.git
  >> cd pytornado
  >> pip install --user .

To test if the installation was a success you can type “pytornado” in a terminal, you should get the default help message.


MacOS
-----

.. warning::

    MacOS is not the best OS for |name|, you may encounter some unexpected issues and difficulties to run some modules.


This installation procedure is not complete yet.

Miniconda
~~~~~~~~~

Install Miniconda or Conda.

CEASIOMpy
~~~~~~~~~

Open a new terminal and go in the repository where you want to install CEASIOMpy,
install git and download CEASIOMpy from Github with the following lines:

.. code::

  >> cd /PathToYourRepository
  >> git clone https://github.com/cfsengineering/CEASIOMpy.git


Then, create the virtual Conda environment for CEASIOMpy (it may take a few minutes to download and install all the libraries):

.. code::

  >> cd CEASIOMpy
  >> conda env create -f environment.yml
  >> pip install -e .


.. warning::

  **Possible error**

  If during the installation you get an error with SMT installation (gcc missing), try:

  .. code::

      >> sudo apt-get install g++

  and redo the previous step.


To test if it works, you can open a new terminal and type:

.. code::

  >> conda activate ceasiompy
  >> cpacscreator

It should launch CPACSCreator in a new window, if it is the case, you can close it and continue the installation.



..

  Update your paths
  ~~~~~~~~~~~~~~~~~

..
  Open the file ~/.bash_profile and add the following lines to the end:

..
  .. code::

      export PYTHONPATH=/InstalDir/CEASIOMpy/:$PYTHONPATH
      export PYTHONPATH


PyTornado (optional)
~~~~~~~~~~~~~~~~~~~~

Before installing PyTronado, make sure you are in the Conda environment you just create, by typing in a terminal:

.. code::

  >> conda activate ceasiompy

Navigate to the repertory where you want to install PyTornado (e.g. next to the CEASIOMpy repository), create a repository for it, download PyTornado and install it:

.. code::

  >> mkdir PyTornado
  >> cd PyTornado
  >> git clone https://github.com/airinnova/pytornado.git
  >> cd pytornado
  >> pip install --user .

To test if the installation was a success you can type “pytornado” in a terminal, you should get the default help message.
