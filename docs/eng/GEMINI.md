# Gemini Live API Integration Plan

**Date:** 2026-03-08
**Status:** Planning Phase
**Goal:** Integrate Gemini Live API as an optional all-in-one provider (ASR+LLM+TTS)

---

## Architecture Overview

### Current Architecture (DashScope)
```
Client Audio → ASR (DashScope) → Text → LLM (DashScope) → Text → TTS (DashScope) → Audio → Client
```

### New Architecture (Gemini Live API)
```
Client Audio → Gemini Live API (WebSocket) → Audio → Client
                              ↓
                         Function Calls
                              ↓
                     Order Updates (HTTP)
```

### Hybrid Support
```
PROVIDER=dashscope  → Use current architecture
PROVIDER=gemini     → Use Live API architecture
```

---

## Implementation Steps

### Phase 1: Configuration & Setup ✅

**Status:** ✅ Complete

**Tasks:**
- [x] Add Gemini API key loading from .env
- [x] Add PROVIDER configuration option
- [x] Create feature branch `feature/gemini-live-api`

**Changes:**
- `config.py`: Added PROVIDER, GEMINI_API_KEY, GEMINI_LIVE_MODEL, validation function
- Branch: `feature/gemini-live-api` created

**Files:**
- `config.py` - Add Gemini configuration
- `.env` - Ensure GEMINI_API_KEY is loaded

---

### Phase 2: Gemini Live API Service ✅

**Status:** ✅ Complete

**Tasks:**
- [x] Create `services/gemini_live_service.py`
- [x] Implement WebSocket connection management
- [x] Handle bidirectional audio streaming
- [x] Parse function calls from Gemini responses
- [x] Emit audio chunks to client

**Key Implementation Details:**
- Uses `websockets` library for WebSocket connection
- WebSocket endpoint: `wss://generativelanguage.googleapis.com/v1alpha/models/gemini-2.0-flash-live-001:connect`
- Handles audio input (PCM 16-bit, 16kHz)
- Handles audio output (PCM 16-bit, 24kHz)
- Function calling support with order updates

**Files:**
- `services/gemini_live_service.py` - Main service (new)
- `services/__init__.py` - Export new service

---

### Phase 3: Provider Factory Pattern ✅

**Status:** ✅ Complete

**Tasks:**
- [x] Create `services/provider_factory.py`
- [x] Abstract provider selection logic
- [x] Return appropriate service based on config

**Functions:**
- `create_llm_service()` - Creates DashScope LLM service or returns None for Gemini
- `create_gemini_live_service()` - Creates Gemini Live service when configured
- `create_order_service()` - Creates order service (provider-agnostic)
- `get_provider_info()` - Returns current provider configuration

**Files:**
- `services/provider_factory.py` (new)

---

### Phase 4: Voice Agent Integration ✅

**Status:** ✅ Complete

**Tasks:**
- [x] Modify `voice_agent.py` to use provider factory
- [x] Handle different session initialization for Gemini
- [x] Route audio data appropriately based on provider
- [x] Handle function calls from both providers uniformly

**Key Changes:**
- Added `asyncio` import for async WebSocket handling
- Services initialized via provider factory
- `start_recognition` - Connects to Gemini Live API or starts DashScope ASR
- `audio_data` - Routes audio to Gemini Live or DashScope ASR
- `stop_recognition` - Disconnects Gemini or stops DashScope ASR
- `chat` - Ignored for Gemini (handles internally), used for DashScope
- `synthesize` - Ignored for Gemini (handles internally), used for DashScope
- Startup shows provider info

**Files:**
- `voice_agent.py` - Provider-aware routing (modified)

---

### Phase 5: Client-Side Updates ✅

**Status:** ✅ Complete (No changes needed)

**Analysis:**
- Client-side `app.js` already handles audio chunks generically
- PCM 16-bit format is the same for both providers
- No provider-specific changes needed on client

**Files:**
- `static/app.js` - No changes required

---

### Phase 6: Testing & Validation ⬜

**Status:** ⬜ Pending User Testing

**Tasks:**
- [ ] Test Gemini Live API connection
- [ ] Verify audio streaming quality
- [ ] Test function calling with orders
- [ ] Compare performance vs DashScope
- [ ] Test provider switching

**Prerequisites:**
- Ensure `GEMINI_API_KEY` is set in `.env`
- Install `websockets` library: `pip install websockets`

**Test Commands:**

```bash
# Test with DashScope (default)
python3 voice_agent.py

# Test with Gemini Live API
PROVIDER=gemini python3 voice_agent.py
```

**Expected Output (Gemini):**
```
============================================================
CamareraI - Streaming Voice Agent POC
============================================================
Provider: gemini
Model: gemini-2.0-flash-live-001
Server starting on http://0.0.0.0:5002
============================================================
```

**Files:**
- `tests/test_gemini_live.py` (to be created if needed)

---

## Technical Details

### Gemini Live API Key Points

1. **WebSocket Endpoint:**
   ```
   wss://generativelanguage.googleapis.com/v1alpha/models/{model}:connect?key={API_KEY}
   ```
   Model: `gemini-2.0-flash-live-001` or similar

2. **Message Format:**
   - Input: Audio chunks (base64 encoded PCM)
   - Output: Audio chunks + function call events

3. **Function Calling:**
   - Define tools in setup message
   - Gemini returns function call events
   - App executes function, returns result
   - Gemini continues with audio response

4. **Audio Format:**
   - Input: PCM 16-bit, 16kHz or 24kHz
   - Output: PCM 16-bit, 24kHz (check docs)

### Code Structure

```python
class GeminiLiveService:
    def __init__(self, api_key, perf_monitor):
        self.client = genai.Client(api_key=api_key)
        self.session = None
        self.audio_queue = asyncio.Queue()

    async def connect(self, tools, session_id, emit_func):
        # Establish WebSocket connection
        # Start audio streaming
        pass

    async def send_audio(self, audio_chunk):
        # Send audio to Gemini
        pass

    async def receive_loop(self):
        # Handle incoming messages (audio + function calls)
        pass

    def handle_function_call(self, function_call):
        # Execute order update
        # Return result to Gemini
        pass
```

---

## Configuration

### Environment Variables

```bash
# Provider selection
PROVIDER=gemini  # 'dashscope' or 'gemini'

# API Keys (already in .env)
DASHSCOPE_API_KEY=sk-xxx
GEMINI_API_KEY=AIzaSy...

# Optional: Model configuration
GEMINI_LIVE_MODEL=gemini-2.0-flash-live-001
```

### Config.py Additions

```python
# Provider Configuration
PROVIDER = os.getenv('PROVIDER', 'dashscope')  # 'dashscope' or 'gemini'

# Gemini Configuration
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
GEMINI_LIVE_MODEL = os.getenv('GEMINI_LIVE_MODEL', 'gemini-2.0-flash-live-001')

# Validate provider selection
def validate_provider_config():
    if PROVIDER == 'gemini' and not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY required when PROVIDER=gemini")
    if PROVIDER == 'dashscope' and not DASHSCOPE_API_KEY:
        raise ValueError("DASHSCOPE_API_KEY required when PROVIDER=dashscope")
```

---

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Gemini Live API in beta | API changes | Pin to specific model version, monitor updates |
| Audio format mismatch | Audio quality | Test format conversion if needed |
| Function calling differences | Order updates fail | Abstract function calling interface |
| WebSocket reliability | Connection drops | Implement reconnection logic |
| Performance not as expected | Wasted effort | Benchmark early in Phase 2 |

---

## Success Criteria

- [ ] Gemini Live API connects successfully
- [ ] Audio streams bidirectionally with <1s latency
- [ ] Function calling works for order updates
- [ ] Can switch between DashScope and Gemini via config
- [ ] Performance meets or exceeds DashScope

---

## Progress Log

### 2026-03-08
- **Status:** Implementation complete, ready for testing
- **Completed:**
  - Phase 1: Configuration & Setup ✅
  - Phase 2: Gemini Live API Service ✅
  - Phase 3: Provider Factory Pattern ✅
  - Phase 4: Voice Agent Integration ✅
  - Phase 5: Client-Side Updates ✅
  - **Cleanup:** Moved `dashscope_client.py` → `services/dashscope_service.py` ✅
    - Renamed `DashScopeClient` → `DashScopeService`
    - Removed unused methods (transcribe, synthesize_realtime, clone_voice)
    - Removed debug logging and test code
    - Updated all imports
- **Next:** Phase 6 - Testing & Validation
- **Dependencies:** `pip install google-genai websockets`
- **Fixed:** Gemini Live API connection using native SDK
  - Correct model: `gemini-2.5-flash-native-audio-latest`
  - Uses `async with` context managers
  - Queue-based audio streaming

---

## Notes

- Keep DashScope implementation intact for fallback
- Use feature branch: `feature/gemini-live-api`
- Document any API-specific quirks discovered during implementation
- Consider asyncio for WebSocket handling (may need to refactor voice_agent.py)
