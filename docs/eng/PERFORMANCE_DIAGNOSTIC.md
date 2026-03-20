# Performance Diagnostic Report

**Date:** 2026-03-08
**Status:** Critical Issues Identified

## Current Performance (Measured)

| Metric | Current | Target | Status |
|--------|---------|--------|--------|
| LLM First Token | **983ms** | 200-300ms | 🔴 CRITICAL |
| LLM Total | **12,654ms** | <2000ms | 🔴 CRITICAL |
| TTS First Audio | **3,959ms** | 400-600ms | 🔴 CRITICAL |
| Total Response | **8,993ms** | <3000ms | 🔴 CRITICAL |

**Verdict:** Performance is unacceptable for production use.

---

## Root Cause Analysis

### 1. Verbose Debug Logging (HIGH IMPACT)

**Problem:** Every LLM chunk and TTS chunk is being logged:

```python
# In llm_service.py - this prints for EVERY token!
print(f"[TTS-Debug] Received chunk: '{delta.content}'")
print(f"[TTS-Debug] Sentence buffer now: '{sentence_buffer}'")
print(f"[TTS-Debug] has_sentence_ending: {has_ending}")
```

**Impact:**
- Console I/O is slow and blocking
- For a 500-token response = 500+ log lines
- Each print() can take 1-5ms → 500ms+ overhead per response

### 2. TTS Model: qwen3-tts-flash (MEDIUM IMPACT)

**Current:** `model='qwen3-tts-flash'`

This is a flash/quantized model which may have:
- Higher latency for first chunk
- Lower quality but not necessarily faster

**Alternative:** Try `qwen-tts` (standard) or `sambert`

### 3. LLM Model: qwen-plus (MEDIUM IMPACT)

**Current:** `model='qwen-plus'`

qwen-plus is balanced for quality/speed. Options:
- `qwen-turbo` - Faster, lower quality (might be acceptable for ordering)
- `qwen-max` - Slower, higher quality (not recommended)

### 4. Sentence Buffering Delay (MEDIUM IMPACT)

**Current Flow:**
1. LLM streams tokens
2. Accumulate until sentence ending (., !, ?)
3. THEN send to TTS

**Problem:** User waits for complete sentence before hearing ANY audio

**Example:**
```
"I'd be happy to recommend some dishes." → Wait for "." → Then TTS
```

**Better:** Start TTS after first few words

### 5. HTTP Connection Pool (UNCERTAIN)

The persistent HTTP client is configured but we're not 100% sure it's being reused correctly.

---

## Quick Fixes (Immediate - 30 min)

### Fix 1: Disable Debug Logging

**File:** `services/llm_service.py`

Comment out or reduce debug prints:
```python
# Remove these lines (or make them conditional):
# print(f"[TTS-Debug] Received chunk: '{delta.content}'")
# print(f"[TTS-Debug] Sentence buffer now: '{sentence_buffer}'")
# print(f"[TTS-Debug] has_sentence_ending: {has_ending}")
```

Keep only essential logs:
```python
print(f"[LLM] First token in {duration}ms")
print(f"[TTS] First audio in {duration}ms")
```

**Expected Improvement:** 30-50% reduction in total time

### Fix 2: Reduce TTS Verbosity

**File:** `dashscope_client.py`

Remove chunk logging:
```python
# Remove:
# print(f"[TTS] Chunk {chunk_count}: {len(audio_chunk)} bytes")
```

---

## Medium Fixes (1-2 hours)

### Fix 3: Faster LLM Model

**File:** `services/llm_service.py:40`

Change:
```python
model='qwen-turbo'  # Instead of qwen-plus
```

**Expected Improvement:** 30-40% faster first token

### Fix 4: Predictive TTS (Start Before Sentence Complete)

Start TTS after collecting ~5-10 words instead of waiting for full sentence.

**File:** `services/llm_service.py`

Modify the sentence detection logic.

---

## Streaming Verification

The streaming **IS** configured correctly:

| Component | Streaming Status |
|-----------|-----------------|
| ASR | ✅ `Recognition` is streaming by design |
| LLM | ✅ `stream=True` set in llm_service.py:44 |
| TTS | ✅ `stream=True` set in llm_service.py:180 |

**The problem is NOT streaming configuration - it's overhead and model latency.**

---

## Recommendations

### Option A: Quick Wins (Recommended for Demo)

1. ✅ Disable debug logging (30 min)
2. ✅ Switch to qwen-turbo (5 min)
3. ✅ Test and measure

**Expected Result:**
- LLM first token: 983ms → ~400-500ms
- Total response: 9s → ~4-5s

### Option B: Aggressive Optimization

1. Implement Option A
2. Add predictive TTS (start TTS after 5 words)
3. Cache common greetings

**Expected Result:**
- First audio: <1000ms
- Total response: <3s

### Option C: Architecture Change (Long-term)

Consider Gemini Live API:
- Unified streaming (no separate ASR/LLM/TTS calls)
- Native audio-to-audio processing
- ~590ms time to first token (reported)

---

## Next Steps

**Immediate (do this now):**
1. Disable debug logging in `llm_service.py`
2. Switch to `qwen-turbo`
3. Restart server
4. Test and measure

**Expected time:** 30 minutes
**Expected improvement:** 40-60% faster

Want me to implement the quick fixes now?
