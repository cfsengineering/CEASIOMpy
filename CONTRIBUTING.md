# Contributing to CEASIOMpy

 - [Documentation/installation](#documentation--installation)
 - [Development guidelines](#development-guidelines)
   - [Git/Github](#git--github)
   - [Python](#python)
     - [Conda](#conda)
     - [Formatting](#formatting)
     - [Naming conventions](#naming-conventions)
     - [Logging](#logging)
     - [Testing and coverage](#testing-and-coverage)
     - [Other resources](#other-resources)
   - [CPACS](#cpacs)
   - [Other](#other)
- [How to contribute](#how-to-contribute) 


## Documentation / Installation

The CEASIOMpy documentation is available at [https://ceasiompy.readthedocs.io/](https://ceasiompy.readthedocs.io/). You will also find the installation procedure.

#### Installation issues

If you have some trouble to install CEASIOMpy on your computer, please use the following [Github Discussion page](https://github.com/cfsengineering/CEASIOMpy/discussions/categories/installation-issues). If your problem is something that could be reproduce it will be transformed into an issues.


## Development guidelines

### Git / Github

If you want participate to development of CEASIOMpy, it is a good thing if you have a basic understanding of how the version control system [Git](https://git-scm.com/) and the Github platform work.

- [Git Tutorials YouTube playlist](https://www.youtube.com/playlist?list=PL-osiE80TeTuRUfjRe54Eea17-YfnOOAx) by [Corey Schafer](https://www.youtube.com/channel/UCCezIgC97PvUuR4_gbFUs5g)

- [Official Github documentation](https://docs.github.com/en/get-started/quickstart/hello-world)

You could then fork the CEASIOMpy repository and create pull request when you think your work is ready to be reviewed.


### Python

#### Conda

It is highly recommended to use conda (or miniconda) for CEASIOMpy. Some libraries could could be complicated to install without it. If you install the default environment as explain in the [installation procedure](https://ceasiompy.readthedocs.io/en/latest/user_guide/installation.html#miniconda) you should then have all the requirements you need to run and develop CEASIOMpy.


#### Formatting

We try use [Black](https://github.com/psf/black) as a formatting tool. It should be install in the CEASIOMpy conda environment, if not, you can install it with:

```sh
pip install black
```

Then, you could either set it as the your default formatting tool in your IDE and set it to 'run on save' or run the following command when you want to lint your code:

```sh
black -l 99 name_of_your_file.py
```

#### Naming conventions

We try to follow th following naming conventions in CEASIOMpy:

- Variables : lower_case_with_underscores
- Functions : lower_case_with_underscores
- Classes and Exceptions : CapWords
- Packages and modules : short, all-lowercase names, no underscore
- Constants : CAPITAL_LETTER_WITH_UNDERSCORE
- Index in loops: i,j,k or lowercase (e.g. alpha, beta,…) or more explicit (i_fus, i_wing, i_eng)

Quotes:
-  `" "` simple quote are used for strings, e.g. print("Test1")
-  `"""Docstring"""` triple double quote are used for docstring (documentation)

-  Variable name should be explicit, with in first position the object
   it represents, then detail about its type, if needed. - aircraft_name
   - engine_nb - wing_span - controlsurf_deflection_angle

Variable name:
-  Variable name should be explicit, with in first position the object
   it represents, then detail about its type, e.g:
    - aircraft_name
    - engine_nb 
    - wing_span 
    - controlsurf_deflection_angle

These guidelines have been adapted from:
- https://www.python.org/dev/peps/pep-0008/#naming-conventions 
- https://gist.github.com/sloria/7001839
- https://www.python.org/dev/peps/pep-0008/


#### Logging

Create a logfle for a module can be very useful to understand what happens during its execution or debuging it.  The CEASIOMpy logger can be imported and used as following:

```python
from lib.utils.ceasiomlogger import get_logger
log = get_logger(__file__.split('.')[0])
```

Then, you can use the following logging function anywhere in the code of the module:

```python
log.debug('This is for debugging messages')
log.info('This is for information messages')
log.warning('This is for warning messages')
log.error('This is for error messages')
log.critical('This is for critical error messages')
```

They will be saved in a log file with the same name as your module (.log)
and prinded in the console during the execution.


#### Testing and coverage

If possible, new functions should have corresponding [pytest](https://docs.pytest.org/en/latest/getting-started.html).

Pytest, [flake8](https://flake8.pycqa.org/en/latest/) and [codecov](https://about.codecov.io/) are included in our [Github action CI](https://github.com/cfsengineering/CEASIOMpy/blob/main/.github/workflows/pytest.yml) and will run automatically for each push and pull request to the main branch.

You could also run the CI manually with on your machine with:

```bash
cd CEASIOMpy
./run_ci.sh
```


#### Other resources

If your are new to Python we recommend some material that could help you (you can also find many other ressources online):

- Website with Python tutorials: 

  - [learnpython.org](https://www.learnpython.org/)

- On YouTube, videos by [Corey Schafer](https://www.youtube.com/channel/UCCezIgC97PvUuR4_gbFUs5g):
  - [Python Programming Beginner Tutorials playlist](https://www.youtube.com/playlist?list=PL-osiE80TeTskrapNbzXhwoFUiLCjGgY7)
  - [Python Object-Oriented Tutorial playlist](https://www.youtube.com/playlist?list=PL-osiE80TeTsqhIuOqKhwlXsIBIdSeYtc)


### CPACS

CPACS is a Common Parametric Aircraft Configuration Schema. It is a data definition for the air transportation system. CPACS enables engineers to exchange information between their tools. CPACS is the default format to define aircrafts geometry in CEASIOMpy.

- [CPACS website](www.cpacs.de)
- [Github repository](https://github.com/DLR-SL/CPACS)
- Related libraries:
  - [TIXI](https://github.com/DLR-SC/tixi) A simple XML interface library
  - [TiGL](https://github.com/DLR-SC/tigl) Geometry Library to process aircraft geometries
  - [cpacspy](https://github.com/cfsengineering/cpacspy) A Python package to work with CPACS file and AeroMaps 


### Other

Other resources that could the useful.

#### PyTornado

- [PyTornado website](https://pytornado.readthedocs.io/en/latest/)
- [Github repository](https://github.com/airinnova/pytornado)

#### SUMO

- [SUMO website](https://www.larosterna.com/products/open-source)

#### SU2

- [SU2 website](https://su2code.github.io/)
- [SU2 Configuration template file](https://github.com/su2code/SU2/blob/master/config_template.cfg)



## How to contribute

### Reporting bugs

If you find a bug, please report it on the [Github issues page](https://github.com/cfsengineering/CEASIOMpy/issues) 


### Writing a new module

We highly encourage and appreciate any contributions to the CEASIOMpy codebase. If you have an idea for a new module, it could be a good thing to contact the CEASIOMpy team which could help you to write the module and be sure it is coherent with the rest of the project. You can also check the [CEASIOMpy project board](https://github.com/cfsengineering/CEASIOMpy/projects/1) to see what are the development status of the project.
If you want to write a new module you can use the [Module Template](https://github.com/cfsengineering/CEASIOMpy/tree/main/ceasiompy/ModuleTemplate) to help you. Normally, all modules follow the same file structure:

```
.
├── files               <- Files related to this module
│   ├── doc1.md
│   └── doc2.md
├── func                <- Module subfunction import by the main one.
│   ├── subfunc1.py
│   └── subfunc2.py
├── tests               <- Test function for this module.
│   ├── cpacsfile_for_test.xml
│   └── test_moduletemplate.py
├── __specs__.py        <- Specification of the module.
└── moduletemplate.py   <- Main module of the module.
```

To develop a new module you need to:

- Create a fork of the CEASIOMpy repository
- On your fork, create a new branch
- On this branch, write your module and its test functions
- Create a pull request on the CEASIOMpy repository
- Ask for a review on the pull request
- If the pull request is accepted, the module will be merged into the CEASIOMpy repository