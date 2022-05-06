#!/usr/bin/env bash

# To run the CI localy:
# >> ./run_ci.sh

echo -e "\n######### Running CI #########"

echo -e "\n## Running Black ## \n"
black ../

echo -e "\n## Running Flake8 ## \n"
flake8 ../

echo -e "\n## Running Pytest ## \n"
pytest -v ../ceasiompy --cov-report html:unittest_cov_html --cov-report term --cov=../ceasiompy --cov-config=../pyproject.toml --disable-warnings

# # TODO get args for option gui and longrun
echo -e "\n## Running Integration tests ## \n"
pytest -v . --cov-report html:integration_cov_html --cov-report term --cov=../ceasiompy --cov-config=../pyproject.toml --disable-warnings
# -m "not gui and not slow"
