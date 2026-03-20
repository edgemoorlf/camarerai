# Tests

This directory contains all tests, separate from implementation code.

## Test Structure

Tests are organized by provider:

```
tests/
├── dashscope/                     # DashScope provider tests
│   ├── test_dashscope.py          # Integration tests
│   └── test_performance.py        # Performance tests
├── gemini/                        # Gemini Standard provider tests
│   ├── test_gemini.py
│   └── test_performance.py
├── gemini_live/                   # Gemini Live provider tests
│   ├── test_gemini_live.py        # Integration tests
│   ├── test_performance.py        # Performance tests
│   └── test_unit.py               # Unit tests (no server required)
├── fixtures/                      # Shared test audio files
└── reports/                       # Test reports (legacy)
```

Implementation code is in `camarerai/`:

```
camarerai/
├── common/                        # Shared models, routes, services, utils
├── providers/
│   ├── dashscope/                 # DashScope implementation
│   ├── gemini/                    # Gemini Standard implementation
│   └── gemini_live/               # Gemini Live implementation
```

## Running Tests

### Unit Tests (No Server Required)
```bash
# Gemini Live unit tests
python tests/gemini_live/test_unit.py
```

### Integration Tests
```bash
# DashScope tests
python tests/dashscope/test_dashscope.py -i 3

# Gemini Standard tests
python tests/gemini/test_gemini.py -i 3

# Gemini Live tests
python tests/gemini_live/test_gemini_live.py -i 1
```

### Performance Tests
```bash
# DashScope performance
python tests/dashscope/test_performance.py -i 5

# Gemini Standard performance
python tests/gemini/test_performance.py -i 5

# Gemini Live performance
python tests/gemini_live/test_performance.py -i 3
```

## Shared Test Fixtures

- `fixtures/` - Test audio files (PCM format for audio-based tests)
- `generate_test_audio.py` - Script to generate test audio using TTS
- `reports/` - Legacy test reports

## Documentation

- `AUTO_TESTS.md` - Automated testing documentation
- `MANUAL_TEST_GUIDE.md` - Manual testing guide

## Legacy Files

The following files are kept for reference but are no longer actively used:
- `test_all.py` - Old test runner
- `TEST_RESULTS.md` - Old test results
- `run_real_performance_tests.py` - Consolidated test runner (use provider-specific tests instead)
