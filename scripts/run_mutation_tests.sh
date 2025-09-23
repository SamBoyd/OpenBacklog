#!/bin/bash

# DEPRECATED: Consider using the optimized version instead
# For faster, targeted mutation testing, use: ./scripts/run_mutation_tests_optimized.sh
# The optimized version runs mutations only on relevant test files for each source file.

export PYTHONPATH='/Users/sam/projects/taskmanagement/'

# Run mutation tests 
mutmut run  --use-coverage

mutmut html

open -a "Google Chrome" html/index.html
