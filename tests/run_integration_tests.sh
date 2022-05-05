#!/usr/bin/env bash

# Color for output
RED='\033[1;31m'
GREEN='\033[1;32m'
NC='\033[0m' # No Color

# Path definitions
logfile="../../ceasiompy.log"
workflow_test_dir="workflow_tests"
cpacs_test_file="../Test_input.xml"

# Remove previous workflow directory and create new one
rm -rf "$workflow_test_dir"
mkdir -p "$workflow_test_dir"
cd "$workflow_test_dir"


function get_test_result {
    if grep -q "###  End of the workflow" "$logfile"; then
        result="PASSED"
        color="$GREEN"
    else
        result="FAILED"
        color="$RED"
    fi
    echo "$result" "$color"
}


echo -e "\n################# Running Integration tests #################\n"

echo -e "Running Integration test 1..."
echo -e "$cpacs_test_file --> PyTornado -->  SkinFriction --> ExportCSV"
nohup ceasiompy_run -m "$cpacs_test_file" PyTornado SkinFriction ExportCSV
read -r test1_result test1_color <<< $(get_test_result) 
printf "${test1_color}$test1_result${NC} \n"


echo -e "\nRunning Integration test 2..."
echo -e "$cpacs_test_file --> CPACS2SUMO --> SUMOAutoMesh --> SU2Run"
nohup ceasiompy_run -m "$cpacs_test_file" CPACS2SUMO SUMOAutoMesh SU2Run
read -r test2_result test2_color <<< $(get_test_result)
printf "${test2_color}$test2_result${NC} \n"


echo -e "\nRunning Integration test 3... "
echo -e "$cpacs_test_file --> CPACS2GMSH  --> SU2Run"
nohup ceasiompy_run -m "$cpacs_test_file" CPACS2GMSH SU2Run
read -r test3_result test3_color <<< $(get_test_result) 
printf "${test3_color}$test3_result${NC} \n"


printf "\n\n#############################\n"
printf "Summary of integration tests\n"
printf "Test 1: ${test1_color}$test1_result${NC} \n"
printf "Test 2: ${test2_color}$test2_result${NC} \n"
printf "Test 3: ${test3_color}$test3_result${NC} \n"
printf "#############################\n"
cd ..
