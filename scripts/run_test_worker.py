#!/usr/bin/env python3
"""
Test worker script for running parallel pytest sessions.
Each worker uses a separate database to avoid conflicts.
"""

import os
import sys
import argparse
import logging
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import pytest
from _pytest.config import Config


os.environ['ENVIRONMENT'] = 'test'

def setup_logging(worker_id: int) -> logging.Logger:
    """Setup logging for the worker."""
    logger = logging.getLogger(f"test_worker_{worker_id:02d}")
    logger.setLevel(logging.INFO)
    
    # Create formatter
    formatter = logging.Formatter(
        f'%(asctime)s - Worker {worker_id:02d} - %(levelname)s - %(message)s'
    )
    
    # Create console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.ERROR)
    console_handler.setFormatter(formatter)
    
    # Create file handler
    log_dir = Path("/tmp/parallel_test_results")
    log_dir.mkdir(exist_ok=True)
    file_handler = logging.FileHandler(log_dir / f"worker_{worker_id:02d}.log")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    
    # Add handlers to logger
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    
    return logger


def configure_database_for_worker(worker_id: int) -> None:
    """Configure environment variables for the worker's database."""
    database_name = f"taskmanager_test_db_{worker_id:02d}"
    
    # Set environment variables
    os.environ['database_name'] = database_name
    os.environ['database_url'] = f"postgresql://taskmanager_test_user:securepassword123@localhost/{database_name}"
    os.environ['PYTHONPATH'] = str(project_root)
    os.environ['ENVIRONMENT'] = 'test'
    
    # Import settings to ensure database URLs are properly constructed
    from src.config import settings
    logger = logging.getLogger(f"test_worker_{worker_id:02d}")
    logger.info(f"Configured database: {settings.database_name}")
    logger.info(f"Database URL: {settings.database_url}")


def pytest_configure_node(node: Config) -> None:
    """Configure pytest node with worker-specific settings."""
    worker_id = int(os.environ.get('WORKER_ID', '0'))
    logger = logging.getLogger(f"test_worker_{worker_id:02d}")
    logger.info(f"Configuring pytest node for worker {worker_id}")


def run_tests_with_pytest_api(worker_id: int, test_files: list[str], logger: logging.Logger) -> int:
    """Run tests using pytest's Python API instead of subprocess."""
    try:
        logger.info(f"Starting test execution for worker {worker_id}")
        logger.info(f"Worker {worker_id} will run {len(test_files)} test files")
        
        if not test_files:
            logger.info(f"Worker {worker_id} has no test files to run")
            return 0
        
        # Configure pytest arguments
        pytest_args = [
            "-n0",  # Disable xdist for individual workers
            "--tb=short",
            "--quiet",
            "--no-cov",
            # "--no-header",
            # "--no-summary"
        ]
        
        # Add test files to arguments
        pytest_args.extend(test_files)
        
        logger.info(f"Worker {worker_id} running: pytest {' '.join(pytest_args)}")
        
        # Run pytest using the Python API
        exit_code = pytest.main(pytest_args)
        
        # if exit_code == 0:
        #     logger.info(f"Worker {worker_id} completed successfully")
        # else:
        #     logger.error(f"Worker {worker_id} failed with exit code {exit_code}")
        
        return exit_code
        
    except Exception as e:
        logger.error(f"Worker {worker_id} encountered an error: {str(e)}", exc_info=True)
        return 1


def main():
    """Main entry point for the test worker."""
    parser = argparse.ArgumentParser(description='Run tests in a worker process')
    parser.add_argument('--worker-id', type=int, required=True, help='Worker ID (0-19)')
    parser.add_argument('--test-files', nargs='*', default=[], help='List of test files to run')
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose logging')
    args = parser.parse_args()
    
    worker_id = args.worker_id
    
    # Setup logging
    logger = setup_logging(worker_id)
    if args.verbose:
        logger.setLevel(logging.DEBUG)
    
    logger.info(f"Worker {worker_id} starting")
    logger.info(f"Worker {worker_id} assigned {len(args.test_files)} test files")
    
    # Configure database for this worker
    configure_database_for_worker(worker_id)
    
    # Run tests
    run_tests_with_pytest_api(worker_id, args.test_files, logger)

if __name__ == '__main__':
    main() 