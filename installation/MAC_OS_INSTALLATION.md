## MacOS

:x: No automatic installation script are available yet.

:warning: **Warning**
Adviced to follow [Docker instructions](https://github.com/cfsengineering/CEASIOMpy/blob/main/installation/DOCKER_INSTALLARION.md).
You can also install it manually, but some packages won't be there.

If you want to install CEASIOMpy manually, you should follow these steps:

- Install [Miniconda](https://docs.conda.io/en/latest/miniconda.html)
- Clone the [CEASIOMpy](https://github.com/cfsengineering/CEASIOMpy) repository
- Create the conda environment `ceasiompy` with the command `conda env create -f environment.yml`, if you have Apple Silicon processor, you need to use the command `CONDA_SUBDIR=osx-64 conda env create -f environment.yml`
- Activate the conda environment with the command `conda activate ceasiompy`
- Run the command `pip install -e .`
- Install [AVL](https://web.mit.edu/drela/Public/web/avl)
- Install [SU2](https://su2code.github.io/download.html)
- Install [Paraview](https://www.paraview.org/download/)
