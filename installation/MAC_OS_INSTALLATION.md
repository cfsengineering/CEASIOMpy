## MacOS

:warning: **Warning**
Adviced to follow [Docker instructions](https://github.com/cfsengineering/CEASIOMpy/blob/main/installation/DOCKER_INSTALLARION.md).

:x: No automatic installation script are available yet.

You can install it manually, the basic steps are the following:

- Install [Miniconda](https://docs.conda.io/en/latest/miniconda.html)
- Clone the [CEASIOMpy](https://github.com/cfsengineering/CEASIOMpy) repository
- Create the conda environment `ceasiompy` with the command `conda env create -f environment.yml`
- Activate the conda environment with the command `conda activate ceasiompy`
- Run the command `pip install -e .`
- Install [AVL](https://web.mit.edu/drela/Public/web/avl)
- Install [SU2](https://su2code.github.io/download.html)
- Install [Paraview](https://www.paraview.org/download/)
