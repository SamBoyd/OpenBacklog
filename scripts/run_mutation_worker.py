#!/usr/bin/env python3
"""
Mutation worker script for running parallel mutmut sessions.
Each worker uses a separate database and processes different source files.
"""

import os
import sys
import argparse
import logging
import subprocess
from pathlib import Path
from typing import List, Tuple

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def setup_logging(worker_id: int) -> logging.Logger:
    """Setup logging for the mutation worker."""
    logger = logging.getLogger(f"mutation_worker_{worker_id:02d}")
    logger.setLevel(logging.INFO)
    
    # Create formatter
    formatter = logging.Formatter(
        f'%(asctime)s - Mutation Worker {worker_id:02d} - %(levelname)s - %(message)s'
    )
    
    # Create console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    
    # Create file handler
    log_dir = Path("/tmp/parallel_mutation_results")
    log_dir.mkdir(exist_ok=True)
    file_handler = logging.FileHandler(log_dir / f"mutation_worker_{worker_id:02d}.log")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    
    # Add handlers to logger
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    
    return logger


def configure_database_for_worker(worker_id: int, logger: logging.Logger) -> None:
    """Configure environment variables for the worker's database."""
    database_name = f"taskmanager_test_db_{worker_id:02d}"
    
    # Set environment variables
    os.environ['database_name'] = database_name
    os.environ['database_url'] = f"postgresql://taskmanager_test_user:securepassword123@localhost/{database_name}"
    os.environ['PYTHONPATH'] = str(project_root)
    os.environ['ENVIRONMENT'] = 'test'
    os.environ['WORKER_ID'] = str(worker_id)
    
    logger.info(f"Configured database: {database_name}")


def get_test_file(src_file: str) -> str:
    """Map source file to corresponding test file."""
    # Remove 'src/' prefix and '.py' suffix
    base_path = src_file.replace('src/', '').replace('.py', '')
    
    # Convert to test path
    if '/' in base_path:
        # Module file: src/module/file.py -> tests/module/test_file.py
        dir_part, file_part = base_path.rsplit('/', 1)
        return f"tests/{dir_part}/test_{file_part}.py"
    else:
        # Root file: src/file.py -> tests/test_file.py
        return f"tests/test_{base_path}.py"


def run_mutmut_for_file(src_file: str, test_file: str, worker_id: int, logger: logging.Logger) -> int:
    """Run mutmut for a specific source file and test file."""
    logger.info(f"Running mutations for: {src_file} -> {test_file}")
    
    # Check if test file exists
    if not Path(test_file).exists():
        logger.warning(f"Test file not found: {test_file} - skipping")
        return 0  # Skip, not an error
    
    # Create worker-specific mutation cache directory
    cache_dir = f"mutants_worker_{worker_id:02d}"
    Path(cache_dir).mkdir(exist_ok=True)
    
    # Set up environment for mutmut
    env = os.environ.copy()
    env['MUTMUT_CACHE_DIR'] = cache_dir
    
    # Run mutmut command
    cmd = [
        'mutmut', 'run',
        '--paths-to-mutate', src_file,
        '--tests-dir', test_file,
        '--use-coverage',
        '--simple-output'
    ]
    
    logger.debug(f"Running command: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            env=env,
            cwd=project_root
        )
        
        # Log the output
        if result.stdout:
            logger.debug(f"mutmut stdout: {result.stdout}")
        if result.stderr:
            logger.debug(f"mutmut stderr: {result.stderr}")
        
        return result.returncode
        
    except Exception as e:
        logger.error(f"Error running mutmut for {src_file}: {str(e)}")
        return 1


def process_worker_files(worker_id: int, source_files: List[str], logger: logging.Logger) -> Tuple[int, int, int, int]:
    """Process all source files assigned to this worker."""
    success_count = 0
    warning_count = 0
    failed_count = 0
    skipped_count = 0
    
    total_files = len(source_files)
    logger.info(f"Worker {worker_id} processing {total_files} source files")
    
    for i, src_file in enumerate(source_files, 1):
        logger.info(f"Processing file {i}/{total_files}: {src_file}")
        
        # Get corresponding test file
        test_file = get_test_file(src_file)
        
        # Check if test file exists
        if not Path(test_file).exists():
            logger.warning(f"No test file found for {src_file} (expected: {test_file})")
            skipped_count += 1
            continue
        
        # Run mutmut for this file
        exit_code = run_mutmut_for_file(src_file, test_file, worker_id, logger)
        
        # Categorize result
        if exit_code == 0:
            logger.info(f"SUCCESS - All mutants killed for {src_file}")
            success_count += 1
        elif exit_code in [2, 4, 8]:
            logger.warning(f"WARNING - Some mutants survived/timed out for {src_file} (exit code: {exit_code})")
            warning_count += 1
        else:
            logger.error(f"ERROR - Fatal error occurred for {src_file} (exit code: {exit_code})")
            failed_count += 1
    
    return success_count, warning_count, failed_count, skipped_count


def main():
    """Main entry point for the mutation worker."""
    parser = argparse.ArgumentParser(description='Run mutation tests in a worker process')
    parser.add_argument('--worker-id', type=int, required=True, help='Worker ID (0-N)')
    parser.add_argument('--source-files', nargs='*', default=[], help='List of source files to mutate')
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose logging')
    args = parser.parse_args()
    
    worker_id = args.worker_id
    
    # Setup logging
    logger = setup_logging(worker_id)
    if args.verbose:
        logger.setLevel(logging.DEBUG)
    
    logger.info(f"Mutation worker {worker_id} starting")
    logger.info(f"Worker {worker_id} assigned {len(args.source_files)} source files")
    
    # Configure database for this worker
    configure_database_for_worker(worker_id, logger)
    
    # Process assigned files
    success, warning, failed, skipped = process_worker_files(worker_id, args.source_files, logger)
    
    # Log summary
    logger.info(f"Worker {worker_id} completed:")
    logger.info(f"  Success: {success}")
    logger.info(f"  Warning: {warning}")
    logger.info(f"  Failed: {failed}")
    logger.info(f"  Skipped: {skipped}")
    
    # Return appropriate exit code
    if failed > 0:
        return 1
    elif warning > 0:
        return 2
    else:
        return 0


if __name__ == '__main__':
    sys.exit(main())