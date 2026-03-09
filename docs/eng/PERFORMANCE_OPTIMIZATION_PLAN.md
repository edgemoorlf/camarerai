# Performance Optimization Plan

**Branch**: `feature/performance-optimization`
**Created**: 2026-02-10
**Updated**: 2026-03-07
**Status**: Implementation Phase - Option 1 (Connection Pre-warming)

---

## Executive Summary

This plan addresses response time optimization for the voice ordering system. The focus is on reducing first audio latency from ~400-600ms to <300ms for a snappy demo experience.

**Current Status:**
- ✅ End-to-end streaming (ASR → LLM → TTS) already implemented
- ✅ Performance monitoring in place
- ✅ Code refactored with function calling
- 🔄 **NOW**: Option 1 - Connection Pre-warming

---

## Current Metrics (March 2026)

| Metric | Current | Target | Status |
|--------|---------|--------|--------|
| LLM first token | ~200-300ms | <200ms | 🟡 Needs improvement |
| First audio | ~400-600ms | <300ms | 🔴 Blocker |
| Total response | ~1600ms | <2000ms | 🟡 OK |

**Primary Issue:** Connection establishment overhead for each request.

---

## Implementation Phases

### Phase 1: Option 1 - Connection Pre-warming (CURRENT)

**Goal:** Eliminate connection setup latency by pre-establishing and reusing connections.

**Effort:** 2-3 hours
**Impact:** High (100-200ms reduction)
**Risk:** Low

**What We'll Do:**
1. Create persistent HTTP session for DashScope API calls
2. Reuse OpenAI client connection across requests
3. Pre-warm connections when session starts (not on first use)
4. Keep connections alive with keep-alive headers

**Expected Outcome:**
- First token: ~200-300ms → ~100-200ms
- First audio: ~400-600ms → ~300-400ms

---

### Phase 2: Option 3 - Cached Greetings

**Goal:** Instant response for common opening phrases.

**Effort:** 3-4 hours
**Impact:** Very High for initial interaction
**Risk:** Low

**What We'll Do:**
1. Pre-generate audio for common greetings:
   - "Hello! What can I get for you today?"
   - "Welcome! Here's what I recommend..."
2. Cache in memory on server start
3. Serve from cache for matching opening phrases (<50ms)

**Expected Outcome:**
- First interaction: ~400-600ms → ~50ms

---

### Phase 3: Option 4 - Faster LLM Model (if needed)

**Goal:** Reduce LLM latency by using faster model for simple queries.

**Effort:** 1-2 hours
**Impact:** Medium
**Risk:** Low

**What We'll Do:**
1. Use `qwen-turbo` for faster first response
2. Switch to `qwen-plus` for complex queries if needed

---

## Option 1: Connection Pre-warming (Detailed Plan)

### Current Problem

Each API call creates a new HTTP connection:

```python
# Current (creates new connection each time)
openai_client = OpenAI(api_key=..., base_url=...)  # New client each request?
stream = openai_client.chat.completions.create(...)  # DNS + TCP + TLS each time
```

**Overhead per connection:**
- DNS lookup: 10-100ms
- TCP handshake: 20-50ms
- TLS handshake: 50-200ms
- **Total: 80-350ms** (kills first token time)

### Solution

**1. Persistent HTTP Session**

```python
# config.py or dashscope_client.py
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

def create_persistent_session():
    session = requests.Session()

    # Keep-alive settings
    retry = Retry(total=3, backoff_factor=0.5)
    adapter = HTTPAdapter(
        pool_connections=10,
        pool_maxsize=10,
        max_retries=retry
    )

    session.mount('https://', adapter)
    session.headers.update({
        'Connection': 'keep-alive',
        'Keep-Alive': 'timeout=60, max=1000'
    })

    return session

# Global session (created once)
http_session = create_persistent_session()
```

**2. Reuse OpenAI Client**

```python
# config.py - Single client instance
openai_client = OpenAI(
    api_key=config.DASHSCOPE_API_KEY,
    base_url=config.DASHSCOPE_BASE_URL,
    http_client=http_session  # Use persistent session
)
```

**3. Connection Pre-warming**

```python
# voice_agent.py - Pre-warm on session start

@socketio.on('create_session')
def handle_create_session(data):
    # ... create session ...

    # Pre-warm connections
    threading.Thread(target=prewarm_connections, daemon=True).start()

    emit('session_created', {...})

def prewarm_connections():
    """Send small request to establish connection"""
    try:
        # Warm up LLM connection
        _ = openai_client.chat.completions.create(
            model='qwen-plus',
            messages=[{'role': 'user', 'content': 'hi'}],
            max_tokens=1,
            stream=False
        )
        print("[Perf] Connections pre-warmed")
    except Exception as e:
        print(f"[Perf] Pre-warm warning: {e}")
```

### Implementation Steps

**Step 1: Add HTTP Session to config.py**
- Create persistent session with keep-alive
- Mount adapter with pool settings

**Step 2: Modify OpenAI Client Initialization**
- Pass http_client to OpenAI client
- Ensure single instance reused

**Step 3: Add Pre-warming to Session Creation**
- Send small request on session start
- Establish connection before user speaks

**Step 4: Test and Measure**
- Compare first token times
- Verify connection reuse

---

## Implementation Checklist

### Step 1: HTTP Session Setup ✅ COMPLETE
- [x] Add `requests` session with keep-alive to config.py
- [x] Configure connection pool (10 connections)
- [x] Add retry logic

### Step 2: OpenAI Client Update ✅ COMPLETE
- [x] Modify OpenAI client to use persistent session
- [x] Ensure single client instance

### Step 3: Pre-warming ✅ COMPLETE
- [x] Add prewarm_connections() function
- [x] Call on session creation
- [x] Make non-blocking (threading)

### Step 4: Testing 🔄 NEXT
- [ ] Measure baseline (before changes)
- [ ] Measure after changes
- [ ] Document improvement

---

## Success Metrics

### Option 1 Success Criteria
- [ ] First token latency reduced by 100-200ms
- [ ] No connection errors
- [ ] Stable performance across multiple requests

### Overall Success
- [ ] First audio < 300ms
- [ ] Smooth conversation flow
- [ ] Demo-ready performance

---

## Next Actions

1. ✅ **Step 1** - HTTP session added to config.py
2. ✅ **Step 2** - OpenAI client updated with persistent session
3. ✅ **Step 3** - Pre-warming implemented
4. 🔄 **Step 4** - Test and measure performance improvement

---

## Historical Notes

### Previous Work (Feb 2026)

**TTS Streaming - COMPLETED:**
- Enabled DashScope TTS streaming
- Implemented sentence-by-sentence streaming
- Added AudioStreamPlayer for progressive playback
- Reduced perceived latency significantly

**Code Refactoring - COMPLETED:**
- Extracted config.py (123 lines)
- Extracted services/order_service.py (127 lines)
- Extracted services/llm_service.py (217 lines)
- Reduced voice_agent.py by 20% (1232 → 980 lines)

### Why Connection Pre-warming Now?

After profiling, connection establishment is the remaining major bottleneck:
- DNS + TCP + TLS = 80-350ms overhead
- Occurs on first API call in each session
- Eliminating this gets us to <300ms target

---

**Status**: Option 1 implementation complete
**Next Action**: Test and measure performance (Step 4)

### How to Test

1. Start the server:
   ```bash
   python3 voice_agent.py
   ```

2. Open browser and check console for:
   ```
   [Perf] Pre-warming API connections...
   [Perf] ✓ Connections pre-warmed
   ```

3. Check performance metrics in UI (debug panel)
   - Look for "LLM first token" and "First audio" times
   - Compare with previous ~400-600ms baseline
   - Target: <300ms for first audio

4. Run a few test conversations and note the response times
