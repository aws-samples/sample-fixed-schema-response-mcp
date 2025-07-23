# Fixed Schema Response MCP Server Tests

This directory contains the test suite for the Fixed Schema Response MCP Server.

## Test Structure

The test suite is organized as follows:

- **Unit Tests**: Tests for individual components in isolation
  - `test_schema_validation.py`: Tests for schema validation functionality
  - `test_schema_manager.py`: Tests for schema management
  - `test_response_processor.py`: Tests for response processing
  - `test_request_processor.py`: Tests for request processing
  - `test_server.py`: Tests for the MCP server core

- **Integration Tests**: Tests for component interactions and end-to-end scenarios
  - `integration/test_end_to_end.py`: End-to-end tests for the complete request/response flow
  - `integration/test_performance.py`: Performance tests for throughput, latency, and queue behavior

## Running Tests

You can run the tests using the `run_tests.py` script in the project root:

```bash
# Run all tests
python run_tests.py

# Run with coverage reporting
python run_tests.py --coverage

# Run with coverage and generate HTML report
python run_tests.py --coverage --html

# Run specific tests
python run_tests.py test_schema_validation.py
python run_tests.py integration/test_end_to_end.py
```

Alternatively, you can use pytest directly:

```bash
# Run all tests
pytest

# Run with coverage
coverage run -m pytest
coverage report
coverage html
```

## Test Coverage

The test suite aims to achieve high code coverage across all components. Coverage reports can be generated using the `--coverage` flag with the `run_tests.py` script.

The coverage configuration is defined in the `.coveragerc` file in the project root.

## Adding New Tests

When adding new tests, follow these guidelines:

1. **Unit Tests**: Place unit tests for individual components in the `tests` directory
2. **Integration Tests**: Place integration tests in the `tests/integration` directory
3. **Test Classes**: Use descriptive class names with the `Test` prefix
4. **Test Methods**: Use descriptive method names with the `test_` prefix
5. **Fixtures**: Use pytest fixtures for common setup and teardown
6. **Mocking**: Use unittest.mock for mocking dependencies
7. **Assertions**: Use pytest assertions for verifying results

## Test Dependencies

The test suite requires the following dependencies:

- pytest
- pytest-asyncio (for testing async functions)
- coverage (for generating coverage reports)

These dependencies are included in the project's development requirements.