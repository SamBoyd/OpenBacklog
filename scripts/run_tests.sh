#!/bin/bash

set -e

export ENVIRONMENT=test

# Get terminal width
columns=$(stty size 2>/dev/null | awk '{print $2}' || echo 80)

# Variable to track overall exit status
exit_status=0

# Trap to print final status
cleanup() {
    echo " "
    printf "%0.s=" $(seq 1 $columns)
    if [ $exit_status -eq 0 ]; then
        echo "All tests passed! 🎉"
    else
        echo "Some tests failed! ❌"
    fi
    printf "%0.s=" $(seq 1 $columns)
    exit $exit_status
}

trap cleanup EXIT

# Function to run command and track exit status
run_with_status() {
    if ! "$@"; then
        exit_status=1
    fi
}

# Run the black linter
run_with_status ./scripts/run_linter.sh

# Run the Python unit tests
echo " "
printf "%0.s=" $(seq 1 $columns)
echo "Running Python Unit tests"
printf "%0.s=" $(seq 1 $columns)

run_with_status pytest --cov=src tests/

# Check the react app builds
echo " "
printf "%0.s=" $(seq 1 $columns)
echo "Running React app build check"
printf "%0.s=" $(seq 1 $columns)

run_with_status ./scripts/build_static_files.sh

# Run the frontend unit tests
echo " "
printf "%0.s=" $(seq 1 $columns)
echo "Running Frontend Unit tests"
printf "%0.s=" $(seq 1 $columns)

run_with_status ./scripts/run_frontend_tests.sh


# Run Storybook test
echo " "
printf "%0.s=" $(seq 1 $columns)
echo "Running Storybook tests"
printf "%0.s=" $(seq 1 $columns)

run_with_status ./scripts/run_storybook_tests.sh

# Run the browser functional tests

echo " "
printf "%0.s=" $(seq 1 $columns)
echo "Running Browser Functional tests"
printf "%0.s=" $(seq 1 $columns)

run_with_status pytest browser_functional_tests/
