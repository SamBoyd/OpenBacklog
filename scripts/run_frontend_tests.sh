#!/bin/bash

set -e

pushd .
cd static/react-components
CI=true npm run test --watchAll=false
test_exit_code=$?

popd

exit $test_exit_code