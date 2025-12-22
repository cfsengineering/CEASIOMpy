## Linux

To install CEASIOMpy on Linux, you can use some script which should simplified the installation. Those scripts exist for:

- Ubuntu (or other version based on it)
- CentOS, Rocky Linux, Alma

Before you run this command, you should read the following remarks:

- If you already have a recent version of [Miniconda](https://docs.conda.io/en/latest/miniconda.html) or [Anaconda](https://anaconda.org/) installed on you computer, you can skip the line with `./install_conda.sh`

- Avl, SUMO, SU2 and Paraview are not mandatory to run CEASIOMpy. You can skip the lines corresponding to those you don't want to install. However, if you want to be able to run all possible workflows, you should have all the modules.

- Some softwares will need to be executed with `sudo` command. It will ask you for your password and you will have to type `yes` to confirm some of the installation steps.

- If you want to be sure of what every script does, we encourage you to read those scripts ([Ubuntu](./Ubuntu), [CentOS](./CentOS)) in detail before you run them.

- We offer no warranty for the correctness of the installation. These scripts have been tested only on a few Linux distro and the installation may differ because of different hardware and software configurations.

If you agree with the remark above, you can start the installation by opening a terminal where you want to install CEASIOMpy and run the following commands one by one:

- Ubuntu:

```bash
sudo apt-get install git
git clone https://github.com/cfsengineering/CEASIOMpy.git
cd CEASIOMpy
./installation/Ubuntu/install_miniconda.sh
source ~/.bashrc
./installation/Ubuntu/install_ceasiompy.sh
./installation/Ubuntu/install_avl.sh
./installation/Ubuntu/install_su2_with_mpi.sh
./installation/Ubuntu/install_paraview.sh
source ~/.bashrc
```

- CentOS:

```bash
sudo dnf install git
git clone https://github.com/cfsengineering/CEASIOMpy.git
cd CEASIOMpy
./installation/CentOS/install_miniconda.sh
source ~/.bashrc
./installation/CentOS/install_ceasiompy.sh
./installation/CentOS/install_avl.sh
./installation/CentOS/install_su2.sh
./installation/CentOS/install_paraview.sh
./installation/CentOS/install_openvsp.sh

source ~/.bashrc
```

When it is done, you can test the installation, by opening a new terminal and try to run the following commands one by one:

Check if ceasiompy conda environment exists.

```bash
conda activate ceasiompy
```

A "CPACSCreator" window will open, you can close it.

```bash
cpacscreator
```

The avl interface should appear in the terminal.

```bash
avl
```

The SU2 interface should appear in the terminal.

```bash
SU2_CFD
```

A "Paraview" window will open, you can close it.

```bash
paraview
```

If one of the software is not working correctly, you can try to run its installation script again or open the script and run the command manually.
If everything is working correctly, you can try the first [test case](../test_cases/test_case_1/README.md) to get familiarized with CEASIOMpy.
