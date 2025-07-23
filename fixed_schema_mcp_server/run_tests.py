#!/usr/bin/env python3
"""
Script to run tests for the Fixed Schema Response MCP Server.
"""

import unittest
import sys

if __name__ == "__main__":
    # Discover and run tests
    test_suite = unittest.defaultTestLoader.discover("fixed_schema_mcp_server/tests")
    test_runner = unittest.TextTestRunner(verbosity=2)
    result = test_runner.run(test_suite)
    
    # Exit with non-zero code if tests failed
    sys.exit(not result.wasSuccessful())