# Contributing to CEASIOMpy

 - [Documentation/installation](#documentation--installation)
 - [Development guidelines](#development-guidelines)
   - [Git/Github](#git--github)
   - [Python](#python)
   - [CPACS](#cpacs)
   - [Other](#other)
- [How to contribute](#how-to-contribute) 


## Documentation / Installation

The CEASIOMpy documentation is available at [https://ceasiompy.readthedocs.io/](https://ceasiompy.readthedocs.io/). You will also find the installation procedure.

#### Installation issues

If you have some trouble to install CEASIOMpy on your computer, please use the [Github Discussion page](https://github.com/cfsengineering/CEASIOMpy/discussions/categories/installation-issues). If your problem is something that could be reproduce it will be transformed into a an issues.


## Development guidelines

### Git/Github

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

It is also recommended to have a look to the Python convention guidelines [PEP8](https://www.python.org/dev/peps/pep-0008/#naming-conventions) 

#### Naming conventions

We try to follow th following naming conventions in CEASIOMpy (should be close to PEP8):

- Variables : lower_case_with_underscores
- Functions : lower_case_with_underscores
- Classes and Exceptions : CapWords
- Packages and modules : short, all-lowercase names, no underscore
- Constants : CAPITAL_LETTER_WITH_UNDERSCORE
- Index in loops: i,j,k or lowercase (e.g. alpha, beta,…) or more explicit (i_fus, i_wing, i_eng)


#### Testing and coverage

If possible, new functions should have corresponding [pytest](https://docs.pytest.org/en/latest/getting-started.html).

Pytest, [flake8](https://flake8.pycqa.org/en/latest/) and [codecov](https://about.codecov.io/) are included in our [Github action CI](https://github.com/cfsengineering/CEASIOMpy/blob/master/.github/workflows/pytest.yml) and will run automatically for each push and pull request to the master branch.

You could also run the CI manually with on your machine with:

```sh
cd CEASIOMpy
./run_ci.sh
```


#### Other resources

If your are new to Python we recommend some material that could help you:

- On YouTube, videos by [Corey Schafer](https://www.youtube.com/channel/UCCezIgC97PvUuR4_gbFUs5g):
  - [Python Programming Beginner Tutorials playlist](https://www.youtube.com/playlist?list=PL-osiE80TeTskrapNbzXhwoFUiLCjGgY7)
  - [Python Object-Oriented Tutorial playlist](https://www.youtube.com/playlist?list=PL-osiE80TeTsqhIuOqKhwlXsIBIdSeYtc)


### CPACS

CPACS is a Common Parametric Aircraft Configuration Schema. It is a data definition for the air transportation system. CPACS enables engineers to exchange information between their tools.

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

If you find a bug, please report it on the [Github issues](https://github.com/cfsengineering/CEASIOMpy/issues) 


### Writing a new module

If you want to write a new module you can use the [Module Template](https://github.com/cfsengineering/CEASIOMpy/tree/master/ceasiompy/ModuleTemplate) to help you. Maybe it is also a good idea to contact the CEASIOMpy team which could help you to write the module and be sure it is coherent with the rest of the project.