#!/usr/bin/env python3
"""
Test runner for apprise_smart_notification handler.

Usage:
    python run_tests.py                    # Run all tests
    python run_tests.py -v                 # Verbose output
    python run_tests.py --cov              # With coverage report
    python run_tests.py -k test_entry_add  # Run specific test
"""

import sys
import subprocess
from pathlib import Path
import os


def main():
    """Run the test suite."""
    # Get the directory containing this script
    test_dir = Path(__file__).parent

    # Add src directory to PYTHONPATH for the subprocess
    src_path = test_dir.parent.parent.parent / "src"
    env = os.environ.copy()
    if src_path.exists():
        if "PYTHONPATH" in env:
            env["PYTHONPATH"] = f"{src_path}{os.pathsep}{env['PYTHONPATH']}"
        else:
            env["PYTHONPATH"] = str(src_path)

    # Base pytest command
    cmd = [sys.executable, "-m", "pytest", "test_handler.py"]

    # Add common options
    cmd.extend(
        [
            "--asyncio-mode=auto",  # Handle async tests
            "--tb=short",  # Shorter traceback format
        ]
    )

    # Check for coverage flag
    if "--cov" in sys.argv:
        cmd.extend(
            [
                "--cov=apprise_smart_notification",
                "--cov-report=term-missing",
                "--cov-report=html:htmlcov",
            ]
        )
        sys.argv.remove("--cov")

    # Pass through any other arguments
    cmd.extend(sys.argv[1:])

    # Run tests
    print(f"Running: {' '.join(cmd)}")
    print("-" * 60)

    result = subprocess.run(cmd, cwd=test_dir, env=env)
    sys.exit(result.returncode)


if __name__ == "__main__":
    main()
