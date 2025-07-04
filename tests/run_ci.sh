#!/usr/bin/env bash

export PYTHONPATH="$(pwd)/../src"

Help()
{
   echo "CEASIOMpy run Continuous Integration tests (Unit and Integration)"
   echo
   echo "Syntax: ./run_ci [-f|g|h|i|u]"
   echo "options:"
   echo "-f     Fast mode (skip tests marked as 'slow')"
   echo "-h     Print this help message."
   echo "-i     Skip integration tests."
   echo "-u     Skip unit tests."
   echo
}

run_black()
{
    echo -e "\n-----------"
    echo -e "|  Black  |"
    echo -e "-----------\n"
    black ./
}

run_flake8()
{
    echo -e "\n------------"
    echo -e "|  Flake8  |"
    echo -e "------------\n"
    flake8 ./
    if [ $? == 0 ]; then
        echo -e "Flake8 passed without error\n"
    fi
}

run_unit_tests()
{
    echo -e "\n----------------"
    echo -e "|  Unit tests  |"
    echo -e "----------------\n"
    if [ "$unit" == false ]; then
        echo -e "Skipping...\n"
        return 0
    fi
    
    echo -e "\nRunning..."
    pytest -v src/ceasiompy/ -k "not integration" --cov=src/ceasiompy --cov-report xml:coverage.xml --disable-warnings --ignore=installation/Pentagrow/include/nlopt/test/

}

run_integration_tests()
{
    
    echo -e "\n-----------------------"
    echo -e "|  Integration tests  |"
    echo -e "-----------------------\n"
    if [ "$integration" == false ]; then
        echo -e "Skipping...\n"
        return 0
    fi

    echo -e "Running..."
    if [ "$fast" = true ]; then
        pytest -v tests/ -k "integration" -m "not slow" --cov=src/ceasiompy --cov-report xml:coverage.xml --disable-warnings --ignore=installation/Pentagrow/include/nlopt/test/
    else
        pytest -v tests/ -k "integration" --cov=src/ceasiompy --cov-report xml:coverage.xml --disable-warnings --ignore=installation/Pentagrow/include/nlopt/test/
    fi

}

integration=true
fast=false
unit=true

for i in "$@" 
do
    if [ "$i" == "-f" ]; then
        fast=true;
    fi
    if [ "$i" == "-i" ]; then
        integration=false;
    fi
    if [ "$i" == "-u" ]; then
        unit=false;
    fi
    if [ "$i" == "-h" ] || [ "$i" == "--help" ]; then
        Help
        exit
    fi
done

echo -e "\n################################"
echo -e "######### CEASIOMpy CI #########"
echo -e "################################"

run_black
run_flake8
run_unit_tests
run_integration_tests 

# Generate the list of module to remove from the code coverage
python ../src/ceasiompy/utils/moduleinterfaces.py
