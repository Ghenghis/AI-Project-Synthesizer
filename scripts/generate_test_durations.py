#!/usr/bin/env python3
"""
Generate test durations file for pytest-split.

This script runs the full test suite once to capture execution times,
then creates a .test_durations file that pytest-split can use for
optimal load balancing across CI shards.

Usage:
    python scripts/generate_test_durations.py
"""

import subprocess
import sys
from pathlib import Path

def main():
    """Generate test durations file."""
    print("Generating test durations for optimal CI sharding...")
    
    # Ensure we're in the project root
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)
    
    # Run pytest with --store-durations
    cmd = [
        sys.executable, "-m", "pytest",
        "--ignore=tests/generated",  # Skip generated tests
        "--store-durations",
        "--durations-path=.test_durations",
        "-q",  # Quiet mode
        "tests",  # All tests, not just unit
    ]
    
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"Error running pytest: {result.stderr}")
        sys.exit(1)
    
    # Check if durations file was created
    durations_file = project_root / ".test_durations"
    if durations_file.exists():
        print(f"✅ Test durations file created: {durations_file}")
        print(f"File size: {durations_file.stat().st_size} bytes")
        
        # Show some stats
        with open(durations_file) as f:
            lines = f.readlines()
            print(f"Number of test entries: {len(lines)}")
        
        print("\nCommit this file to your repository for optimal CI sharding.")
        print("Regenerate monthly or after significant test changes.")
    else:
        print("❌ Test durations file was not created")
        sys.exit(1)

if __name__ == "__main__":
    import os
    main()
