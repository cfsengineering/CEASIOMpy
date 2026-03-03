# contributing to CEASIOMpy

- [Documentation/installation](#documentation--installation)
- [Development guidelines](#development-guidelines)
  - [Git/Github](#git--github)
  - [Python](#python)
    - [Conda](#conda)
    - [Formatting](#formatting)
    - [Naming conventions](#naming-conventions)
    - [Logging](#logging)
    - [Testing and coverage](#testing-and-coverage)
    - [Learn Python](#learn-python)
  - [CPACS](#cpacs)
  - [Other](#other)
- [How to contribute](#how-to-contribute)
  - [Reporting bugs](#reporting-bugs)
  - [Writing a new module](#writing-a-new-module)
  - [Writing specs file](#writing-specs-file)

## Documentation / Installation

The CEASIOMpy documentation is included in the [Github repository](./README.md) in Markdown files as this one. You can follow the links to find the information that you are looking for.

### Installation

To install CEASIOMpy please refer to the [installation page](./installation/INSTALLATION.md), it will guide you through the installation process depending on your system.

If you have some trouble to install CEASIOMpy on your computer, please use the following [Github Discussion page](https://github.com/cfsengineering/CEASIOMpy/discussions/categories/installation-issues). If your problem is something that could be reproduced it will be transformed into an issues.

## Development guidelines

### Git / Github

If you want to participate in the development of CEASIOMpy, it is a good thing if you have a basic understanding of how the version control system [Git](https://git-scm.com/) and the Github platform work.

- [Learn Git Branching](https://learngitbranching.js.org/?locale=en_EN) : online tutorials to learn how to use Git

- [Git Tutorials YouTube playlist](https://www.youtube.com/playlist?list=PL-osiE80TeTuRUfjRe54Eea17-YfnOOAx) by [Corey Schafer](https://www.youtube.com/channel/UCCezIgC97PvUuR4_gbFUs5g)

- [Official Github documentation](https://docs.github.com/en/get-started/quickstart/hello-world)

You could then fork the CEASIOMpy repository and create pull request when you think your work is ready to be reviewed.

### Python

#### Conda

It is highly recommended to use conda (or miniconda) for CEASIOMpy. Some libraries could be complicated to install without it. If you install the default environment as explain in the [installation procedure](./installation/INSTALLATION.md) you should then have all the requirements you need to run and develop CEASIOMpy.

#### Formatting

We try to use [Black](https://github.com/psf/black) as a formatting tool. It should be installed in the CEASIOMpy conda environment, if not, you can install it with:

```sh
pip install black
```

Then, you could either set it as the your default formatting tool in your IDE and set it to 'run on save' or run the following command when you want to lint your code:

```sh
black -l 99 name_of_your_file.py
```

#### Naming conventions

We try to follow the following naming conventions in CEASIOMpy:

- Variables : lower_case_with_underscores
- Functions : lower_case_with_underscores
- Classes and Exceptions : CapWords
- Packages and modules : short, all-lowercase names, no underscore
- Constants : CAPITAL_LETTER_WITH_UNDERSCORE
- Index in loops: i,j,k or lowercase (e.g. alpha, beta,…) or more explicit (i_fus, i_wing, i_eng)

Quotes:

- `" "` simple quotes are used for strings, e.g. `print("Test1")`
- `"""Docstring"""` triple-double quotes are used for docstring (documentation)
- Variable name should be explicit, with in first position the object
   it represents, then detail about its type, e.g:
  - aircraft_name
  - engine_nb
  - wing_span
  - controlsurf_deflection_angle

These guidelines have been adapted from:

- <https://www.python.org/dev/peps/pep-0008/#naming-conventions>
- <https://gist.github.com/sloria/7001839>
- <https://www.python.org/dev/peps/pep-0008/>

#### Logging

Logging the output of a module can be very useful to understand what happens during its execution or debugging it.  The CEASIOMpy logger can be imported and used as following:

```python
from ceasiompy import log
```

Then, you can use the following logging function anywhere in the code of the module:

```python
log.debug('This is for debugging messages')
log.info('This is for information messages')
log.warning('This is for warning messages')
log.error('This is for error messages')
log.critical('This is for critical error messages')
```

The log file is saved at the root of CEASIOMpy (CEASIOMpy/ceasiompy.log) and printed in the console during the execution. In the log file, the second column is the level of the message and the third column is the module from which the message comes from.

#### Testing and coverage

If possible, new functions should be tested with [pytest](https://docs.pytest.org/en/latest/getting-started.html).

Pytest, [flake8](https://flake8.pycqa.org/en/latest/) and [codecov](https://about.codecov.io/) are included in our [Github action CI](.github/workflows/unittests.yml) and will run automatically for each push and pull request to the main branch.

You can also run the CI manually with on your machine with:

```bash
cd CEASIOMpy
./tests/run_ci.sh
```

The CI will run [Black](https://black.readthedocs.io/en/stable/), Flake8, Unit tests, Integration tests and Coverage. You can also use options to run only a part of the CI. Use the help to see the available options.

```bash
./tests/run_ci.sh --help
CEASIOMpy run Continuous Integration tests (Unit and Integration)

Syntax: ./run_ci [-f|g|h|i|u]
options:
-f     Fast mode (skip tests marked as 'slow')
-g     Run GUI tests, requiring a user interaction (not active by default).
-h     Print this help message.
-i     Skip integration tests.
-u     Skip unit tests.
```

### CPACS

[CPACS](https://www.cpacs.de) is a Common Parametric Aircraft Configuration Schema [[1]](#Alder20). It is a data definition for the air transportation system. CPACS enables engineers to exchange information between their tools. CPACS is the default format to define aircrafts geometry in CEASIOMpy.

- [CPACS official website](https://www.cpacs.de)
- [CPACS Github repository](https://github.com/DLR-SL/CPACS)
- [CPACS documentation](https://www.cpacs.de/documentation/CPACS_3_3_0_Docs/html/89b6a288-0944-bd56-a1ef-8d3c8e48ad95.htm)
- Related libraries:
  - [TIXI](https://github.com/DLR-SC/tixi) A simple XML interface library
  - [TiGL](https://github.com/DLR-SC/tigl) Geometry Library to process aircraft geometries [[2]](#Sigg19)
  - [cpacspy](https://github.com/cfsengineering/cpacspy) A Python package to work with CPACS file and aeromaps

### Other

Other resources that could the useful.

- [gmsh website](https://gmsh.info/)
- [avl website](https://web.mit.edu/drela/Public/web/avl/)
- [su2 website](https://su2code.github.io/)
- [su2 config template file](https://github.com/su2code/SU2/blob/master/config_template.cfg)
- [paraview website](https://www.paraview.org/)

## How to contribute

### Reporting bugs

If you find a bug, please report it on the [Github issues page](https://github.com/cfsengineering/CEASIOMpy/issues)

### Writing a new module

We highly encourage and appreciate any contributions to the CEASIOMpy codebase. If you have an idea for a new module, it could be a good thing to contact the CEASIOMpy team which could help you to write the module and be sure it is coherent with the rest of the project. You can also check the [CEASIOMpy project board](https://github.com/cfsengineering/CEASIOMpy/projects/1) to see what is the development status of the project.

## References

<a id="Alder20">[1]</a> M. Alder, E. Moerland, J. Jepsen and B. Nagel. Recent Advances in Establishing a Common Language for Aircraft Design with CPACS. Aerospace Europe Conference 2020, Bordeaux, France, 2020. <https://elib.dlr.de/134341/>  

<a id="Sigg19">[2]</a> Siggel, M. and Kleinert, J. and Stollenwerk, T. and Maierl, R.: TiGL: An Open Source Computational Geometry Library for Parametric Aircraft Design. Mathematics in Computer Science (2019). [10.1007/s11786-019-00401-y](https://link.springer.com/article/10.1007/s11786-019-00401-y)  
