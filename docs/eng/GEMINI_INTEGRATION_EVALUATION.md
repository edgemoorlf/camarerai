# Gemini Integration Evaluation

**Date:** 2026-03-08
**Status:** Test file exists, integration not yet implemented

---

## Current State

### What Exists

1. **Test File:** `tests/test_gemini_api.py`
   - Tests API key validation
   - Tests text generation with `gemini-2.5-flash`
   - Tests streaming generation
   - Tests function calling
   - Tests performance (time to first chunk)

2. **Current Architecture (DashScope only):**
   ```
   voice_agent.py
   ├── DashScopeClient (ASR, TTS)
   ├── OpenAI client (LLM via DashScope compatible API)
   └── LLMService (uses both clients)
   ```

### What Gemini Offers

| Feature | DashScope | Gemini | Notes |
|---------|-----------|--------|-------|
| **ASR** | paraformer-realtime-v2 | Live API (native audio) | Gemini Live API does ASR+LLM+TTS together |
| **LLM** | qwen-turbo/plus | gemini-2.5-flash | Gemini claims ~590ms time to first token |
| **TTS** | qwen3-tts-flash | Live API (native audio) | Gemini Live API is audio-to-audio |
| **Streaming** | ✅ | ✅ | Both support streaming |
| **Function Calling** | ✅ | ✅ | Both support function calling |

### Key Differences

1. **Gemini Live API** is a unified audio-to-audio stream:
   - Input: Audio (microphone)
   - Output: Audio (speaker)
   - LLM processing happens internally
   - Cannot easily mix with other providers

2. **DashScope** has separate services:
   - ASR (Speech → Text)
   - LLM (Text → Text)
   - TTS (Text → Speech)
   - Can mix and match components

---

## Configuration Options

The user wants to configure ASR/LLM/TTS individually using either DashScope or Gemini.

### Option 1: Fully Flexible (Recommended)

Allow any combination:
```python
ASR_PROVIDER = 'dashscope'  # or 'gemini'
LLM_PROVIDER = 'gemini'     # or 'dashscope'
TTS_PROVIDER = 'dashscope'  # or 'gemini'
```

**Pros:**
- Maximum flexibility
- Can use best-of-breed for each service
- Easy A/B testing

**Cons:**
- More complex implementation
- Gemini Live API doesn't fit this model (it's all-in-one)

### Option 2: Provider Sets

Choose entire provider stack:
```python
PROVIDER = 'dashscope'  # or 'gemini'
```

**Pros:**
- Simpler implementation
- Gemini Live API works natively

**Cons:**
- Less flexibility
- Can't mix best components

### Option 3: Hybrid (Recommended Implementation)

Support both modes:
```python
# Mode 1: Use single provider stack
PROVIDER = 'gemini'  # Uses Gemini Live API for everything

# Mode 2: Mix and match (DashScope only for now)
ASR_PROVIDER = 'dashscope'
LLM_PROVIDER = 'gemini'  # Can use Gemini LLM with DashScope ASR/TTS
TTS_PROVIDER = 'dashscope'
```

---

## Implementation Plan

### Phase 1: Configuration Updates

**File:** `config.py`

```python
# Provider Selection
PROVIDER = os.getenv('PROVIDER', 'dashscope')  # 'dashscope' or 'gemini'

# Individual service providers (used when PROVIDER='hybrid')
ASR_PROVIDER = os.getenv('ASR_PROVIDER', 'dashscope')
LLM_PROVIDER = os.getenv('LLM_PROVIDER', 'dashscope')
TTS_PROVIDER = os.getenv('TTS_PROVIDER', 'dashscope')

# API Keys
DASHSCOPE_API_KEY = os.getenv('DASHSCOPE_API_KEY')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

# Model Configuration
GEMINI_LLM_MODEL = 'gemini-2.5-flash'
```

### Phase 2: Abstract Service Interfaces

**File:** `services/base_service.py`

```python
from abc import ABC, abstractmethod

class BaseLLMService(ABC):
    @abstractmethod
    def stream_with_function_calling(self, messages, tools, voice, session_id, emit_func):
        pass

class BaseTTSService(ABC):
    @abstractmethod
    def synthesize(self, text, voice, language_type, stream=False):
        pass
```

### Phase 3: Gemini Service Implementation

**File:** `services/gemini_service.py`

```python
from google import genai
from google.genai import types

class GeminiLLMService(BaseLLMService):
    def __init__(self, api_key, perf_monitor):
        self.client = genai.Client(api_key=api_key)
        self.perf_monitor = perf_monitor

    def stream_with_function_calling(self, messages, tools, voice, session_id, emit_func):
        # Convert OpenAI message format to Gemini format
        # Use gemini-2.5-flash model
        # Support streaming with function calling
        pass
```

### Phase 4: Service Factory

**File:** `services/service_factory.py`

```python
def create_llm_service(provider, perf_monitor):
    if provider == 'gemini':
        return GeminiLLMService(config.GEMINI_API_KEY, perf_monitor)
    elif provider == 'dashscope':
        openai_client = OpenAI(...)
        dashscope_client = DashScopeClient()
        return DashScopeLLMService(openai_client, dashscope_client, perf_monitor)
    else:
        raise ValueError(f"Unknown provider: {provider}")
```

### Phase 5: Voice Agent Updates

**File:** `voice_agent.py`

```python
from services.service_factory import create_llm_service, create_tts_service

# Initialize services based on config
llm_service = create_llm_service(config.LLM_PROVIDER, perf_monitor)
tts_service = create_tts_service(config.TTS_PROVIDER)
```

---

## Estimated Performance Comparison

| Metric | DashScope (Current) | Gemini (Estimated) | Improvement |
|--------|---------------------|-------------------|-------------|
| LLM First Token | ~400-500ms | ~200-300ms | 40-50% faster |
| LLM Total | ~5-7s | ~3-5s | 30-40% faster |
| TTS First Audio | ~2.5-3s | ~500-800ms* | 70% faster |

*Gemini Live API has native audio output, no separate TTS latency

---

## Risks and Considerations

1. **Gemini Live API is All-in-One**
   - Can't easily separate ASR/LLM/TTS
   - If using Gemini Live API, must use for everything
   - Alternative: Use Gemini LLM only (via REST API), keep DashScope ASR/TTS

2. **Message Format Differences**
   - DashScope uses OpenAI-compatible format
   - Gemini uses native Google format
   - Need conversion layer

3. **Function Calling Differences**
   - Different parameter structures
   - Different response formats
   - Need abstraction layer

4. **Streaming Behavior**
   - May have different chunk sizes/timing
   - Need to test integration thoroughly

---

## Recommendation

### Immediate Steps

1. **Implement Gemini LLM only** (keep DashScope ASR/TTS)
   - Easiest integration
   - Biggest performance gain
   - Can compare LLM quality directly

2. **Add configuration system**
   - Allow switching LLM between DashScope and Gemini
   - Keep ASR/TTS on DashScope for now

### Future Steps

3. **Evaluate Gemini Live API**
   - Separate proof-of-concept
   - Requires different architecture
   - May require rewriting audio handling

---

## Files to Create/Modify

### New Files
- `services/base_service.py` - Abstract interfaces
- `services/gemini_service.py` - Gemini LLM implementation
- `services/service_factory.py` - Service instantiation
- `docs/eng/GEMINI_INTEGRATION_PLAN.md` - Implementation details

### Modified Files
- `config.py` - Add provider configuration
- `voice_agent.py` - Use service factory
- `services/llm_service.py` - Rename to `dashscope_llm_service.py` or refactor

---

## Test Plan

1. Test Gemini LLM with DashScope ASR/TTS
2. Compare performance metrics
3. Compare response quality
4. Test function calling works correctly
5. Verify streaming behavior

---

## Decision Needed

**Question for User:**

Should I proceed with implementing **Phase 1 & 2** (Gemini LLM only, keeping DashScope ASR/TTS)?

This would:
- Add Gemini LLM as a configurable option
- Keep existing DashScope services unchanged
- Allow A/B testing between qwen-turbo and gemini-2.5-flash
- Be the fastest path to performance improvement

Alternatively, I can explore the **Gemini Live API** (full audio-to-audio), but this requires significant architectural changes.
