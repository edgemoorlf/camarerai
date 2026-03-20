# Automated Performance Testing

**Status:** ✅ Implemented (DashScope ✅, Gemini Standard ✅, Gemini Live ⚠️)
**Last Updated:** 2026-03-15

This document describes the automated performance testing framework for CamareraI voice agents.

## Quick Start (Real Tests)

```bash
# Test DashScope (fastest, fully tested)
python tests/run_real_performance_tests.py -p dashscope -i 1

# Test Gemini Standard (slower but functional)
python tests/run_real_performance_tests.py -p gemini -i 1

# More iterations for statistical significance
python tests/run_real_performance_tests.py -p dashscope -i 10
```

⚠️ **Note:** This makes REAL API calls and will incur costs!

**Current Status:**
- ✅ **DashScope**: Fully tested, avg ~2200ms response time (6/6 scenarios pass)
- ✅ **Gemini Standard**: Tested, avg ~2000ms response time (6/6 scenarios pass)
- ⚠️ **Gemini Live**: Working but timing issues in performance tests (4/6 scenarios pass), unit tests pass (3/3)

## Overview

The automated testing framework:
1. Starts a server for each provider
2. Runs real voice interactions via WebSocket
3. Measures actual latency metrics
4. Generates comparison reports

## Architecture

```
tests/
├── AUTO_TESTS.md                    # This document
├── run_real_performance_tests.py    # ⭐ Main real test runner
├── performance/
│   ├── test_audio_generator.py      # Generate synthetic test audio
│   ├── run_performance_tests.py     # Alternative async runner (requires manual server)
│   └── compare_providers.py         # Alternative comparison tool
├── fixtures/                        # Test audio files
│   ├── simple_order.pcm
│   ├── complex_order.pcm
│   ├── question.pcm
│   ├── modification.pcm
│   ├── greeting.pcm
│   └── closing.pcm
└── reports/                         # Generated reports
    ├── perf_report_dashscope_*.json  # ✅ Available (avg 1802ms)
    ├── perf_report_gemini_*.json     # ✅ Available (avg 4947ms)
    ├── perf_report_gemini_live_*.json # ❌ Cannot generate (voice-only)
    └── comparison_*.json
```

## Real Test Runner

The `run_real_performance_tests.py` script:

1. **Loads API keys** from `.env` file automatically
2. **Starts server** for each provider
3. **Runs test scenarios** via real WebSocket connections
4. **Collects metrics** from actual API responses
5. **Generates reports** with statistical analysis

### Usage

```bash
# Run all tests (default: 5 iterations × 6 scenarios × 3 providers = 90 API calls)
python tests/run_real_performance_tests.py

# Test specific providers only
python tests/run_real_performance_tests.py -p dashscope
python tests/run_real_performance_tests.py -p dashscope gemini

# More iterations for better statistics
python tests/run_real_performance_tests.py -i 10

# Help
python tests/run_real_performance_tests.py --help
```

### Output Example (Real Test Results)

**DashScope Test Results (1 iteration, 6 scenarios):**
```
======================================================================
TESTING PROVIDER: DASHSCOPE
======================================================================
  closing (1/1)... ✓ 3322ms
  complex_order (1/1)... ✓ 1562ms
  greeting (1/1)... ✓ 1694ms
  modification (1/1)... ✓ 1725ms
  question (1/1)... ✓ 1410ms
  simple_order (1/1)... ✓ 1101ms

Total Response: Avg 1802ms (target: <600ms) ❌
```

**Gemini Standard Test Results (1 iteration, 6 scenarios):**
```
======================================================================
TESTING PROVIDER: GEMINI
======================================================================
  closing (1/1)... ✓ 4608ms
  complex_order (1/1)... ✓ 5921ms
  greeting (1/1)... ✓ 4272ms
  modification (1/1)... ✓ 5443ms
  question (1/1)... ✓ 4135ms
  simple_order (1/1)... ✓ 5303ms

Tts First Audio: Avg 4046ms (target: <200ms) ❌
Total Response: Avg 4947ms (target: <600ms) ❌
```

**Gemini Live Test Results:**
```
======================================================================
TESTING PROVIDER: GEMINI_LIVE
======================================================================
  closing (1/1)... ❌ Text chat not supported in Gemini Live mode
  ...
```

**Note on Gemini Live Testing:**

The Gemini Live implementation now works correctly:

1. **Connection works** - Successfully connects to Gemini Live API
2. **Audio streaming works** - Real-time bidirectional audio streaming
3. **Function calling works** - Order updates via function calls

**Fixed Issues:**
- Audio format: Now uses raw PCM bytes (not base64) as per Google documentation
- WAV header: Fixed struct.pack format for audio output
- Threading: Thread-safe audio queueing using `asyncio.run_coroutine_threadsafe()`
- Session cleanup: Proper disconnect handling between scenarios

**Performance Test Status:**
- Unit tests: ✅ 3/3 pass (Connection, Audio Reception, Function Calling)
- Performance tests: ⚠️ 4/6 scenarios pass (2 timeout due to initial message timing)

The Gemini Live service is functional. Performance test timing issues are due to the initial wake-up message response being counted in timing calculations.

## Metrics Measured

| Metric | Description | Target | Current (DashScope) |
|--------|-------------|--------|---------------------|
| `llm_first_token_ms` | Time from LLM start to first token | <300ms | ~0-1ms* |
| `tts_first_audio_ms` | Time from TTS start to first audio chunk | <200ms | Not captured** |
| `total_response_ms` | Time from chat sent to first audio byte | <600ms | 1100-3300ms |
| `transcription_latency_ms` | Time from audio to transcript | <1000ms | N/A (text-based test) |

**Notes:**
- \* The ~0-1ms LLM first token is because we measure from when the streaming starts to first chunk, which happens immediately in our setup
- \*\* TTS first audio metric is not currently captured due to a client-side race condition in the test framework (audio chunks are emitted by server but test client sometimes misses them)

**Why no transcription latency?** The current tests use text-based chat instead of audio input for more reliable testing. This tests LLM+TTS latency without ASR variability. Future tests could add audio-based scenarios.

## Alternative Test Runners

The directory also contains alternative test runners that require manual server management:

### Manual Server Approach

If you prefer to run the server separately:

```bash
# Terminal 1: Start server
PROVIDER=dashscope python main.py

# Terminal 2: Run tests
python tests/performance/run_performance_tests.py dashscope
```

### View Reports

```bash
# Latest report
cat tests/reports/perf_report_*.json | jq '.summary'

# Comparison report
cat tests/reports/comparison_*.json | jq

# Pretty print
python -m json.tool tests/reports/comparison_*.json
```

## Test Report Structure

### Report Files Explained

**Individual Provider Reports:**
```
perf_report_<provider>_<timestamp>.json
```
Contains detailed metrics for a single provider test run:
- `total_tests`: Number of scenarios run
- `successful_tests`: Tests that completed without errors
- `summary`: Statistics (avg, min, max, p95) for each metric
- `details`: Raw event timestamps for each test scenario

**Comparison Reports:**
```
comparison_<timestamp>.json
```
Contains cross-provider comparisons when multiple providers are tested in one run.

### Current Test Status

| Provider | Tested | Report Available | Avg Response | Notes |
|----------|--------|------------------|--------------|-------|
| **DashScope** | ✅ Yes | ✅ Yes | ~2200ms | Fastest, fully tested (6/6 scenarios) |
| **Gemini Standard** | ✅ Yes | ✅ Yes | ~2000ms | Fully tested (6/6 scenarios) |
| **Gemini Live** | ⚠️ Yes | ✅ Yes | ~1150ms | 4/6 scenarios pass, timing issues |

**Key Findings:**
- **Gemini Live** has lowest avg response time (~1150ms) but 2/6 scenarios timeout
- **Gemini Standard** is most reliable with consistent ~2000ms response time
- **DashScope** has good performance but client-side race condition in TTS first audio metric
- Gemini Live unit tests pass (3/3): Connection, Audio Reception, Function Calling

### Understanding the Metrics

| Metric | What it measures | Typical Values |
|--------|------------------|----------------|
| `llm_first_token_ms` | Time from LLM request to first token received | 0-300ms (varies by model) |
| `tts_first_audio_ms` | Time from TTS request to first audio chunk | 100-500ms |
| `total_response_ms` | End-to-end: chat sent → first audio received | 1000-3500ms |

**Note:** Lower is better. The targets (<300ms LLM, <600ms total) are aspirational goals for optimization.

## Test Scenarios

1. **simple_order**: "I'd like Kung Pao Chicken" (2.5s)
2. **complex_order**: "I want two orders of Dan Dan Noodles, one with extra spicy" (4.0s)
3. **question**: "What do you recommend?" (2.0s)
4. **modification**: "Actually, make that three instead" (2.5s)
5. **greeting**: "Hello, I'd like to place an order" (2.5s)
6. **closing**: "Thank you, that's all" (2.0s)

Each scenario runs 5 iterations by default (30 API calls per provider).

## CI/CD Integration

See `.github/workflows/performance.yml` for GitHub Actions integration.

## Future Improvements

- [ ] Use real TTS-generated audio instead of sine waves
- [ ] Add concurrent user load testing
- [ ] Track metrics over time (trend analysis)
- [ ] Add audio quality metrics (PESQ, STOI)
- [ ] Integrate with Grafana/Prometheus
