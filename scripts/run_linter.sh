#!/bin/bash

export PYTHONPATH='/Users/sam/projects/taskmanagement/'

black src tests

isort end_to_end_tests tests src
 