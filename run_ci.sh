#!/usr/bin/env bash

# To run the CI localy:
# >> ./run_ci.sh

echo -e "\n######### Running CI #########"

echo -e "\n## Running Black ## \n"
black .
TODO uncomment when some files will be cleaned

echo -e "\n## Running Flake8 ## \n"
flake8

echo -e "\n## Running Pytest ## \n"
pytest -v --cov=ceasiompy
