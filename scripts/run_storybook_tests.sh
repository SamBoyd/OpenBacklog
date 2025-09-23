#!/bin/bash

set -e

pushd .
cd static/react-components

echo "Building Storybook for testing..."
npm run build-storybook --quiet

echo "Installing test runner dependencies if not present..."
if ! npm list @storybook/test-runner >/dev/null 2>&1; then
    echo "Installing @storybook/test-runner..."
    npm install --save-dev @storybook/test-runner
fi

if ! npm list concurrently >/dev/null 2>&1; then
    echo "Installing concurrently..."
    npm install --save-dev concurrently
fi

if ! npm list http-server >/dev/null 2>&1; then
    echo "Installing http-server..."
    npm install --save-dev http-server
fi

if ! npm list wait-on >/dev/null 2>&1; then
    echo "Installing wait-on..."
    npm install --save-dev wait-on
fi

echo "Installing/updating Playwright browsers..."
npx playwright install --with-deps

echo "Running Storybook tests..."
# Use concurrently to serve the built storybook and run tests on port 6007 to avoid conflicts
npx concurrently -k -s first -n "SB,TEST" -c "magenta,blue" \
  "npx http-server storybook-static --port 6007 --silent" \
  "npx wait-on http://127.0.0.1:6007 && npx test-storybook --url http://127.0.0.1:6007"

popd
