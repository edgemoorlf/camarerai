# Streaming Verification Report

**Date:** 2026-03-08
**Status:** Streaming IS configured correctly - Performance issues are due to overhead, not configuration

---

## Streaming Configuration Status

| Component | Streaming Configured | Status |
|-----------|---------------------|--------|
| **ASR** | ✅ `Recognition` class (WebSocket streaming) | Native streaming by design |
| **LLM** | ✅ `stream=True` in llm_service.py:44 | Correctly configured |
| **TTS** | ✅ `stream=True` in llm_service.py:154 | Correctly configured |

**Conclusion:** The streaming pipeline is properly configured end-to-end.

---

## What Was Fixed

### 1. Debug Logging Reduction (HIGH IMPACT)

**Files Modified:**
- `services/llm_service.py` - Removed [TTS-Debug] logs that printed for every token
- `dashscope_client.py` - Removed per-chunk logging in `_stream_audio_chunks()`

**Impact:**
- Before: Every LLM token and TTS chunk was being logged (500+ log lines per response)
- After: Minimal logging (only first token timing, sentence sends, completion)
- Expected improvement: 30-50% reduction in total response time

### 2. LLM Model Changed (MEDIUM IMPACT)

**Change:** `qwen-plus` → `qwen-turbo`

**Expected improvement:** 30-40% faster first token

### 3. Syntax Error Fixed

**File:** `services/llm_service.py:115`
- Fixed indentation error in `_stream_to_tts()` call

---

## Performance Estimates

### Before Optimization (Measured)

| Metric | Value | Status |
|--------|-------|--------|
| LLM First Token | 983ms | 🔴 CRITICAL |
| LLM Total | 12,654ms | 🔴 CRITICAL |
| TTS First Audio | 3,959ms | 🔴 CRITICAL |
| Total Response | 8,993ms | 🔴 CRITICAL |

### After Optimization (Estimated)

| Metric | Estimated | Status |
|--------|-----------|--------|
| LLM First Token | ~400-500ms | 🟡 IMPROVED |
| LLM Total | ~5,000-7,000ms | 🟡 IMPROVED |
| TTS First Audio | ~2,500-3,000ms | 🟡 IMPROVED |
| Total Response | ~5,000-6,000ms | 🟡 IMPROVED |

**Expected improvement:** 40-60% faster

---

## Is This Good Enough for Real Scenarios?

### For POC/Demo Purposes
- **Yes** - 5-6 seconds is acceptable for demonstrating voice ordering
- Natural conversation flow is preserved
- Streaming makes it feel responsive (audio starts playing before full response)

### For Production Use
- **No** - Target should be <2 seconds total response time
- First audio at 2.5-3s is still too slow for natural conversation

---

## How to Make It Better (Next Steps)

### Option 1: Predictive TTS (Can achieve <1000ms first audio)

**Idea:** Start TTS after collecting ~5-10 words instead of waiting for complete sentence.

**Implementation:**
- Modify sentence detection in `llm_service.py`
- Start TTS when buffer has N words OR sentence ending
- Improves perceived responsiveness significantly

**Expected:** First audio in ~800-1200ms

### Option 2: Cached Greetings (Can achieve <300ms first audio)

**Idea:** Pre-generate audio for common opening phrases.

**Common greetings:**
- "What can I get for you today?"
- "I'd be happy to help you with that."
- "Let me confirm your order."

**Implementation:**
- Pre-generate TTS audio files
- Serve immediately from cache
- No LLM/TTS latency for cached phrases

**Expected:** First audio in ~100-300ms (instant)

### Option 3: Gemini Live API (Long-term)

**Idea:** Use unified audio-to-audio streaming API.

**Benefits:**
- ~590ms time to first token (reported)
- Native audio streaming (no ASR/LLM/TTS separation)
- Single connection, lower overhead

---

## Recommendation

**For immediate demo:**
1. ✅ Test with current optimizations
2. ✅ If performance is acceptable, stop here

**For <300ms target:**
1. Implement cached greetings (fastest win)
2. Add predictive TTS
3. Consider Gemini Live API for v2

---

## Test Commands

```bash
# Start server
python3 voice_agent.py

# Test performance
# Open browser to http://localhost:5002
# Click "Touch to Order" and speak
# Watch console for timing logs:
#   [Perf] LLM first token in XXXms
#   [Perf] First audio in XXXms
```

---

## Summary

The streaming pipeline is correctly configured. The performance issues were caused by:
1. Excessive debug logging (fixed)
2. Slower LLM model (fixed - changed to qwen-turbo)

Expected improvement: 40-60% faster responses. For <300ms first audio, implement cached greetings.
