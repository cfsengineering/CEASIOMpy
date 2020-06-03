#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Aaron Dettmann

import setuptools
import os

from ceasiompy.__version__ import __version__

NAME = 'ceasiompy'
EXCLUDE_DIRS = ['doc', 'test']
VERSION = __version__
AUTHOR = 'CFS Engineering'
EMAIL = 'aidan.jungo@cfse.ch'
DESCRIPTION = 'A conceptual aircraft design environment'
URL = 'https://github.com/cfsengineering/CEASIOMpy'
REQUIRES_PYTHON = '>=3.6.0'
REQUIRED = ['numpy']
README = 'README.rst'
PACKAGE_DIR = '.'
LICENSE = 'LICENSE'


here = os.path.abspath(os.path.dirname(__file__))

with open(os.path.join(here, README), "r") as fp:
    long_description = fp.read()

with open(LICENSE) as f:
    license = f.read()

setuptools.setup(
    name=NAME,
    version=VERSION,
    author=AUTHOR,
    author_email=EMAIL,
    description=DESCRIPTION,
    long_description=long_description,
    url=URL,
    include_package_data=True,
    package_dir={'': PACKAGE_DIR},
    license=license,
    packages=setuptools.find_packages(exclude=EXCLUDE_DIRS),
    python_requires=REQUIRES_PYTHON,
    install_requires=REQUIRED,
    # See: https://pypi.org/classifiers/
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
        "Intended Audience :: Developers",
        "Intended Audience :: Education",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering",
        "Topic :: Scientific/Engineering :: Physics",
    ],
)
