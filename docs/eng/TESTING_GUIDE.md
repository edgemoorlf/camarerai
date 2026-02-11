# Testing Guide - End-to-End Streaming

**Server**: http://localhost:5002
**Status**: Running with end-to-end streaming enabled

---

## Quick Test Scenarios

### Test 1: Simple Order (Chinese)
**Say**: "我要一份麻婆豆腐"

**Expected**:
- Audio starts within 1.5-2 seconds
- Smooth playback
- No long silence

**What to check**:
- Time from when you stop speaking to when audio starts
- Audio quality and smoothness
- Any gaps or stuttering

---

### Test 2: Conversation (Chinese)
**Say**: "你们有什么推荐吗？"

**Expected**:
- Audio starts quickly
- Continues smoothly as AI generates response
- Natural conversation flow

**What to check**:
- Does audio start before AI finishes thinking?
- Are there gaps between sentences?
- Does it feel natural?

---

### Test 3: Multiple Items (Chinese)
**Say**: "我要两份麻婆豆腐，一份回锅肉，还有三瓶青岛啤酒"

**Expected**:
- Audio starts quickly
- Order is captured correctly
- Smooth playback

**What to check**:
- Response time
- Order accuracy
- Audio quality

---

### Test 4: English Order
**Say**: "I want one Mapo Tofu and two beers"

**Expected**:
- Same fast response time
- English TTS works well
- Order captured correctly

---

## What to Look For

### Good Signs ✅
- Audio starts within 1-2 seconds
- Smooth, continuous playback
- No awkward pauses
- Natural conversation flow
- Feels responsive and fast

### Bad Signs ❌
- Long silence (> 3 seconds)
- Choppy or stuttering audio
- Gaps between sentences
- Audio cuts off
- Still feels slow

---

## Monitoring

### Check Server Logs
```bash
tail -f /tmp/voice_agent.log | grep -E "\[LLM\]|\[TTS\]|\[LLM→TTS\]"
```

**Look for**:
- `[LLM] Starting streaming response generation`
- `[LLM→TTS] Sentence complete, streaming to TTS: ...`
- `[TTS] Sent chunk X to client`

### Check Browser Console
Open browser DevTools (F12) and look for:
- `[TTS] Streaming synthesis started`
- `[TTS] Received chunk X (url/data)`
- `[AudioStreamPlayer] Playing next chunk`

---

## Comparison

### Before (Non-streaming)
```
You: "我要一份麻婆豆腐"
[Long silence - 4-5 seconds]
AI: "好的，我为您添加一份麻婆豆腐..."
```

### After (End-to-end streaming)
```
You: "我要一份麻婆豆腐"
[Brief pause - 1.5 seconds]
AI: "好的，" [audio starts immediately]
    "我为您添加一份麻婆豆腐..." [continues smoothly]
```

---

## Troubleshooting

### If audio is still slow:
1. Check server logs for errors
2. Check browser console for errors
3. Verify network connection
4. Try refreshing the page

### If audio is choppy:
1. Check network speed
2. Look for TTS streaming errors in logs
3. May need to adjust sentence detection

### If no audio at all:
1. Check browser audio permissions
2. Check server logs for TTS errors
3. Verify DashScope API is working

---

## Feedback Needed

Please let me know:

1. **Response time**: How long from when you stop speaking to when audio starts?
2. **Audio quality**: Is playback smooth or choppy?
3. **User experience**: Does it feel fast and responsive?
4. **Any issues**: Errors, gaps, stuttering, etc.

---

**Ready to test!** 🚀

Open http://localhost:5002 and try the test scenarios above.
