#!/bin/bash

set -e

export PYTHONPATH='/Users/sam/projects/taskmanagement/'
export ENVIRONMENT=test

# Setup logging
LOG_DIR="/tmp/parallel_test_results"
mkdir -p "$LOG_DIR"

# Function to log messages with timestamp
log_message() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$LOG_DIR/parallel_tests.log"
}

log_message "Starting parallel test execution with file-based distribution"

# Run the black linter first
log_message "Running linter..."
./scripts/run_linter.sh

# Clean up any existing log files
rm -f $LOG_DIR/*

# Discover and split test files
# log_message "Discovering test files and splitting into buckets..."
python scripts/discover_test_files.py --show-buckets > "$LOG_DIR/test_distribution.txt" 2>&1

# Get the bucket information
BUCKET_INFO=$(python scripts/discover_test_files.py)

# Parse bucket information
TOTAL_FILES=$(echo "$BUCKET_INFO" | grep "Total test files:" | cut -d' ' -f4)
NUM_BUCKETS=$(echo "$BUCKET_INFO" | grep "Number of buckets:" | cut -d' ' -f4)

log_message "Discovered $TOTAL_FILES test files, splitting into $NUM_BUCKETS buckets"

# Function to run a worker with specific test files
run_worker() {
    local worker_id=$1
    local test_files="${*:2}"
    local num_files=$(echo "$test_files" | wc -w | tr -d ' ')
    
    # log_message "Starting worker $worker_id with $(echo "$test_files" | wc -w | tr -d ' ') test files: ${test_files} "
    
    # Set the worker ID in environment for the worker script
    export WORKER_ID=$worker_id
    
    # Run the worker script with the assigned test files
    python scripts/run_test_worker.py --worker-id $worker_id --test-files $test_files
    
    return $?
}

# Extract test files for each bucket and launch workers
# log_message "Launching workers with distributed test files..."

# Launch all workers in parallel and capture their PIDs
pids=()
for i in $(seq 0 $((NUM_BUCKETS - 1))); do
    # Extract test files for this bucket
    bucket_files=$(echo "$BUCKET_INFO" | grep "BUCKET_$i:" | cut -d' ' -f2-)
    
    if [ -n "$bucket_files" ]; then
        run_worker $i "$bucket_files" &
        pids+=($!)
    fi
done

# Wait for all processes and collect exit codes
failed_workers=()
for i in $(seq 0 $((NUM_BUCKETS - 1))); do
    if [ -n "${pids[$i]}" ]; then
        wait ${pids[$i]}
    fi
done

log_message "Parallel test execution completed successfully!"
# log_message "Test distribution details saved to $LOG_DIR/test_distribution.txt" 