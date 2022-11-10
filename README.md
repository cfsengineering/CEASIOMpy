[![Unittest](https://github.com/cfsengineering/CEASIOMpy/actions/workflows/unittests.yml/badge.svg)](https://github.com/cfsengineering/CEASIOMpy/actions/workflows/unittests.yml)
[![Integration tests](https://github.com/cfsengineering/CEASIOMpy/actions/workflows/integrationtests.yml/badge.svg)](https://github.com/cfsengineering/CEASIOMpy/actions/workflows/integrationtests.yml)
[![Codecov](https://codecov.io/gh/cfsengineering/CEASIOMpy/branch/main/graph/badge.svg?token=d6cyUEOmOQ)](https://codecov.io/gh/cfsengineering/CEASIOMpy)
[![Codacy Badge](https://app.codacy.com/project/badge/Grade/a2bd41b9be294e578382ca3f20281c85)](https://www.codacy.com/gh/cfsengineering/CEASIOMpy/dashboard?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=cfsengineering/CEASIOMpy&amp;utm_campaign=Badge_Grade)
[![Black code style](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![License](https://img.shields.io/badge/license-Apache%202-blue.svg)](https://github.com/cfsengineering/CEASIOMpy/blob/main/LICENSE)

# CEASIOMpy

<img align="right" width="300" height="300" src="documents/logos/CEASIOMpy_main_logos.png">

CEASIOMpy is an open source conceptual aircraft design environment. CEASIOMpy can be used to set up complex design and optimization workflows, both for conventional and unconventional aircraft configurations. Tools for various disciplines in aircraft design are provided, however, the aerodynamic tools are the most developed. They allow to automatically generate aerodynamic meshes and perform CFD calculation.

CEASIOMpy is written mostly in Python but it also depends on third-party libraries and software (like [SU2](https://su2code.github.io/) for the CFD calculation).

CEASIOMpy is based on the open-standard format [CPACS](https://www.cpacs.de/), a *Common Parametric Aircraft Configuration Schema*. It is a data definition for the air transportation system which is developed by the German Aerospace Center [DLR](https://www.dlr.de/). CPACS enables engineers to exchange information between their tools.

:scroll: CEASIOMpy is maintained by [CFS Engineering](https://cfse.ch/) and [Airinnova](https://airinnova.se/). CEASIOMpy is under the [Apache License 2.0](https://github.com/cfsengineering/CEASIOMpy/blob/main/LICENSE).

:book: The Documentation of CEASIOMpy is integrated in this repository and can be read in documents like this one. Follow links to find the information that you are looking for.

## Table of contents

- [Installation](#installation)
- [Usage](#usage)
  - [Test cases](#test-cases)
  - [Run CEASIOMpy](#run-ceasiompy)
  - [Examples of workflows](#examples-of-workflows)
  - [Available modules](#available-modules)
- [Contributing](#contributing)
- [More Information](#more-information)

## Installation

To install CEASIOMpy, please refer to the [installation page](installation/INSTALLATION.md), it will guide you through the installation process depending on your system.

## Usage

### Demo

[![CEASIOMpy GUI Video tutorial (Test case 2)](./test_cases/test_case_2/testcase2_startvideo.png)](https://www.youtube.com/watch?v=d-AaSrF5g3k)

### Test cases

Theses test cases are there to learn how to use CEASIOMpy. You will probably also learn a few things about the CPACS format. You can also run these tests to check that everything is installed and works as expected as they cover different possibilities of use of CEASIOMpy.

- [Test case 1](test_cases/test_case_1/README.md) : Run a simple workflow :heavy_check_mark:
- [Test case 2](test_cases/test_case_2/README.md) : Create and run a workflow with the Graphical User Interface (Video tutorial) :heavy_check_mark:
- [Test case 3](test_cases/test_case_3/README.md) : Create and run a workflow with the Graphical User Interface :heavy_check_mark:
- [Test case 4](test_cases/test_case_4/README.md) : Create and run a from a command line :x:
- [Test case 5](test_cases/test_case_5/README.md) : Create and run a from a configuration file :x:

### Run CEASIOMpy

- **Run CEASIOMpy with a GUI to build the workflow**

    If you run CEASIOMpy with the following command, you can build the workflow with a graphical user interface.

    ```bash
    ceasiompy_run --gui
    ```

- **Run CEASIOMpy with a command line to build the workflow**

    If you run CEASIOMpy with the following command, you can build the workflow directly by defining the CPACS files and the modules you want to use.

    ```bash
    cd WKDIR
    ceasiompy_run -m ../test_files/CPACSfiles/D150_simple.xml PyTornado SaveAeroCoefficients
    ```

- **Run CEASIOMpy with an existing configuration file**

    You can run an existing configuration file (e.g. from the [test cases](#test-cases)) with the following command.

    ```bash
    cd WKDIR
    ceasiompy_run --cfg ../test_cases/config_test_case_1.cfg
    ```

- **Write a CEASIOMpy configuration file**

    A CEASIOMpy configuration file is a text file (saved as `*.cfg`) which contains the information necessary to run CEASIOMpy. You can write a configuration file by following the example.

    ```text
    % CEASIOMpy configuration file

    % Input CPACS files (required) which contain the aircraft geometry
    CPACS_TOOLINPUT = /users/disk10/jungo/github/CEASIOMpy/test_files/CPACSfiles/D150_simple.xml

    # Modules which will be used in the workflow (in order)

    MODULE_TO_RUN = ( PyTornado, SaveAeroCoefficients )
    ```

    You can save this file as `my_config_file.cfg` in your `WKDIR`. Then, you can run it with the following commands:

    ```bash
    cd WKDIR
    ceasiompy_run --cfg ./my_config_file.cfg
    ```

### Examples of workflows

- **Simple workflow with PyTornado (Vortex Lattice Method)**

<div align="center">

```mermaid
  graph LR;
      PyTornado-->SaveAeroCoefficients;
```

</div>

- **Workflow with SU2 (CFD) at fixed CL**

<div align="center">

```mermaid
  graph LR;
      CLCalculator-->CPACS2SUMO;
      CPACS2SUMO-->SUMOAutoMesh;
      SUMOAutoMesh-->SU2Run;
      SU2Run-->ExportCSV;
```

</div>

### Available modules

A lot of different modules are available in CEASIOMpy, they can be assembled in various workflows. You can find below the list of available modules. The module status is marked as follows:

:heavy_check_mark: : The module should be working as expected. Some small bugs may be present, don't hesitate to report them (more details [here](CONTRIBUTING.md#reporting-bugs)).

:warning: : The module is not working fully as expected. It is not a bug, but some features or data handling are yet compatible with the new file structure. Check the [Kanban board](https://github.com/cfsengineering/CEASIOMpy/projects/1) to see planned and in progress features.

:x: : The module is not working at all. Some functions have been written but requires a lot of changes to be compatible with the rest of CEASIOMpy.

<img align="right" height="80" src="documents/logos/CEASIOMpy_banner_main.png">

#### General modules

- [ModuleTemplate](ceasiompy/ModuleTemplate/README.md) :heavy_check_mark:
- [Optimisation](ceasiompy/Optimisation/README.md) :x:
- [SMTrain](ceasiompy/SMTrain/README.md) :x:
- [SMUse](ceasiompy/SMUse/README.md) :x:

<img align="right" height="80" src="documents/logos/CEASIOMpy_banner_geometry.png">

#### Geometry and Mesh

- [CPACSCreator](ceasiompy/CPACSCreator/README.md) :heavy_check_mark:
- [CPACS2GMSH](ceasiompy/CPACS2GMSH/README.md) :heavy_check_mark:
- [CPACS2SUMO](ceasiompy/CPACS2SUMO/README.md) :heavy_check_mark:
- [SUMOAutoMesh](ceasiompy/SUMOAutoMesh/README.md) :heavy_check_mark:
- SU2MeshDef :warning:

<img align="right" height="80" src="documents/logos/CEASIOMpy_banner_aero.png">

#### Aerodynamics

- [CLCalculator](ceasiompy/CLCalculator/README.md) :heavy_check_mark:
- [PyTornado](ceasiompy/PyTornado/README.md) :heavy_check_mark:
- [SU2Run](ceasiompy/SU2Run/README.md) :heavy_check_mark:
- [SkinFriction](ceasiompy/SkinFriction/README.md) :heavy_check_mark:
- [SaveAeroCoefficients](ceasiompy/SaveAeroCoefficients/README.md) :heavy_check_mark:

<img align="right" height="80" src="documents/logos/CEASIOMpy_banner_weights.png">

#### Weight and Balance

- BalanceConventional :warning:
- BalanceUnconventional :warning:
- [WeightConventional](./ceasiompy/WeightConventional/README.md) :heavy_check_mark:
- WeightUnconventional :warning:

<img align="right" height="80" src="documents/logos/CEASIOMpy_banner_mission.png">

#### Mission Analysis

- Range :warning:
- StabilityStatic :warning:
- StabilityDynamic :x:

<img align="right" height="80" src="documents/logos/CEASIOMpy_banner_structure.png">

#### Structure

- AeroFrame :x:

## Contributing

CEASIOMpy is an open source project and we welcome contributions from everyone. Some CEASIOMpy modules have been developed by students during their internship or master thesis.
If you want to contribute to the development of CEASIOMpy , please refer to the [CONTRIBUTING.md](CONTRIBUTING.md) document.

## More information

- [CEASIOMpy YouTube channel](https://www.youtube.com/channel/UCcGsFJV29os1Zzv66YKFRZQ)
- [CFS Engineering](https://cfse.ch/)
- [Airinnova](https://airinnova.se/)
