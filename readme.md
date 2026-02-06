[![Unittest](https://github.com/cfsengineering/CEASIOMpy/actions/workflows/unittests.yml/badge.svg)](https://github.com/cfsengineering/CEASIOMpy/actions/workflows/unittests.yml)
[![Integration tests](https://github.com/cfsengineering/CEASIOMpy/actions/workflows/integrationtests.yml/badge.svg)](https://github.com/cfsengineering/CEASIOMpy/actions/workflows/integrationtests.yml)
[![Codecov](https://codecov.io/gh/cfsengineering/CEASIOMpy/branch/main/graph/badge.svg?token=d6cyUEOmOQ)](https://codecov.io/gh/cfsengineering/CEASIOMpy)
[![Codacy Badge](https://app.codacy.com/project/badge/Grade/a2bd41b9be294e578382ca3f20281c85)](https://www.codacy.com/gh/cfsengineering/CEASIOMpy/dashboard?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=cfsengineering/CEASIOMpy&amp;utm_campaign=Badge_Grade)
[![Black code style](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![License](https://img.shields.io/badge/license-Apache%202-blue.svg)](https://github.com/cfsengineering/CEASIOMpy/blob/main/license)

# CEASIOMpy

<img align="right" width="300" height="300" src="documents/logos/CEASIOMpy_main_logos.png">

CEASIOMpy is an open source conceptual aircraft design environment which can be used to set up complex design and optimisation workflows for both conventional and unconventional aircraft configurations.

CEASIOMpy is mostly written in Python but it also depends on third-party libraries and software (like [SU2](https://su2code.github.io/) for the CFD calculation).

All input geometries are based on the open-standard format [CPACS](https://www.cpacs.de/), a *Common Parametric Aircraft Configuration Schema*. It uses a parametric definition for air transportation systems which is developed by the German Aerospace Center [DLR](https://www.dlr.de/).

:scroll: CEASIOMpy is maintained by [CFS Engineering](https://cfse.ch/) and [Airinnova](https://airinnova.se/). CEASIOMpy is under the [Apache License 2.0](https://github.com/cfsengineering/CEASIOMpy/blob/main/license).

:book: The Documentation of CEASIOMpy is integrated in this repository and can be read in documents like this one. Follow links to find the information that you are looking for.

## Table of contents

- [Table of contents](#table-of-contents)
- [Installation](#installation)
  - [Linux/macOS](#linuxmacos)
  - [Run CEASIOMpy](#run-ceasiompy)
- [Available modules](#available-modules)
  - [Geometry and Mesh](#geometry-and-mesh)
  - [Aerodynamics](#aerodynamics)
  - [Mission Analysis](#mission-analysis)
  - [Structure](#structure)
- [Contributing](#contributing)
- [More information](#more-information)
- [Cite us](#cite-us)

## Online Version (in development)

Visit: https://ceasiompy.com for an overview of what this repository has to offer.

## Installation

### Linux/macOS

On Linux/macOS, run the installer to set up the conda environment and optional tools (some scripts are still under development):

```bash
git clone https://github.com/cfsengineering/CEASIOMpy
cd CEASIOMpy
./scripts/install.sh
ceasiompy_run --g
```

For Windows users please use the online version at https://ceasiompy.com

### Create Docker Container (Windows, Optional)
A video which explains how to ![install](installation/DOCKER_INSTALLATION.md) CEASIOMpy on Docker is now available!
[![CEASIOMpy Docker Installation](installation/docker_installation.png)](https://www.youtube.com/watch?v=KTS1-6AsReU)

### Run CEASIOMpy

- **Run CEASIOMpy with a GUI to build the workflow**

    If you run CEASIOMpy with the following command, you can build the workflow with a graphical user interface.

    ```bash
    ceasiompy_run --gui
    ```

Follow the [test cases](#test-cases) to discover the different way of using CEASIOMpy.

### Available modules

There are many different modules available in CEASIOMpy that can be combined to create different workflows.

#### Geometry and Mesh

- [Add Control Surfaces](src/ceasiompy/addcontrolsurfaces/readme.md)
- [CPACS to GMSH](src/ceasiompy/cpacs2gmsh/readme.md)

#### Aerodynamics

- [AVL low-fidelity solver](src/ceasiompy/pyavl/readme.md)
- [SU2 high-fidelity Solver](src/ceasiompy/su2run/readme.md)

#### Meta modules

- [Surrogate Model Module](src/ceasiompy/smtrain/readme.md)

#### Mission Analysis

- [Static Stability](./src/ceasiompy/staticstability/readme.md)

#### Structure

- [Aeroframe](./src/ceasiompy/aeroframe/readme.md)

## Contributing

CEASIOMpy is an open source project and we welcome contributions from everyone. If you want to contribute to the development of CEASIOMpy, please read the document [contributing.md](contributing.md).

## More information

- [CEASIOMpy YouTube channel](https://www.youtube.com/channel/UCcGsFJV29os1Zzv66YKFRZQ)
- [CFS Engineering](https://cfse.ch/)
- [Airinnova](https://airinnova.se/)

## Upgrading environment

Sometimes deleting cache helps.

```bash
sudo find . -name "__pycache__" -type d -prune -exec rm -rf {} +
find . -name "*.pyc" -type f -delete
```

Or upgrading the environment.

```bash
conda env update -f environment.yml
```

## Cite us

This respository may be cited via BibTex as:
```
@software{CEASIOMpy,
  author = {
    Benedetti G. and
    Deligny L. and
    Jungo A.
},
  title = {CEASIOMpy: a python Aircraft Design environment},
  url = {https://github.com/cfsengineering/CEASIOMpy},
  year = {2025},
}
```
