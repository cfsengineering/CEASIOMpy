#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import platform
import setuptools
from pathlib import Path

NAME = "ceasiompy"
EXCLUDE_DIRS = ["test_cases", "test_files", "installation"]
VERSION = "0.2.1"
AUTHOR = "CFS Engineering"
EMAIL = "giacomo.benedetti@cfse.ch"
DESCRIPTION = "A conceptual aircraft design environment"
URL = "https://github.com/cfsengineering/CEASIOMpy"
REQUIRES_PYTHON = ">=3.11.11"
REQUIRED = ["numpy"]
README = "README.md"
PACKAGE_DIR = "src"
LICENSE = "LICENSE"

here = Path(__file__).parent

with open(Path(here, README), "r") as fp:
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
    package_dir={"": PACKAGE_DIR},
    entry_points={'console_scripts': ['ceasiompy_run = src.ceasiompy_package.cli:main_exec']},
    license=license,
    packages=setuptools.find_packages(where=PACKAGE_DIR, exclude=EXCLUDE_DIRS),
    python_requires=REQUIRES_PYTHON,
    install_requires=[],
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
