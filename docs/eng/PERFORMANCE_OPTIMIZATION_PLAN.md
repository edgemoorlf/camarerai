# Performance Optimization Plan

**Branch**: `feature/performance-optimization`
**Created**: 2026-02-10
**Status**: Planning Phase

## Executive Summary

User reports poor voice recognition performance affecting user experience. This plan addresses response time optimization across all components (ASR, LLM, TTS) and evaluates Google Gemini API as an alternative to DashScope.

## Problem Statement

### Current Issues
- Voice recognition performance is "really bad" (user feedback)
- Response time delays negatively impact user experience
- Unclear which component(s) are causing bottlenecks

### Success Criteria
- Total response time < 3 seconds (from speech end to audio playback start)
- Time to first audio < 1 second (perceived responsiveness)
- Smooth, natural conversation flow
- Configurable API provider (DashScope vs Gemini)

## Current Architecture Analysis

### DashScope Implementation

**ASR (Speech Recognition)**
- Model: `paraformer-realtime-v2`
- Mode: ✅ **Streaming** (WebSocket-based)
- Format: PCM, 16kHz
- Features: Semantic punctuation, sentence detection
- Status: **Working well**

**LLM (Text Generation)**
- Model: `qwen-plus`
- Mode: ✅ **Streaming** (Server-Sent Events)
- Implementation: `Generation.call(stream=True)`
- Status: **Working well**

**TTS (Text-to-Speech)**
- Model: `qwen3-tts-flash`
- Mode: ❌ **NON-streaming** (blocking)
- Implementation: `synthesize(text, voice, language_type='Auto')` without `stream=True`
- Status: **BOTTLENECK IDENTIFIED** ⚠️

### Performance Bottleneck

**Root Cause**: TTS is not streaming!

```python
# Current implementation (voice_agent.py:931)
audio_url = dashscope_client.synthesize(text, voice=voice, language_type='Auto')
# ❌ No stream=True parameter
# ❌ Waits for entire audio generation before returning
# ❌ Client must download entire audio file before playback
```

**Impact**:
- User hears nothing while TTS generates entire response
- Long responses = long silence = poor UX
- No perceived progress during generation

## Performance Metrics

### Target Metrics

| Metric | Target | Acceptable | Poor |
|--------|--------|------------|------|
| ASR latency (speech → text) | < 500ms | < 1s | > 1s |
| LLM latency (text → response start) | < 800ms | < 1.5s | > 2s |
| TTS latency (text → audio start) | < 500ms | < 1s | > 1.5s |
| **Total response time** | **< 2s** | **< 3s** | **> 3s** |
| Time to first audio chunk | < 1s | < 1.5s | > 2s |

### Measurement Points

```
User Speech End
    ↓ [ASR Processing]
Transcription Complete
    ↓ [LLM Processing]
Response Text Start
    ↓ [TTS Processing]
Audio Playback Start
    ↓ [Audio Streaming]
Audio Playback Complete
```

## Solution Approaches

### Approach 1: Enable DashScope TTS Streaming (Quick Win)

**Effort**: Low (1-2 hours)
**Impact**: High (immediate improvement)
**Risk**: Low

**Changes Required**:
1. Enable streaming in TTS call: `synthesize(text, voice, stream=True)`
2. Handle streaming audio chunks in client
3. Play audio progressively as chunks arrive

**Pros**:
- Minimal code changes
- Keeps existing DashScope infrastructure
- Immediate performance improvement
- Low risk

**Cons**:
- Still dependent on DashScope API
- May not achieve best possible latency
- Separate API calls for ASR, LLM, TTS

### Approach 2: Implement Gemini Live API (Long-term Solution)

**Effort**: High (1-2 days)
**Impact**: Very High (unified streaming)
**Risk**: Medium

**Gemini Live API Features**:
- **Unified streaming**: ASR + LLM + TTS in one WebSocket connection
- **Native audio**: Direct audio-to-audio processing
- **Low latency**: ~590ms time to first token (Gemini 2.0 Flash Lite)
- **Bidirectional**: Simultaneous send/receive
- **30 HD voices** in 24 languages
- **Function calling**: Tool use support
- **Free tier available**: User has API key

**Architecture**:
```
Client (Browser)
    ↕ WebSocket (Audio PCM)
Flask-SocketIO Server
    ↕ WebSocket (Audio PCM)
Gemini Live API
    ↓ Streaming Response (Audio PCM)
Flask-SocketIO Server
    ↓ Audio Chunks
Client (Browser)
    ↓ Progressive Playback
```

**Pros**:
- Single unified API (simpler architecture)
- Native audio processing (no intermediate steps)
- Potentially lower latency
- Free tier available
- Modern, well-documented API

**Cons**:
- Requires significant refactoring
- New API to learn and integrate
- Need to handle migration of existing features
- Dependency on Google infrastructure

### Approach 3: Hybrid (Recommended)

**Phase 1**: Enable DashScope TTS streaming (quick win)
**Phase 2**: Implement Gemini Live API as alternative provider
**Phase 3**: Make provider configurable via environment variable

**Configuration**:
```python
# .env
API_PROVIDER=dashscope  # or 'gemini'
DASHSCOPE_API_KEY=xxx
GEMINI_API_KEY=xxx
```

## Implementation Plan

### Phase 1: Enable DashScope TTS Streaming (Quick Win)

**Goal**: Immediate performance improvement
**Effort**: 2-4 hours
**Priority**: HIGH

**Tasks**:
1. ✅ Create feature branch `feature/performance-optimization`
2. Modify `dashscope_client.py`:
   - Update `synthesize()` to handle streaming response
   - Return audio chunks generator when `stream=True`
3. Modify `voice_agent.py`:
   - Update `handle_synthesize()` to stream audio chunks
   - Emit audio chunks progressively to client
4. Modify `static/app.js`:
   - Handle streaming audio chunks
   - Implement progressive audio playback
   - Use Web Audio API or MediaSource Extensions
5. Test and measure performance improvement

**Expected Improvement**: 50-70% reduction in perceived latency

### Phase 2: Measure Current Performance

**Goal**: Establish baseline metrics
**Effort**: 1-2 hours
**Priority**: HIGH

**Tasks**:
1. Add performance logging to `voice_agent.py`:
   - Log timestamp at each stage (ASR → LLM → TTS)
   - Calculate and log latencies
2. Create test scenarios:
   - Short response (1 sentence)
   - Medium response (2-3 sentences)
   - Long response (5+ sentences)
3. Run tests and document baseline metrics
4. Identify specific bottlenecks

### Phase 3: Research Gemini Live API

**Goal**: Understand Gemini capabilities and requirements
**Effort**: 2-3 hours
**Priority**: MEDIUM

**Tasks**:
1. Test Gemini API key validity
2. Review Gemini Live API documentation
3. Create proof-of-concept:
   - Simple audio input → audio output
   - Test latency and quality
   - Verify function calling support
4. Document findings and recommendations

### Phase 4: Implement Gemini Client

**Goal**: Create alternative API provider
**Effort**: 1-2 days
**Priority**: MEDIUM

**Tasks**:
1. Create `gemini_client.py`:
   - Implement WebSocket connection to Gemini Live API
   - Handle bidirectional audio streaming
   - Implement function calling for order management
   - Error handling and reconnection logic
2. Create unified interface:
   - Abstract `VoiceAPIProvider` base class
   - `DashScopeProvider` implementation
   - `GeminiProvider` implementation
3. Update `voice_agent.py`:
   - Load provider based on configuration
   - Use provider interface for all API calls

### Phase 5: Configuration and Testing

**Goal**: Make provider configurable and validate performance
**Effort**: 4-6 hours
**Priority**: MEDIUM

**Tasks**:
1. Add configuration:
   - Environment variable `API_PROVIDER`
   - Provider-specific settings
   - Fallback logic
2. Comprehensive testing:
   - Test both providers
   - Compare performance metrics
   - Test edge cases and error handling
3. Documentation:
   - Update README.md
   - Add configuration guide
   - Document performance comparison

## Technical Details

### DashScope TTS Streaming Implementation

**Current (Non-streaming)**:
```python
# dashscope_client.py
def synthesize(self, text, voice='Cherry', language_type='Auto', stream=False):
    response = MultiModalConversation.call(
        model='qwen3-tts-flash',
        text=text,
        voice=voice,
        language_type=language_type,
        api_key=self.api_key,
        stream=stream  # Currently always False
    )

    if stream:
        return response  # Generator
    else:
        audio_url = response.output.get('audio', {}).get('url')
        return audio_url  # Single URL
```

**Proposed (Streaming)**:
```python
# voice_agent.py
@socketio.on('synthesize')
def handle_synthesize(data):
    text = data.get('text')
    voice = data.get('voice', 'Cherry')

    # Enable streaming
    response_generator = dashscope_client.synthesize(
        text,
        voice=voice,
        stream=True  # ✅ Enable streaming
    )

    # Stream audio chunks to client
    for chunk in response_generator:
        if chunk.status_code == HTTPStatus.OK:
            audio_data = chunk.output.get('audio', {})
            audio_chunk = audio_data.get('data')  # Base64 encoded audio

            if audio_chunk:
                emit('audio_chunk', {
                    'session_id': session_id,
                    'audio_data': audio_chunk,
                    'is_final': False
                })

    # Send final marker
    emit('audio_chunk', {
        'session_id': session_id,
        'is_final': True
    })
```

**Client-side (Progressive Playback)**:
```javascript
// static/app.js
class AudioStreamPlayer {
    constructor() {
        this.audioContext = new AudioContext();
        this.audioQueue = [];
        this.isPlaying = false;
    }

    async addChunk(base64Audio) {
        // Decode base64 to ArrayBuffer
        const audioData = this.base64ToArrayBuffer(base64Audio);

        // Decode audio data
        const audioBuffer = await this.audioContext.decodeAudioData(audioData);

        // Add to queue
        this.audioQueue.push(audioBuffer);

        // Start playing if not already
        if (!this.isPlaying) {
            this.playNext();
        }
    }

    playNext() {
        if (this.audioQueue.length === 0) {
            this.isPlaying = false;
            return;
        }

        this.isPlaying = true;
        const buffer = this.audioQueue.shift();

        const source = this.audioContext.createBufferSource();
        source.buffer = buffer;
        source.connect(this.audioContext.destination);
        source.onended = () => this.playNext();
        source.start();
    }
}
```

### Gemini Live API Implementation

**Architecture**:
```python
# gemini_client.py
import asyncio
import websockets
import json
import base64

class GeminiLiveClient:
    def __init__(self, api_key):
        self.api_key = api_key
        self.ws_url = f"wss://generativelanguage.googleapis.com/ws/google.ai.generativelanguage.v1alpha.GenerativeService.BidiGenerateContent?key={api_key}"
        self.websocket = None

    async def connect(self):
        """Establish WebSocket connection"""
        self.websocket = await websockets.connect(self.ws_url)

        # Send setup message
        setup = {
            "setup": {
                "model": "models/gemini-2.0-flash-exp",
                "generation_config": {
                    "response_modalities": ["AUDIO"],
                    "speech_config": {
                        "voice_config": {
                            "prebuilt_voice_config": {
                                "voice_name": "Aoede"  # Female voice
                            }
                        }
                    }
                }
            }
        }
        await self.websocket.send(json.dumps(setup))

    async def send_audio(self, audio_data):
        """Send audio chunk to Gemini"""
        message = {
            "realtime_input": {
                "media_chunks": [{
                    "mime_type": "audio/pcm",
                    "data": base64.b64encode(audio_data).decode()
                }]
            }
        }
        await self.websocket.send(json.dumps(message))

    async def receive_audio(self):
        """Receive audio response from Gemini"""
        async for message in self.websocket:
            data = json.loads(message)

            if "serverContent" in data:
                parts = data["serverContent"].get("modelTurn", {}).get("parts", [])
                for part in parts:
                    if "inlineData" in part:
                        audio_data = part["inlineData"]["data"]
                        yield base64.b64decode(audio_data)
```

**Integration with Flask-SocketIO**:
```python
# voice_agent.py
from gemini_client import GeminiLiveClient

# Initialize based on configuration
if os.getenv('API_PROVIDER') == 'gemini':
    voice_client = GeminiLiveClient(os.getenv('GEMINI_API_KEY'))
else:
    voice_client = DashScopeClient(os.getenv('DASHSCOPE_API_KEY'))

@socketio.on('audio_data')
async def handle_audio_data(data):
    """Handle incoming audio from client"""
    audio_bytes = base64.b64decode(data.get('audio'))

    # Send to Gemini
    await voice_client.send_audio(audio_bytes)

    # Receive and forward response
    async for audio_chunk in voice_client.receive_audio():
        emit('audio_chunk', {
            'audio_data': base64.b64encode(audio_chunk).decode()
        })
```

## Risk Assessment

### Technical Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| DashScope streaming TTS not working as expected | Low | Medium | Test thoroughly, fallback to non-streaming |
| Gemini API rate limits | Medium | High | Implement rate limiting, caching, fallback to DashScope |
| WebSocket connection instability | Medium | High | Implement reconnection logic, heartbeat monitoring |
| Audio format compatibility issues | Medium | Medium | Test multiple formats, implement conversion if needed |
| Performance not meeting targets | Low | High | Measure continuously, optimize incrementally |

### Business Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Gemini API costs exceed budget | Low | Medium | Monitor usage, implement free tier limits |
| DashScope API deprecation | Low | High | Maintain both providers, easy switching |
| User experience regression | Low | High | Thorough testing, gradual rollout |

## Testing Strategy

### Performance Testing

**Test Scenarios**:
1. **Short response** (1 sentence, ~10 words)
   - Measure: ASR → LLM → TTS → Audio playback
   - Target: < 2s total
2. **Medium response** (2-3 sentences, ~30 words)
   - Measure: Time to first audio chunk
   - Target: < 1s
3. **Long response** (5+ sentences, ~80 words)
   - Measure: Progressive playback smoothness
   - Target: No gaps or stuttering
4. **Rapid-fire** (multiple quick exchanges)
   - Measure: System stability under load
   - Target: No degradation

**Metrics to Track**:
- ASR latency (speech end → transcription complete)
- LLM latency (transcription → response start)
- TTS latency (response start → audio start)
- Total latency (speech end → audio start)
- Audio streaming smoothness (gaps, stuttering)
- Error rate (failed requests, timeouts)

### Functional Testing

**Test Cases**:
1. ✅ ASR accuracy (English, Mandarin, Cantonese)
2. ✅ LLM response quality (natural, contextual)
3. ✅ TTS voice quality (clear, natural)
4. ✅ Order management (add, modify, remove items)
5. ✅ Session management (passive mode, resume)
6. ✅ Error handling (network issues, API errors)
7. ✅ Provider switching (DashScope ↔ Gemini)

## Success Metrics

### Phase 1 Success (DashScope Streaming)
- ✅ TTS streaming implemented and working
- ✅ Time to first audio < 1s
- ✅ Total response time < 3s
- ✅ No audio playback issues

### Phase 2 Success (Gemini Integration)
- ✅ Gemini Live API working end-to-end
- ✅ Performance equal or better than DashScope
- ✅ All features working (order management, session management)
- ✅ Configurable provider switching

### Overall Success
- ✅ User reports improved performance
- ✅ Natural conversation flow
- ✅ < 3s total response time consistently
- ✅ Smooth audio playback
- ✅ Production-ready code

## Timeline

### Week 1 (Current)
- ✅ Day 1: Planning and research (this document)
- 🔄 Day 2-3: Phase 1 - Enable DashScope TTS streaming
- 🔄 Day 3-4: Phase 2 - Measure and validate performance

### Week 2
- 📋 Day 1-2: Phase 3 - Research and test Gemini API
- 📋 Day 3-5: Phase 4 - Implement Gemini client
- 📋 Day 5-7: Phase 5 - Configuration and testing

### Week 3
- 📋 Performance optimization and tuning
- 📋 Documentation and deployment
- 📋 User acceptance testing

## Resources

### Documentation
- [DashScope TTS Documentation](https://www.alibabacloud.com/help/en/model-studio/qwen-tts)
- [Gemini Live API Documentation](https://ai.google.dev/gemini-api/docs/live)
- [Gemini Live API Guide](https://ai.google.dev/gemini-api/docs/live-guide)
- [Gemini TTS Documentation](https://ai.google.dev/gemini-api/docs/speech-generation)
- [LLM Benchmarks - Gemini Performance](https://llm-benchmarks.com/models/vertex/gemini20flashlite)

### API Keys
- DashScope: Already configured in `.env`
- Gemini: `AIzaSyA_eFyU4EueIpm5xYAivKi5trF94dVoGzw` (provided by user)

### Performance References
- [Real-Time Streaming LLM Inference Guide 2026](https://iterathon.tech/blog/real-time-streaming-llm-inference-guide-2026)
- [Gemini 2.5 Flash Native Audio Guide](https://supermaker.ai/blog/gemini-2-5-flash-native-audio-real-time/)
- [Gemini 2.5 Flash Live API Complete Guide](https://fastgptplus.com/en/posts/gemini-2-5-flash-live)

## Next Steps

1. **Get approval** for this plan from user
2. **Start Phase 1**: Enable DashScope TTS streaming
3. **Measure baseline**: Document current performance metrics
4. **Test Gemini API**: Validate API key and basic functionality
5. **Implement incrementally**: Phase by phase with testing

## Questions for User

1. ✅ Approve this plan to proceed with implementation?
2. Should we prioritize quick win (DashScope streaming) or go straight to Gemini?
3. Any specific performance targets or requirements?
4. Any concerns about using Gemini API (costs, privacy, etc.)?

---

**Status**: Awaiting approval to begin implementation
**Next Action**: User review and approval
