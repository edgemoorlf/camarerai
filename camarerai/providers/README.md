# Provider Segregation

This directory contains segregated implementations for each AI provider.

## Directory Structure

```
src/
├── main.py                      # Entry point - launches appropriate provider
├── config.py                    # Configuration (API keys, constants)
└── providers/
├── README.md                    # This file
├── common/                      # Shared code
│   ├── models/                  # Data models
│   ├── routes/                  # HTTP API routes
│   ├── services/                # Shared services (order_service, llm_service)
│   └── utils/                   # Shared utilities
│       ├── performance_monitor.py
│       └── streaming_utils.py
├── dashscope/                   # DashScope Provider (ASR + LLM + TTS)
│   ├── voice_agent.py           # Main Flask-SocketIO app
│   ├── asr_vocabulary.py        # ASR hot words for restaurant terms
│   └── services/
│       └── dashscope_service.py # DashScope-specific services
├── gemini/                      # Gemini Standard Provider (ASR + LLM, DashScope TTS)
│   ├── voice_agent.py
│   └── services/
│       └── gemini_standard_service.py
└── gemini_live/                 # Gemini Live Provider (native audio streaming)
    ├── voice_agent.py
    └── services/
        └── gemini_live_service.py

main.py                          # Entry point
config.py                        # Configuration (API keys, constants)
tests/                           # Tests (separate from implementation)
├── dashscope/                     # DashScope tests
│   ├── test_dashscope.py        # Integration tests
│   └── test_performance.py      # Performance tests
├── gemini/                        # Gemini Standard tests
│   ├── test_gemini.py
│   └── test_performance.py
├── gemini_live/                   # Gemini Live tests
│   ├── test_gemini_live.py      # Integration tests
│   ├── test_performance.py      # Performance tests
│   └── test_unit.py             # Unit tests (no server required)
└── fixtures/                      # Shared test audio files
```

## Running Tests

Tests are in the `tests/` directory, separate from implementation code:

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

## Running Voice Agents

Use the main entry point with the `PROVIDER` environment variable:

```bash
# DashScope
PROVIDER=dashscope python main.py

# Gemini Standard
PROVIDER=gemini python main.py

# Gemini Live
PROVIDER=gemini_live python main.py
```

## Provider Comparison

| Provider | ASR | LLM | TTS | Audio Format | Latency |
|----------|-----|-----|-----|--------------|---------|
| **DashScope** | DashScope | DashScope (OpenAI compatible) | DashScope | Streaming PCM | ~2200ms |
| **Gemini** | Gemini (audio to text) | Gemini 1.5 Flash | DashScope | WebM upload | ~2000ms |
| **Gemini Live** | Native (in stream) | Native (in stream) | Native (in stream) | Bidirectional PCM | ~1150ms |

## Notes

- Each provider is completely independent with its own voice_agent.py
- Common code (models, routes, order_service) is shared in `common/`
- Configuration (API keys, constants) is in `src/config.py`
- Tests are segregated so failures in one provider don't affect others
- Reports are saved in each provider's `tests/reports/` directory
