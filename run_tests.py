#!/usr/bin/env python
"""
Test runner for the poker game project.
Discovers and runs all unit tests.
"""
import unittest
import sys
import os


def run_tests():
    """Discover and run all tests in the tests directory."""
    # Ensure that the tests directory is in the path
    sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
    
    # Discover tests
    loader = unittest.TestLoader()
    tests = loader.discover(start_dir='tests', pattern='test_*.py')
    
    # Run tests
    test_runner = unittest.TextTestRunner(verbosity=2)
    result = test_runner.run(tests)
    
    return result.wasSuccessful()


if __name__ == "__main__":
    print("Running poker game tests...")
    success = run_tests()
    
    if success:
        print("All tests passed!")
        sys.exit(0)
    else:
        print("Some tests failed!")
        sys.exit(1)