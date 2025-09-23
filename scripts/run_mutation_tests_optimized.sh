#!/bin/bash

# Optimized Mutation Testing Script
# 
# This script runs mutation tests efficiently by targeting only the specific test files
# that correspond to each source file, based on the project's naming conventions:
# - src/module/file.py -> tests/module/test_file.py  
# - src/file.py -> tests/test_file.py
#
# Usage:
#   ./scripts/run_mutation_tests_optimized.sh           # Run all mutation tests
#   ./scripts/run_mutation_tests_optimized.sh --dry-run # Preview what would be tested
#
# Benefits over the original script:
# - Only runs relevant tests for each source file (faster execution)
# - Provides detailed progress tracking and colored output
# - Categorizes results (success/warning/failed/skipped)
# - Comprehensive summary report

export PYTHONPATH='/Users/sam/projects/taskmanagement/'

# Parse command line arguments
DRY_RUN=false
if [[ "$1" == "--dry-run" ]]; then
    DRY_RUN=true
    echo "DRY RUN MODE - Will show what would be tested without running mutations"
    echo ""
fi

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to log with colors
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
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

# Function to run mutation test for a specific file
run_mutation_for_file() {
    local src_file="$1"
    local test_file="$2"
    
    log_info "Testing mutations for: $src_file"
    log_info "Using test file: $test_file"
    
    # Check if test file exists
    if [[ ! -f "$test_file" ]]; then
        log_warning "Test file not found: $test_file - skipping"
        return 0
    fi
    
    # In dry-run mode, just show what would be tested
    if [[ "$DRY_RUN" == "true" ]]; then
        log_success "Would run mutations on $src_file with tests from $test_file"
        return 0
    fi
    
    # Run mutmut for this specific file and test
    mutmut run \
        --paths-to-mutate "$src_file" \
        --tests-dir "$test_file" \
        --use-coverage \
        --simple-output
    
    local exit_code=$?
    
    if [[ $exit_code -eq 0 ]]; then
        log_success "All mutants killed for $src_file"
    elif [[ $exit_code -eq 2 ]]; then
        log_warning "Some mutants survived for $src_file"
    elif [[ $exit_code -eq 4 ]]; then
        log_warning "Some mutants timed out for $src_file"
    elif [[ $exit_code -eq 8 ]]; then
        log_warning "Some mutants caused slow tests for $src_file"
    else
        log_error "Fatal error occurred for $src_file (exit code: $exit_code)"
    fi
    
    return $exit_code
}

# Function to find all Python files in src directory
find_python_files() {
    find src -name "*.py" -type f | grep -v __pycache__ | grep -v __init__.py | sort
}

# Main execution
log_info "Starting optimized mutation testing..."
log_info "Scanning src directory for Python files..."

# Count total files
total_files=$(find_python_files | wc -l)
log_info "Found $total_files Python files to test"

# Track results
declare -a successful_files=()
declare -a failed_files=()
declare -a warning_files=()
declare -a skipped_files=()

current_file=0

# Process each Python file
while IFS= read -r src_file; do
    ((current_file++))
    
    echo ""
    log_info "Processing file $current_file/$total_files: $src_file"
    
    test_file=$(get_test_file "$src_file")
    
    if [[ ! -f "$test_file" ]]; then
        log_warning "No test file found for $src_file (expected: $test_file)"
        skipped_files+=("$src_file")
        continue
    fi
    
    run_mutation_for_file "$src_file" "$test_file"
    exit_code=$?
    
    case $exit_code in
        0)
            successful_files+=("$src_file")
            ;;
        2|4|8)
            warning_files+=("$src_file")
            ;;
        *)
            failed_files+=("$src_file")
            ;;
    esac
    
done < <(find_python_files)

# Generate HTML report (skip in dry-run mode)
if [[ "$DRY_RUN" == "false" ]]; then
    log_info "Generating HTML report..."
    mutmut html
fi

# Summary report
echo ""
echo "=========================================="
log_info "MUTATION TESTING SUMMARY"
echo "=========================================="

log_success "Successfully tested files: ${#successful_files[@]}"
for file in "${successful_files[@]}"; do
    echo "  ✅ $file"
done

if [[ ${#warning_files[@]} -gt 0 ]]; then
    echo ""
    log_warning "Files with warnings (mutants survived/timed out): ${#warning_files[@]}"
    for file in "${warning_files[@]}"; do
        echo "  ⚠️  $file"
    done
fi

if [[ ${#failed_files[@]} -gt 0 ]]; then
    echo ""
    log_error "Failed files: ${#failed_files[@]}"
    for file in "${failed_files[@]}"; do
        echo "  ❌ $file"
    done
fi

if [[ ${#skipped_files[@]} -gt 0 ]]; then
    echo ""
    log_warning "Skipped files (no tests): ${#skipped_files[@]}"
    for file in "${skipped_files[@]}"; do
        echo "  ⏭️  $file"
    done
fi

echo ""
if [[ "$DRY_RUN" == "false" ]]; then
    log_info "Opening HTML report in browser..."
    open -a "Google Chrome" html/index.html
else
    log_info "Dry run completed. Use './scripts/run_mutation_tests_optimized.sh' to run actual mutations."
fi

# Exit with appropriate code
if [[ ${#failed_files[@]} -gt 0 ]]; then
    exit 1
elif [[ ${#warning_files[@]} -gt 0 ]]; then
    exit 2
else
    exit 0
fi 