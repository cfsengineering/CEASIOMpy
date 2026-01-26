[![Unittest](https://github.com/cfsengineering/CEASIOMpy/actions/workflows/unittests.yml/badge.svg)](https://github.com/cfsengineering/CEASIOMpy/actions/workflows/unittests.yml)
[![Integration tests](https://github.com/cfsengineering/CEASIOMpy/actions/workflows/integrationtests.yml/badge.svg)](https://github.com/cfsengineering/CEASIOMpy/actions/workflows/integrationtests.yml)
[![Codecov](https://codecov.io/gh/cfsengineering/CEASIOMpy/branch/main/graph/badge.svg?token=d6cyUEOmOQ)](https://codecov.io/gh/cfsengineering/CEASIOMpy)
[![Codacy Badge](https://app.codacy.com/project/badge/Grade/a2bd41b9be294e578382ca3f20281c85)](https://www.codacy.com/gh/cfsengineering/CEASIOMpy/dashboard?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=cfsengineering/CEASIOMpy&amp;utm_campaign=Badge_Grade)
[![Black code style](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![License](https://img.shields.io/badge/license-Apache%202-blue.svg)](https://github.com/cfsengineering/CEASIOMpy/blob/main/LICENSE)

# CEASIOMpy

<img align="right" width="300" height="300" src="documents/logos/CEASIOMpy_main_logos.png">

CEASIOMpy is an open source conceptual aircraft design environment which can be used to set up complex design and optimisation workflows for both conventional and unconventional aircraft configurations.

CEASIOMpy is mostly written in Python but it also depends on third-party libraries and software (like [SU2](https://su2code.github.io/) for the CFD calculation).

All input geometries are based on the open-standard format [CPACS](https://www.cpacs.de/), a *Common Parametric Aircraft Configuration Schema*. It uses a parametric definition for air transportation systems which is developed by the German Aerospace Center [DLR](https://www.dlr.de/).

:scroll: CEASIOMpy is maintained by [CFS Engineering](https://cfse.ch/) and [Airinnova](https://airinnova.se/). CEASIOMpy is under the [Apache License 2.0](https://github.com/cfsengineering/CEASIOMpy/blob/main/LICENSE).

:book: The Documentation of CEASIOMpy is integrated in this repository and can be read in documents like this one. Follow links to find the information that you are looking for.

## Table of contents

- [CEASIOMpy](#ceasiompy)
  - [Table of contents](#table-of-contents)
  - [Installation](#installation)
      - [Recommended storage](#recommended-storage)
    - [Linux/macOS](#linuxmacos)
    - [Windows](#windows)
      - [1. Download CEASIOMpy Repository](#1-download-ceasiompy-repository)
      - [2. Install WSL with Ubuntu (if not done already)](#2-install-wsl-with-ubuntu-if-not-done-already)
      - [3. Install the necesssary softwares](#3-install-the-necesssary-softwares)
    - [Windows users](#windows-users)
    - [Demo](#demo)
    - [Test cases](#test-cases)
    - [Run CEASIOMpy](#run-ceasiompy)
    - [Examples of workflows](#examples-of-workflows)
    - [Available modules](#available-modules)
      - [General modules](#general-modules)
      - [Geometry and Mesh](#geometry-and-mesh)
      - [Aerodynamics](#aerodynamics)
      - [Weight and Balance](#weight-and-balance)
      - [Mission Analysis](#mission-analysis)
      - [Structure](#structure)
      - [Data Analysis and Storage](#data-analysis-and-storage)
  - [Contributing](#contributing)
  - [More information](#more-information)
  - [Cite us](#cite-us)

## Installation

#### Recommended storage

At least 20 GB required for overall installation.

### Linux/macOS

On Linux/macOS, run the installer to set up the conda environment and optional tools (some scripts are still under development):

```bash
git clone https://github.com/cfsengineering/CEASIOMpy
cd CEASIOMpy
./scripts/install.sh
```

### Windows (Under Maintenance)

Windows requires WSL installation.

#### 1. Download CEASIOMpy Repository

```
git clone https://github.com/cfsengineering/CEASIOMpy
cd CEASIOMpy
```

#### 2. Install WSL with Ubuntu (if not done already)

```
wsl --install
wsl --install -d Ubuntu
```

You might need to reboot your machine after the installation.

#### 3. Install the necesssary softwares

```
bash ./scripts/install.sh
```

### Create Docker Container (Optional)
A video which explains how to ![install](installation/DOCKER_INSTALLATION.md) CEASIOMpy on Docker is now available!
[![CEASIOMpy Docker Installation](installation/docker_installation.png)](https://www.youtube.com/watch?v=KTS1-6AsReU)

### Demo

[![CEASIOMpy GUI Video tutorial (Test case 2)](./test_cases/test_case_2/testcase2_startvideo.png)](https://www.youtube.com/watch?v=d-AaSrF5g3k)

### Test cases

These test cases are there to learn how to use CEASIOMpy. You will probably also learn a few things about the CPACS format. You can also run these tests to verify that everything is installed and working as expected as they cover different possible ways of using CEASIOMpy. Be sure you finish the [installation](installation/INSTALLATION.md) before you try them.

- [Test case 1](test_cases/test_case_1/README.md) : Run a simple workflow
- [Test case 2](test_cases/test_case_2/README.md) : Create and run a workflow with the Graphical User Interface (Video tutorial)
- [Test case 3](test_cases/test_case_3/README.md) : Create and run a workflow with the Graphical User Interface
- [Test case 4](test_cases/test_case_4/README.md) : Create and run a from a command line
- [Test case 5](test_cases/test_case_5/README.md) : Create and run a from a configuration file

### Run CEASIOMpy

- **Run CEASIOMpy with a GUI to build the workflow**

    If you run CEASIOMpy with the following command, you can build the workflow with a graphical user interface.

    ```bash
    ceasiompy_run --gui
    ```

- **Run CEASIOMpy with a command line to build the workflow**

    If you run CEASIOMpy with the following command, you can build the workflow directly by defining the CPACS files and the modules you want to use.

    ```bash
    ceasiompy_run -m test_files/CPACSfiles/D150_simple.xml PyAVL SaveAeroCoefficients
    ```

Follow the [test cases](#test-cases) to discover the different way of using CEASIOMpy.

### Examples of workflows

- **Simple workflow with PyAVL (Vortex Lattice Method)**

<div align="center">

```mermaid
  graph LR;
      PyAVL-->SaveAeroCoefficients;
```

</div>

- **Workflow with SU2 (CFD) at fixed CL**

<div align="center">

```mermaid
  graph LR;
      CPACS2Updater-->CPACS2Gmsh;
      CPACS2Gmsh-->SU2Run;
      SU2Run-->ExportCSV;
      ExportCSV-->Database;
```

</div>

### Available modules

There are many different modules available in CEASIOMpy that can be combined to create different workflows. The list of available modules is shown below. The modules' statuses are marked as follows:

:heavy_check_mark: : The module should work as expected. If you find bugs, do not hesitate to report them (more details [here](CONTRIBUTING.md#reporting-bugs)).

:warning: : The module does not work as expected. It is not a bug, but some features or data handling are not yet compatible with the new file structure. Check the [Kanban Board](https://github.com/cfsengineering/CEASIOMpy/projects/1) to see planned and in-progress features.

:x: : The module does not work at all. Some functions have been written, but need a lot of changes to be compatible with the rest of CEASIOMpy.

<img align="right" height="80" src="documents/logos/CEASIOMpy_banner_main.png">

#### General modules

- [Optimisation](src/ceasiompy/Optimisation/README.md) :x:
- [SMTrain](src/ceasiompy/SMTrain/README.md) :heavy_check_mark:
- [SMUse](src/ceasiompy/SMUse/README.md) :heavy_check_mark:
- [ThermoData](src/ceasiompy/ThermoData/README.md) :heavy_check_mark:

<img align="right" height="80" src="documents/logos/CEASIOMpy_banner_geometry.png">

#### Geometry and Mesh

- [CPACSCreator](src/ceasiompy/CPACSCreator/README.md) :heavy_check_mark:
- [CPACSUpdater](src/ceasiompy/CPACSUpdater/README.md) :heavy_check_mark:
- [CPACS2GMSH](src/ceasiompy/CPACS2GMSH/README.md) :heavy_check_mark:
- [CPACS2SUMO](src/ceasiompy/CPACS2SUMO/README.md) :heavy_check_mark:
- [SUMOAutoMesh](src/ceasiompy/SUMOAutoMesh/README.md) :warning:
- SU2MeshDef :warning:

<img align="right" height="80" src="documents/logos/CEASIOMpy_banner_aero.png">

#### Aerodynamics

- [CLCalculator](src/ceasiompy/CLCalculator/README.md) :heavy_check_mark:
- [PyAVL](src/ceasiompy/PyAVL/README.md) :heavy_check_mark:
- [SU2Run](src/ceasiompy/SU2Run/README.md) :heavy_check_mark:
- [SkinFriction](src/ceasiompy/SkinFriction/README.md) :heavy_check_mark:
- [SaveAeroCoefficients](src/ceasiompy/SaveAeroCoefficients/README.md) :heavy_check_mark:

<img align="right" height="80" src="documents/logos/CEASIOMpy_banner_weights.png">

#### Weight and Balance

- BalanceConventional :warning:
- BalanceUnconventional :warning:
- [WeightConventional](./src/ceasiompy/WeightConventional/README.md) :heavy_check_mark:
- WeightUnconventional :warning:

<img align="right" height="80" src="documents/logos/CEASIOMpy_banner_mission.png">

#### Mission Analysis

- Range :warning:
- [StaticStability](./src/ceasiompy/StaticStability/README.md) :heavy_check_mark:
- [DynamicStability](./src/ceasiompy/DynamicStability/README.md) :heavy_check_mark:

<img align="right" height="80" src="documents/logos/CEASIOMpy_banner_structure.png">

#### Structure

- [AeroFrame](./src/ceasiompy/AeroFrame/README.md) :heavy_check_mark:

#### Data Analysis and Storage

- [Database](./src/ceasiompy/Database/README.md) :heavy_check_mark:

## Contributing

CEASIOMpy is an open source project and we welcome contributions from everyone. Some CEASIOMpy modules have been developed by students as part of their internship or master thesis.

If you want to contribute to the development of CEASIOMpy, please read the document [CONTRIBUTING.md](CONTRIBUTING.md).

## More information

- [CEASIOMpy YouTube channel](https://www.youtube.com/channel/UCcGsFJV29os1Zzv66YKFRZQ)
- [CFS Engineering](https://cfse.ch/)
- [Airinnova](https://airinnova.se/)

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
