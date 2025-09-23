#!/bin/bash

export PYTHONPATH='/Users/sam/projects/taskmanagement/'

rm -rf src/__pycache__

# Run mutation tests 
mypy src
