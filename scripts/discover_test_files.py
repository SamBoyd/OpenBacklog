#!/usr/bin/env python3
"""
Discover all test files in the project and split them into buckets for parallel execution.
"""

import os
import argparse
from pathlib import Path
from typing import List, Dict

# num cpus - 1
DEFAULT_NUM_BUCKETS = os.cpu_count() - 1 if os.cpu_count() is not None else 1 # type: ignore

def discover_test_files(test_dir: str = "tests") -> List[str]:
    """Discover all test files in the project."""
    test_files: List[str] = []
    test_path = Path(test_dir)
    
    if not test_path.exists():
        print(f"Test directory {test_dir} does not exist")
        return []
    
    # Walk through all subdirectories
    for root, _, files in os.walk(test_path):
        for file in files:
            if file.startswith("test_") and file.endswith(".py"):
                # Get relative path from test directory
                rel_path = Path(root) / file
                test_files.append(str(rel_path))
    
    # Sort for consistent ordering
    test_files.sort()
    return test_files

def split_test_files_into_buckets(test_files: List[str], num_buckets: int) -> Dict[int, List[str]]:
    """Split test files into buckets for parallel execution."""
    buckets: Dict[int, List[str]] = {i: [] for i in range(num_buckets)}
    
    for i, test_file in enumerate(test_files):
        bucket_id = i % num_buckets
        buckets[bucket_id].append(test_file)
    
    return buckets

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='Discover and split test files for parallel execution')
    parser.add_argument('--test-dir', default='tests', help='Test directory to scan')
    parser.add_argument('--num-buckets', type=int, default=DEFAULT_NUM_BUCKETS, help='Number of buckets to split files into')
    parser.add_argument('--list-files', action='store_true', help='List all discovered test files')
    parser.add_argument('--show-buckets', action='store_true', help='Show how files are distributed across buckets')
    args = parser.parse_args()
    
    # Discover test files
    test_files = discover_test_files(args.test_dir)
    
    if args.list_files:
        print(f"Discovered {len(test_files)} test files:")
        for test_file in test_files:
            print(f"  {test_file}")
        print()
    
    # Split into buckets
    buckets = split_test_files_into_buckets(test_files, args.num_buckets)
    
    if args.show_buckets:
        print(f"Test files distributed across {args.num_buckets} buckets:")
        for bucket_id in range(args.num_buckets):
            files = buckets[bucket_id]
            print(f"Bucket {bucket_id:2d}: {len(files):2d} files")
            for test_file in files:
                print(f"    {test_file}")
            print()
    
    # Print bucket information for the shell script
    print(f"Total test files: {len(test_files)}")
    print(f"Number of buckets: {args.num_buckets}")
    
    # Print files for each bucket (for shell script consumption)
    for bucket_id in range(args.num_buckets):
        files = buckets[bucket_id]
        print(f"BUCKET_{bucket_id}:{' '.join(files)}")

if __name__ == '__main__':
    main() 