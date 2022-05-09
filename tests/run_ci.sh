#!/usr/bin/env bash

Help()
{
   echo "CEASIOMpy run continuous integration tests (Unit and Integration)"
   echo
   echo "Syntax: ./run_ci [-f|g|h|i|u]"
   echo "options:"
   echo "-f     Fast mode (skip tests marked as 'slow')"
   echo "-g     Run GUI tests, requiring a user interaction (not active by default)."
   echo "-h     Print this help message."
   echo "-i     Skip integration tests."
   echo "-u     Skip unit tests."
   echo
}


gui=false
integration=true
fast=false
unit=true
for i in "$@" 
do
    if [ $i == "-g" ]; then
        gui=true;
    fi
    if [ $i == "-f" ]; then
        fast=true;
    fi
    if [ $i == "-i" ]; then
        integration=false;
    fi
    if [ $i == "-u" ]; then
        unit=false;
    fi
    if [ $i == "-h" ]; then
        Help
        exit
    fi
done


echo -e "\n######### CEASIOMpy CI #########"

echo -e "\n## Black ## \n"
black ../


echo -e "\n## Flake8 ## "
flake8 ../
if [ $? == 0 ]; then
    echo -e "Flake8 passed without error\n"
fi


echo -e "\n## Unit tests ##"
if [ $unit == true ]; then
    echo -e "\nRunning..."
    pytest -v ../ceasiompy --cov-report html:unittest_cov_html --cov-report term --cov=../ceasiompy --cov-config=../pyproject.toml 
    #--disable-warnings
else
    echo -e "Skipping...\n"
fi


echo -e "\n## Integration tests ##"
if [ $integration == true ]; then

    echo -e "Running..."

    if [ "$gui" = true ]; then
        if [ "$fast" = true ]; then
            pytest -v . --cov-report html:integration_cov_html --cov-report term --cov=../ceasiompy --cov-config=../pyproject.toml -m "not slow" --disable-warnings
        else
            pytest -v . --cov-report html:integration_cov_html --cov-report term --cov=../ceasiompy --cov-config=../pyproject.toml --disable-warnings
        fi
    else
        if [ "$fast" = true ]; then
            pytest -v . --cov-report html:integration_cov_html --cov-report term --cov=../ceasiompy --cov-config=../pyproject.toml -m "not gui and not slow" --disable-warnings
        else
            pytest -v . --cov-report html:integration_cov_html --cov-report term --cov=../ceasiompy --cov-config=../pyproject.toml -m "not gui" --disable-warnings
        fi
    fi
else
    echo -e "Skipping...\n"
fi


#
