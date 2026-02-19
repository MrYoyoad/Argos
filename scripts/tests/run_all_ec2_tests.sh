#!/usr/bin/env bash
# ==================================================
# EC2 Test Suite Runner
# ==================================================
# Runs all EC2 tests and provides comprehensive report

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo ""
echo "=================================================="
echo "EC2 Test Suite Runner"
echo "=================================================="
echo ""
echo "This will run all EC2 validation tests to ensure"
echo "the updated pipeline still works correctly on EC2."
echo ""
echo "Tests to run:"
echo "  1. Environment detection and path resolution"
echo "  2. Pipeline module functionality"
echo "  3. Pipeline smoke test (dependencies and files)"
echo ""

# Make test scripts executable
chmod +x "$SCRIPT_DIR/test_ec2_environment.sh" 2>/dev/null || true
chmod +x "$SCRIPT_DIR/test_pipeline_modules.sh" 2>/dev/null || true
chmod +x "$SCRIPT_DIR/test_pipeline_smoke.sh" 2>/dev/null || true

TEST_RESULTS=()
TOTAL_TESTS=0
TOTAL_PASSED=0
TOTAL_FAILED=0

run_test() {
    local test_name="$1"
    local test_script="$2"

    echo ""
    echo "=================================================="
    echo -e "${BLUE}Running: $test_name${NC}"
    echo "=================================================="
    echo ""

    if [ ! -f "$test_script" ]; then
        echo -e "${RED}ERROR: Test script not found: $test_script${NC}"
        TEST_RESULTS+=("✗ $test_name - SCRIPT NOT FOUND")
        return 1
    fi

    local start_time=$(date +%s)

    if bash "$test_script"; then
        local end_time=$(date +%s)
        local duration=$((end_time - start_time))
        echo ""
        echo -e "${GREEN}✓ $test_name PASSED${NC} (${duration}s)"
        TEST_RESULTS+=("✓ $test_name PASSED (${duration}s)")
        return 0
    else
        local end_time=$(date +%s)
        local duration=$((end_time - start_time))
        echo ""
        echo -e "${RED}✗ $test_name FAILED${NC} (${duration}s)"
        TEST_RESULTS+=("✗ $test_name FAILED (${duration}s)")
        return 1
    fi
}

# ==================================================
# Run All Tests
# ==================================================

echo -e "${YELLOW}Starting test suite...${NC}"
echo ""

# Test 1: Environment Detection
if run_test "Environment Detection" "$SCRIPT_DIR/test_ec2_environment.sh"; then
    ((TOTAL_PASSED++))
else
    ((TOTAL_FAILED++))
fi

((TOTAL_TESTS++))

# Test 2: Module Functionality
if run_test "Module Functionality" "$SCRIPT_DIR/test_pipeline_modules.sh"; then
    ((TOTAL_PASSED++))
else
    ((TOTAL_FAILED++))
fi

((TOTAL_TESTS++))

# Test 3: Pipeline Smoke Test
if run_test "Pipeline Smoke Test" "$SCRIPT_DIR/test_pipeline_smoke.sh"; then
    ((TOTAL_PASSED++))
else
    ((TOTAL_FAILED++))
fi

((TOTAL_TESTS++))

# ==================================================
# Final Summary
# ==================================================

echo ""
echo ""
echo "=================================================="
echo "FINAL TEST SUMMARY"
echo "=================================================="
echo ""

for result in "${TEST_RESULTS[@]}"; do
    if [[ $result == ✓* ]]; then
        echo -e "${GREEN}$result${NC}"
    else
        echo -e "${RED}$result${NC}"
    fi
done

echo ""
echo "=================================================="
echo "Total Tests: $TOTAL_TESTS"
echo -e "Passed: ${GREEN}$TOTAL_PASSED${NC}"
echo -e "Failed: ${RED}$TOTAL_FAILED${NC}"
echo "=================================================="
echo ""

if [ $TOTAL_FAILED -eq 0 ]; then
    echo -e "${GREEN}╔════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║  ✓ ALL EC2 TESTS PASSED SUCCESSFULLY  ║${NC}"
    echo -e "${GREEN}╚════════════════════════════════════════╝${NC}"
    echo ""
    echo "The pipeline is ready for use on EC2!"
    echo ""
    echo "Next steps:"
    echo "  - All environment detection working correctly"
    echo "  - All modules functional and properly exported"
    echo "  - All dependencies and files present"
    echo "  - Ready to run the full pipeline"
    echo ""
    exit 0
else
    echo -e "${RED}╔════════════════════════════════════════╗${NC}"
    echo -e "${RED}║  ✗ SOME EC2 TESTS FAILED               ║${NC}"
    echo -e "${RED}╚════════════════════════════════════════╝${NC}"
    echo ""
    echo "Please review the failures above and fix them before"
    echo "running the pipeline on EC2."
    echo ""
    echo "Check individual test logs for detailed error messages."
    echo ""
    exit 1
fi
