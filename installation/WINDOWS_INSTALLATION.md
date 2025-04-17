## Windows

:x: **For now it seems there are some issues with some packages (TiGL, smt) in the Conda environment. If you are familiar with Windows and you want to help us to create an installation script, please contact us.**

An alternative solution is to install Ubuntu with [VirtualBox](https://www.virtualbox.org) and install CEASIOMpy in it.

Or, if you don't have VirtualBox and for some reason don't want to install it, you can download the Windows subsystem for Linux [WSL](https://learn.microsoft.com/en-us/windows/wsl/install)

:x: No automatic installation script are available yet.

You can try to install it manually, the basic steps are the following:

- Install [Miniconda](https://docs.conda.io/en/latest/miniconda.html)
- Clone the [CEASIOMpy](https://github.com/cfsengineering/CEASIOMpy) repository
- Create the conda environment `ceasiompy` with the command `conda env create -f environment.yml`
- Activate the conda environment with the command `conda activate ceasiompy`
- Run the command `pip install -e .`
- Install [AVL](https://web.mit.edu/drela/Public/web/avl)
- Install [SU2](https://su2code.github.io/download.html)
- Install [Paraview](https://www.paraview.org/download/)