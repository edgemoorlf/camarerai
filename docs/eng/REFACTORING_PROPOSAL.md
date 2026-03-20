# Provider Architecture Refactoring Proposal

**Date:** 2026-03-08
**Status:** Proposal
**Goal:** Clean separation between DashScope and Gemini implementations

---

## Current Problems

### 1. Scattered DashScope Code
```python
# voice_agent.py - DashScope imports scattered at top
from dashscope.audio.asr import Recognition
import dashscope
dashscope.api_key = config.DASHSCOPE_API_KEY  # Global state

# DashScope-specific callback class embedded in voice_agent.py
class StreamingRecognitionCallback:
    ...

# Provider checks scattered throughout handlers
if config.PROVIDER == 'gemini':
    ...
else:
    ...
```

### 2. Inconsistent Abstractions
- `GeminiLiveService` - Clean abstraction
- `DashScopeClient` - Low-level client, not aligned with Gemini service
- `LLMService` - Uses DashScope TTS directly

### 3. Voice Agent Knows Too Much
- Handles both WebSocket (Gemini) and callback-based (DashScope) ASR
- Manages different audio formats
- Contains provider-specific connection logic

---

## Proposed Architecture

### Pattern: Strategy + Factory

```
┌─────────────────────────────────────────────────────────────┐
│                    voice_agent.py                           │
│  - No provider-specific imports                             │
│  - Uses VoiceService interface only                         │
│  - Single code path for audio/chat                          │
└─────────────────────────────────────────────────────────────┘
                              │
              ┌───────────────┴───────────────┐
              │                               │
┌─────────────▼─────────────┐    ┌─────────────▼─────────────┐
│   DashScopeVoiceService   │    │    GeminiVoiceService     │
│   (implements VoiceService)│   │   (implements VoiceService)│
├───────────────────────────┤    ├───────────────────────────┤
│ - ASR: Recognition        │    │ - ASR: Live API WebSocket │
│ - LLM: OpenAI client      │    │ - LLM: Live API (built-in)│
│ - TTS: MultiModalConv     │    │ - TTS: Live API (built-in)│
│ - Format: PCM 16kHz       │    │ - Format: PCM 16kHz       │
└───────────────────────────┘    └───────────────────────────┘
```

---

## Implementation Plan

### Phase 1: Define VoiceService Interface

**File:** `services/voice_service.py`

```python
from abc import ABC, abstractmethod
from typing import Callable, Optional

class VoiceService(ABC):
    """
    Abstract interface for voice service providers.
    Both DashScope and Gemini implement this interface.
    """

    @abstractmethod
    async def connect(self, session_id: str, emit_func: Callable,
                      order_service=None, tools=None) -> None:
        """Establish connection to voice service"""
        pass

    @abstractmethod
    async def disconnect(self) -> None:
        """Disconnect from voice service"""
        pass

    @abstractmethod
    async def send_audio(self, audio_data: bytes) -> None:
        """Send audio chunk to service"""
        pass

    @abstractmethod
    def is_connected(self) -> bool:
        """Check if service is connected"""
        pass

    @abstractmethod
    def get_provider_name(self) -> str:
        """Return provider name"""
        pass
```

### Phase 2: Refactor DashScope into Service

**File:** `services/dashscope_voice_service.py`

```python
from dashscope.audio.asr import Recognition
import dashscope
from .voice_service import VoiceService

class DashScopeVoiceService(VoiceService):
    """
    DashScope implementation of VoiceService.
    Wraps ASR + LLM + TTS into unified interface.
    """

    def __init__(self, api_key: str, perf_monitor=None):
        self.api_key = api_key
        self.perf_monitor = perf_monitor
        dashscope.api_key = api_key

        # Internal components
        self._recognition = None
        self._callback = None
        self._session_id = None
        self._emit_func = None
        self._connected = False

    async def connect(self, session_id: str, emit_func: Callable,
                      order_service=None, tools=None):
        """Start ASR recognition"""
        from .dashscope_callback import StreamingRecognitionCallback

        self._session_id = session_id
        self._emit_func = emit_func
        self._callback = StreamingRecognitionCallback(session_id, emit_func)

        self._recognition = Recognition(
            model='paraformer-realtime-v2',
            format='pcm',
            sample_rate=16000,
            callback=self._callback,
            semantic_punctuation_enabled=True,
            max_sentence_silence=5000,
            disfluency_removal_enabled=False
        )

        # Don't start yet - wait for first audio
        self._connected = True

    async def disconnect(self):
        """Stop ASR recognition"""
        if self._recognition:
            self._recognition.stop()
        self._connected = False

    async def send_audio(self, audio_data: bytes):
        """Send audio to ASR"""
        if not self._recognition:
            return

        # Start on first audio if not started
        if hasattr(self._recognition, '_started') and not self._recognition._started:
            self._recognition.start()
            self._recognition._started = True

        self._recognition.send_audio_frame(audio_data)

    def is_connected(self) -> bool:
        return self._connected

    def get_provider_name(self) -> str:
        return "dashscope"

    # DashScope-specific: Handle transcription completion
    def on_transcription_complete(self, text: str):
        """Called when ASR completes - triggers LLM"""
        # This will trigger the LLM flow
        pass
```

### Phase 3: Update Gemini to Implement Interface

**File:** `services/gemini_voice_service.py` (rename from gemini_live_service.py)

```python
from .voice_service import VoiceService

class GeminiVoiceService(VoiceService):
    """Gemini Live API implementation of VoiceService"""

    def get_provider_name(self) -> str:
        return "gemini"

    # ... rest of implementation aligned with interface
```

### Phase 4: Simplified Voice Agent

**File:** `voice_agent.py` (refactored)

```python
"""
Streaming Voice Recognition Server
Provider-agnostic voice ordering system
"""

from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit
import config
from services.provider_factory import create_voice_service

app = Flask(__name__)
socketio = SocketIO(app, **config.SOCKETIO_CONFIG)

# Single voice service instance (provider selected by config)
voice_service = create_voice_service(config.PROVIDER)
active_sessions = {}

@socketio.on('start_recognition')
def handle_start_recognition(data):
    """Start voice recognition - provider agnostic"""
    session_id = data.get('session_id')

    # Single code path - no provider checks
    voice_service.connect(
        session_id=session_id,
        emit_func=emit,
        order_service=order_service,
        tools=[config.ORDER_UPDATE_TOOL]
    )

    emit('recognition_started', {'session_id': session_id})

@socketio.on('audio_data')
def handle_audio_data(data):
    """Handle audio - provider agnostic"""
    audio_bytes = base64.b64decode(data['audio'])

    # Single code path
    voice_service.send_audio(audio_bytes)
```

### Phase 5: Chat/LLM Flow Alignment

**Challenge:** DashScope needs separate chat handler, Gemini handles it internally.

**Solution:** Both services implement `handle_conversation_turn()`

```python
class VoiceService(ABC):
    @abstractmethod
    async def handle_conversation_turn(self, transcript: str,
                                       session, emit_func) -> None:
        """
        Process a conversation turn.
        - DashScope: Calls LLM + TTS, emits audio chunks
        - Gemini: Already handled internally, this is no-op or for logging
        """
        pass
```

---

## Directory Structure

```
services/
├── __init__.py
├── voice_service.py           # Abstract interface (NEW)
├── provider_factory.py        # Create service by provider
├── dashscope/
│   ├── __init__.py
│   ├── voice_service.py       # DashScopeVoiceService (REFACTOR)
│   ├── asr_callback.py        # StreamingRecognitionCallback (MOVE)
│   ├── llm_service.py         # LLM + TTS streaming (REFACTOR from llm_service.py)
│   └── client.py              # Low-level client (OPTIONAL)
├── gemini/
│   ├── __init__.py
│   └── voice_service.py       # GeminiVoiceService (RENAME)
└── order_service.py           # Unchanged
```

---

## Benefits

1. **Single Responsibility**
   - Each provider encapsulates its own complexity
   - Voice agent only knows about VoiceService interface

2. **Easy Testing**
   - Mock VoiceService for testing
   - Test providers independently

3. **Adding New Providers**
   - Just implement VoiceService interface
   - No changes to voice_agent.py

4. **Clean Configuration**
   - One env var: `PROVIDER=dashscope|gemini`
   - No conditional logic scattered through code

---

## Migration Steps

### Step 1: Create VoiceService interface
- Create `services/voice_service.py`

### Step 2: Move DashScope callback
- Move `StreamingRecognitionCallback` to `services/dashscope/asr_callback.py`

### Step 3: Create DashScopeVoiceService
- Encapsulate all DashScope logic
- Handle ASR → LLM → TTS flow internally

### Step 4: Refactor voice_agent.py
- Remove all DashScope-specific imports
- Use only VoiceService interface
- Remove provider conditionals

### Step 5: Test both providers
- Verify DashScope still works
- Verify Gemini still works

---

## Estimated Effort

- Step 1: 30 min
- Step 2: 30 min
- Step 3: 2-3 hours (most complex)
- Step 4: 1-2 hours
- Step 5: 1 hour

**Total:** ~5-7 hours

---

## Decision Point

Should I proceed with this refactoring?

**Pros:**
- Clean, maintainable architecture
- Easy to add new providers (OpenAI, Azure, etc.)
- Voice agent becomes simple coordinator

**Cons:**
- Significant refactoring effort
- Risk of introducing bugs
- Current "messy" version works for now

**Alternative:**
- Keep current architecture for demo
- Refactor after demo if adding more providers
