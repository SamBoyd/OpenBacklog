#!/bin/bash

set -e

export PYTHONPATH='/Users/sam/projects/taskmanagement/'

echo "Running all tests..."

columns=$(stty size | awk '{print $2}')

echo " "
printf "%0.s-" $(seq 1 $columns)
echo "Running the black linter..."
./scripts/run_linter.sh

echo " "
printf "%0.s-" $(seq 1 $columns)
echo "Running the Unit tests..."
./scripts/run_tests.sh

echo " "
printf "%0.s-" $(seq 1 $columns)
echo "Running the type checker..."
./scripts/run_type_checker.sh

echo " "
printf "%0.s-" $(seq 1 $columns)
echo "Running the mutation tests..."
./scripts/run_mutation_tests.sh

echo " "
printf "%0.s-" $(seq 1 $columns)
echo "Running the end-to-end tests..."
./scripts/run_end_to_end_tests.py

echo "All tests passed! Amazing!"
