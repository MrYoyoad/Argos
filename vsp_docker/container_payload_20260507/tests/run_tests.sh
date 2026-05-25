#!/bin/bash
set -e

echo "=== Running VSP Pipeline Tests ==="
echo ""

# Setup test environment
export PYTHONPATH="/home/ubuntu/VSP-LLM/src:/home/ubuntu/auto_avsr:/home/ubuntu/av_hubert:$PYTHONPATH"

# Check if pytest is installed
if ! command -v pytest &> /dev/null; then
    echo "ERROR: pytest not found. Please install with: pip install pytest pytest-cov"
    exit 1
fi

# Create test fixtures if needed
mkdir -p /home/ubuntu/tests/fixtures/expected_outputs

# Display test configuration
echo "Test Configuration:"
echo "  PYTHONPATH: $PYTHONPATH"
echo "  Working directory: $(pwd)"
echo "  Pytest version: $(pytest --version)"
echo ""

# Run unit tests
echo "=== Running Unit Tests ==="
echo ""
pytest /home/ubuntu/tests/unit/ -v --tb=short

echo ""
echo "=== Unit Tests Complete ==="
echo ""

# Run integration tests (if they exist and are implemented)
if [ -d "/home/ubuntu/tests/integration" ] && [ "$(ls -A /home/ubuntu/tests/integration/*.py 2>/dev/null)" ]; then
    echo "=== Running Integration Tests ==="
    echo ""
    pytest /home/ubuntu/tests/integration/ -v --tb=short
    echo ""
    echo "=== Integration Tests Complete ==="
    echo ""
else
    echo "=== Integration Tests ==="
    echo "  (No integration tests found - skipping)"
    echo ""
fi

# Run with coverage if requested
if [ "$1" = "--coverage" ]; then
    echo "=== Running Tests with Coverage ==="
    echo ""
    pytest /home/ubuntu/tests/ \
        --cov=/home/ubuntu/VSP-LLM/scripts \
        --cov=/home/ubuntu/auto_avsr/preparation \
        --cov-report=html \
        --cov-report=term
    echo ""
    echo "Coverage report generated at: htmlcov/index.html"
fi

echo ""
echo "✓ All tests passed!"
