#!/bin/bash

set -e

export PYTHONPATH='/Users/sam/projects/taskmanagement/'
export ENVIRONMENT=test

# Setup logging
LOG_DIR="/tmp/parallel_mutation_results"
mkdir -p "$LOG_DIR"

# Function to log messages with timestamp
log_message() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$LOG_DIR/parallel_mutations.log"
}

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to log with colors
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1" | tee -a "$LOG_DIR/parallel_mutations.log"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1" | tee -a "$LOG_DIR/parallel_mutations.log"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1" | tee -a "$LOG_DIR/parallel_mutations.log"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1" | tee -a "$LOG_DIR/parallel_mutations.log"
}

log_message "Starting parallel mutation testing with file-based distribution"

# Run the black linter first
log_message "Running linter..."
./scripts/run_linter.sh

# Clean up any existing log files
rm -f $LOG_DIR/*

# Get number of CPU cores and calculate workers (num_cpus - 1)
NUM_CPUS=$(sysctl -n hw.ncpu)
NUM_WORKERS=$((NUM_CPUS - 1))

log_message "Detected $NUM_CPUS CPU cores, using $NUM_WORKERS workers"

# Function to discover and distribute Python files
discover_and_distribute_files() {
    local num_workers=$1
    
    # Find all Python files in src directory
    local all_files=($(find src -name "*.py" -type f | grep -v __pycache__ | grep -v __init__.py | sort))
    local total_files=${#all_files[@]}
    
    log_message "Found $total_files Python files to distribute among $num_workers workers"
    
    # Calculate files per worker
    local files_per_worker=$((total_files / num_workers))
    local remainder=$((total_files % num_workers))
    
    log_message "Base files per worker: $files_per_worker, remainder: $remainder"
    
    # Distribute files to workers
    local file_index=0
    for ((worker_id=0; worker_id<num_workers; worker_id++)); do
        local worker_files=()
        local worker_file_count=$files_per_worker
        
        # Add one extra file to first 'remainder' workers
        if ((worker_id < remainder)); then
            ((worker_file_count++))
        fi
        
        # Assign files to this worker
        for ((j=0; j<worker_file_count && file_index<total_files; j++)); do
            worker_files+=("${all_files[file_index]}")
            ((file_index++))
        done
        
        # Save worker files to a file for the worker script
        printf '%s\n' "${worker_files[@]}" > "$LOG_DIR/worker_${worker_id}_files.txt"
        
        log_message "Worker $worker_id assigned ${#worker_files[@]} files"
    done
}

# Function to map source file to test file
get_test_file() {
    local src_file="$1"
    
    # Remove 'src/' prefix and '.py' suffix
    local base_path="${src_file#src/}"
    base_path="${base_path%.py}"
    
    # Convert to test path
    if [[ "$base_path" == *"/"* ]]; then
        # Module file: src/module/file.py -> tests/module/test_file.py
        local dir_part="${base_path%/*}"
        local file_part="${base_path##*/}"
        echo "tests/${dir_part}/test_${file_part}.py"
    else
        # Root file: src/file.py -> tests/test_file.py
        echo "tests/test_${base_path}.py"
    fi
}

# Function to run mutation testing for a worker using Python script
run_mutation_worker() {
    local worker_id=$1
    local worker_files_file="$LOG_DIR/worker_${worker_id}_files.txt"
    
    log_message "Starting mutation worker $worker_id"
    
    # Read worker files into array
    local worker_files=()
    while IFS= read -r src_file; do
        [[ -n "$src_file" ]] && worker_files+=("$src_file")
    done < "$worker_files_file"
    
    # Set the worker ID in environment for the worker script
    export WORKER_ID=$worker_id
    
    # Run the Python mutation worker script with the assigned source files
    python scripts/run_mutation_worker.py --worker-id $worker_id --source-files "${worker_files[@]}"
    
    return $?
}

# Discover and distribute files
discover_and_distribute_files $NUM_WORKERS

# Launch all workers in parallel and capture their PIDs
log_message "Launching $NUM_WORKERS mutation workers..."
pids=()
for ((worker_id=0; worker_id<NUM_WORKERS; worker_id++)); do
    run_mutation_worker $worker_id &
    pids+=($!)
done

# Wait for all processes and collect exit codes
worker_results=()
for ((worker_id=0; worker_id<NUM_WORKERS; worker_id++)); do
    wait ${pids[$worker_id]}
    worker_results+=($?)
done

# Aggregate results
total_success=0
total_warning=0
total_failed=0
total_skipped=0

for ((worker_id=0; worker_id<NUM_WORKERS; worker_id++)); do
    worker_log="$LOG_DIR/mutation_worker_$(printf "%02d" $worker_id).log"
    if [[ -f "$worker_log" ]]; then
        success=$(grep "Success:" "$worker_log" | grep -o '[0-9]*' | tail -1)
        warning=$(grep "Warning:" "$worker_log" | grep -o '[0-9]*' | tail -1)
        failed=$(grep "Failed:" "$worker_log" | grep -o '[0-9]*' | tail -1)
        skipped=$(grep "Skipped:" "$worker_log" | grep -o '[0-9]*' | tail -1)
        
        total_success=$((total_success + ${success:-0}))
        total_warning=$((total_warning + ${warning:-0}))
        total_failed=$((total_failed + ${failed:-0}))
        total_skipped=$((total_skipped + ${skipped:-0}))
    fi
done

# Try to generate consolidated HTML report
log_message "Attempting to generate consolidated HTML report..."
mutmut html 2>/dev/null || log_warning "Could not generate consolidated HTML report (expected with parallel workers)"

# Final summary
echo ""
echo "=========================================="
log_info "PARALLEL MUTATION TESTING SUMMARY"
echo "=========================================="
log_success "Total files with all mutants killed: $total_success"
log_warning "Total files with warnings (mutants survived/timed out): $total_warning"
log_error "Total files with errors: $total_failed"
log_warning "Total files skipped (no tests): $total_skipped"

echo ""
log_info "Individual worker logs available in: $LOG_DIR/"
log_info "Worker mutation caches available in: mutants_worker_* directories"

# Determine overall exit code
overall_exit_code=0
if ((total_failed > 0)); then
    overall_exit_code=1
elif ((total_warning > 0)); then
    overall_exit_code=2
fi

log_message "Parallel mutation testing completed with exit code: $overall_exit_code"
exit $overall_exit_code