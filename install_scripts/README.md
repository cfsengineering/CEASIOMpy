# CEASIOMpy installation scripts

To simplify the installation of CEASIOMpy, you can use the followings sripts, if there is one which correspond to your OS.


## Ubuntu, Mint

To install CEASIOMpy on Ubuntu (or other version based on it), you can use the following command. Before you run this command, you should read the following remarks:

- If you already have a recent version of [Miniconda](https://docs.conda.io/en/latest/miniconda.html) or [Anaconda](https://anaconda.org/) installed on you computer, you can skip the line with `./install_conda.sh`

- PyTornado, SUMO, SU2 and Paraview are not mendatory to run CEASIOMpy. You can skip the lines corresponding to those you don't want to insatll.However, if you want to be able to run all possible workflows, you should all the modules.

- Some of the softwares will need to be execuded with `sudo` command. It will ask you you for your password and you will have to type `yes` to confirm some of the installation steps.

- If you want to be sure of what every script does, we encourage you to read those [scripts] in detail before you run them.

- We offer no warranty for the correctness of the installation. These cript have been tested only on Ubuntu 20.04 and Mint 20.3, but installation may differ because of different hardware and software configurations.

If you agree with the remark above, you can start the installation by openning a terminal where you want to install CEASIOMpy and run the following commands:

```bash
apt-get install git
git clone https://github.com/cfsengineering/CEASIOMpy.git
cd CEASIOMpy/install_scripts/Ubuntu
./install_conda.sh
./install_ceasiompy.sh
./install_pytornado.sh
./install_sumo.sh
./install_su2.sh
./install_paraview.sh
```

To test the installation, you can open a terminal and run the following commands:

```bash
conda activate ceasiompy
python -c "import ceasiompy"
cpacscreator # A "CPACSCreator" window will open, you can close it.
pytornado # You should see the help of PyTornado in the terminal.
sumo # A "SUMO" window will open, you can close it.
SU2_CFD # You should see something like "Error in "void CConfig::SetConfig_Parsing(char*)" in the terminal
paraview # A "Paraview" window will open, you can close it.
```

If one of the software is not working correctly, you can try to run its installation script again or open the script and run the command manually. 
If everything is working correctly, you can follow the [first turtorial](https://ceasiompy.readthedocs.io/en/latest/user_guide/getting_started.html#test-case-1-simple-workflow) to get familiar with CEASIOMpy.


