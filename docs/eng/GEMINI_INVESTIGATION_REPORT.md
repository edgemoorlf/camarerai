# Gemini Integration Investigation Report

**Date:** 2026-03-09
**Status:** Investigation Complete

---

## Executive Summary

The working project (`~/codes/camarerai_gemini`) uses a **completely different architecture** than what we've been building. The working project does NOT use Gemini Live API - it uses standard Gemini 1.5 Flash with separate TTS.

Our current implementation attempts to use Gemini Live API (native audio), which is causing compatibility issues.

---

## Architecture Comparison

### Working Project (camarerai_gemini)

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐     ┌─────────────┐
│   Record    │────▶│ Gemini 1.5   │────▶│  Google TTS │────▶│   Play      │
│  Audio      │     │  Flash       │     │  (REST API) │     │   MP3       │
│ (WebM)      │     │  (ASR+LLM)   │     │             │     │             │
└─────────────┘     └──────────────┘     └─────────────┘     └─────────────┘
                           │
                           ▼
                    Text Response
                    (JSON format)
```

**Key Components:**
1. **Audio Input**: MediaRecorder records WebM audio from microphone
2. **Gemini ASR+LLM**: `gemini-1.5-flash` model receives audio, returns text
3. **TTS**: Separate Google Cloud Text-to-Speech API call (REST)
4. **Audio Output**: HTMLAudioElement plays MP3 data URL

**Code Flow:**
```typescript
// 1. Record audio
const mediaRecorder = new MediaRecorder(stream);
const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });

// 2. Send to Gemini (not Live API!)
const response = await ai.models.generateContent({
    model: 'gemini-1.5-flash',  // NOT Live API
    contents: [{
        role: 'user',
        parts: [{
            inlineData: {
                mimeType: 'audio/webm',
                data: base64Audio
            }
        }]
    }]
});

// 3. Get text response
const text = response.text;  // JSON with text and language_code

// 4. Call Google TTS separately
const audioContent = await synthesizeSpeech(text, language_code);

// 5. Play audio
audioPlayer.src = `data:audio/mp3;base64,${audioContent}`;
audioPlayer.play();
```

---

### Our Current Project (camarerai)

```
┌─────────────┐     ┌─────────────────────────────┐     ┌─────────────┐
│   Record    │────▶│   Gemini Live API           │────▶│   Play      │
│  Audio      │     │   (Native Audio)            │     │   PCM       │
│  (PCM)      │     │   ASR + LLM + TTS combined  │     │             │
└─────────────┘     └─────────────────────────────┘     └─────────────┘
                              │
                              ▼
                    Function Calls (order updates)
```

**Key Components:**
1. **Audio Input**: WebSocket streaming of PCM 16-bit audio
2. **Gemini Live API**: Native audio model (`gemini-2.5-flash-native-audio-latest`)
3. **Audio Output**: Raw PCM 24kHz streaming back
4. **Function Calling**: Order updates interleaved with audio

---

## Key Differences

| Aspect | Working Project | Our Current Project |
|--------|-----------------|---------------------|
| **API Type** | Standard REST API | Live API (WebSocket) |
| **Model** | `gemini-1.5-flash` | `gemini-2.5-flash-native-audio-latest` |
| **Audio In** | WebM (recorded blob) | PCM 16kHz (streaming) |
| **Audio Out** | MP3 (Google TTS) | Raw PCM 24kHz |
| **Response** | Text → TTS → Audio | Audio directly |
| **Latency** | Higher (3 API calls) | Lower (streaming) |
| **Function Calls** | Not supported | Supported |

---

## Problems Identified

### 1. Audio Format Mismatch

**Our Issue:**
- Gemini Live API outputs raw PCM (`audio/pcm;rate=24000`)
- Browser's `decodeAudioData()` expects container formats (WAV, MP3, etc.)
- Raw PCM has no headers, so browser can't decode it

**Error:**
```
EncodingError: Unable to decode audio data
```

**Solutions:**
1. **Server-side**: Convert PCM to WAV before sending to client
2. **Client-side**: Use AudioWorklet to play raw PCM directly
3. **Alternative**: Use standard Gemini + separate TTS (like working project)

### 2. Wrong API Expectations

We assumed the working project used Gemini Live API, but it doesn't. It uses:
- Standard `generateContent()` API
- Separate Google Cloud TTS API
- Full audio files, not streaming

### 3. Model Compatibility

The `gemini-2.5-flash-native-audio-latest` model:
- Requires native audio SDK methods
- Outputs PCM, not MP3
- Has different function calling behavior

---

## Recommended Solutions

### Option 1: Fix Current Live API Implementation (Fastest)

Convert PCM to WAV on the server:

```python
def pcm_to_wav(pcm_data, sample_rate=24000):
    """Add WAV headers to raw PCM data"""
    # Add RIFF, fmt, and data chunk headers
    # Return WAV bytes
```

**Pros:**
- Keeps low-latency streaming
- Keeps function calling capability

**Cons:**
- More complex audio handling
- Browser needs to handle chunked WAV

### Option 2: Switch to Standard Gemini + TTS (Like Working Project)

Match the working project's architecture:

```
Client Audio → Gemini 1.5 Flash (ASR+LLM) → Text → Google TTS → MP3 → Play
```

**Pros:**
- Proven working code
- Simpler audio handling (MP3)
- Easier to debug

**Cons:**
- Higher latency (3 separate API calls)
- More expensive (Gemini + TTS calls)
- Loses "Live API" streaming benefits

### Option 3: Use Native Audio with AudioWorklet (Most Complex)

Play raw PCM directly in browser using AudioWorklet:

```javascript
// AudioWorklet processor
class PCMProcessor extends AudioWorkletProcessor {
    process(inputs, outputs, parameters) {
        // Fill output with PCM data from queue
    }
}
```

**Pros:**
- True native audio streaming
- Lowest latency

**Cons:**
- Complex Web Audio API code
- Browser compatibility issues
- Harder to debug

---

## Investigation Files Examined

1. **~/codes/camarerai_gemini/services/gemini.ts**
   - Uses `ai.models.generateContent()` (standard API)
   - Model: `gemini-1.5-flash`
   - Sends audio as `inlineData` (base64 WebM)
   - Receives text response

2. **~/codes/camarerai_gemini/services/tts.ts**
   - Uses Google Cloud Text-to-Speech REST API
   - Returns MP3 base64
   - Separate from Gemini call

3. **~/codes/camarerai_gemini/hooks/useVoiceAssistant.ts**
   - Records WebM audio with MediaRecorder
   - Calls Gemini, then TTS, then plays MP3
   - No streaming, sequential API calls

4. **~/codes/camarerai_gemini/components/VoiceAssistant.tsx**
   - Simple UI with HTMLAudioElement
   - No complex audio streaming logic

---

## Conclusion

The working project does NOT use Gemini Live API. It uses:
1. Standard Gemini API for ASR+LLM
2. Separate Google TTS for speech synthesis
3. MP3 audio playback (not PCM streaming)

Our current implementation tries to use Gemini Live API (native audio), which is more complex and requires different audio handling.

**Recommendation:** Choose between:
1. **Fix Live API**: Convert PCM→WAV on server (keeps streaming)
2. **Match Working Project**: Use standard Gemini + TTS (proven, simpler)

---

## Next Steps

1. Decide on architecture (Live API vs Standard)
2. If Live API: Implement PCM→WAV conversion
3. If Standard: Refactor to match working project pattern
4. Test audio playback with chosen approach
