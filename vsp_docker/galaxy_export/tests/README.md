# VSP Pipeline Test Suite

This directory contains unit and integration tests for the VSP pipeline segment-level architecture.

## Test Structure

```
tests/
├── unit/                           # Unit tests
│   ├── test_overlap_parameters.py  # Overlap calculation tests
│   ├── test_segment_grouping.py    # Segment ID parsing tests
│   └── test_wer_calculation.py     # WER calculation tests
├── integration/                    # Integration tests (future)
├── fixtures/                       # Test fixtures and data
└── run_tests.sh                    # Test runner script
```

## Running Tests

### Prerequisites

Install pytest:
```bash
pip install pytest pytest-cov
```

### Run All Tests

```bash
cd /home/ubuntu/tests
bash run_tests.sh
```

### Run Specific Test File

```bash
pytest tests/unit/test_overlap_parameters.py -v
```

### Run with Coverage

```bash
bash run_tests.sh --coverage
```

This generates an HTML coverage report at `htmlcov/index.html`.

### Run Single Test Function

```bash
pytest tests/unit/test_wer_calculation.py::TestWERCalculation::test_wer_calculation_basic -v
```

## Test Coverage

### Unit Tests

1. **test_overlap_parameters.py** - Tests overlap and segmentation logic:
   - 2-second overlap creates 10s stride (12s - 2s)
   - Videos <12s don't get split
   - Videos ≥12s split properly
   - Frame calculations match time calculations

2. **test_segment_grouping.py** - Tests segment ID parsing and grouping:
   - Parses segment IDs with hash: `VideoA__abc12345_00_000000_000300`
   - Parses segment IDs without hash: `Obama_00_000000_000300`
   - Groups segments by original video
   - Handles out-of-order segments

3. **test_wer_calculation.py** - Tests WER calculation with overlap:
   - Basic editdistance calculation
   - Overlap deduplication (skips ~17% of words at boundaries)
   - Single and multiple segment concatenation
   - End-to-end WER calculation

### Integration Tests (Future)

Planned integration tests:
- Full preprocessing with 2s overlap
- Report generation shows all segments
- Burned video generation (one per segment)
- No merged output generated
- Per-video WER calculation script

## Test Philosophy

- **Unit tests**: Fast, focused tests of individual functions
- **Integration tests**: Slower tests of full pipeline stages
- **Fixtures**: Minimal test data for reproducible tests

## Continuous Testing

To run tests automatically before commits, add a git hook:

```bash
cat > .git/hooks/pre-commit << 'EOF'
#!/bin/bash
pytest tests/unit/ -q
if [ $? -ne 0 ]; then
    echo "Unit tests failed. Commit aborted."
    exit 1
fi
EOF
chmod +x .git/hooks/pre-commit
```

## Adding New Tests

1. Create test file in `tests/unit/` or `tests/integration/`
2. Follow naming convention: `test_*.py`
3. Use pytest fixtures and assertions
4. Run tests to verify they pass
5. Update this README if adding new test categories

## Troubleshooting

### Import Errors

If you get import errors, ensure PYTHONPATH is set:
```bash
export PYTHONPATH="/home/ubuntu/VSP-LLM/src:/home/ubuntu/auto_avsr:/home/ubuntu/av_hubert:$PYTHONPATH"
```

### Module Not Found

If specific modules are missing:
```bash
# For auto_avsr
source ~/auto_avsr/pre-process-venv/bin/activate

# For VSP-LLM
source ~/vsp-llm-yoad-venv/bin/activate
```

### Test Failures

1. Check that overlap parameters in pipeline match test expectations (2s overlap, 12s segments)
2. Verify segment ID format matches actual preprocessed files
3. Run individual test with `-vv` for detailed output:
   ```bash
   pytest tests/unit/test_overlap_parameters.py::TestOverlapParameters::test_overlap_2_seconds_12_second_segments -vv
   ```
