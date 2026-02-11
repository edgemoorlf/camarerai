# Debugging TTS Issues - Quick Guide

## 1. Check Server Logs (Real-time)

### Watch all logs in real-time:
```bash
tail -f /tmp/voice_agent.log
```

### Watch only TTS-related logs:
```bash
tail -f /tmp/voice_agent.log | grep -E "\[TTS\]|\[LLM→TTS\]|\[LLM\]"
```

### Watch for errors:
```bash
tail -f /tmp/voice_agent.log | grep -i error
```

## 2. Check Recent Logs

### Last 50 lines:
```bash
tail -50 /tmp/voice_agent.log
```

### Last 100 TTS-related lines:
```bash
tail -200 /tmp/voice_agent.log | grep -E "\[TTS\]|\[LLM→TTS\]"
```

### Search for specific errors:
```bash
grep -i "synthesis error" /tmp/voice_agent.log | tail -20
```

## 3. Check Browser Console

1. Open browser DevTools: **F12** or **Right-click → Inspect**
2. Go to **Console** tab
3. Look for errors (red text)
4. Look for TTS-related messages:
   - `[TTS] Streaming synthesis started`
   - `[TTS] Received chunk X`
   - `[AudioStreamPlayer] ...`

## 4. Common Issues

### Issue 1: No audio chunks received
**Symptoms**: Logs show `[LLM→TTS] Sentence complete` but no audio chunks
**Check**:
```bash
tail -100 /tmp/voice_agent.log | grep -A 5 "LLM→TTS"
```

### Issue 2: Audio chunks received but not playing
**Symptoms**: Logs show chunks sent, but no sound
**Check**: Browser console for AudioStreamPlayer errors

### Issue 3: DashScope TTS streaming not working
**Symptoms**: TTS errors in logs
**Check**:
```bash
grep "TTS.*error\|TTS.*Error\|Streaming error" /tmp/voice_agent.log | tail -20
```

## 5. Enable Debug Mode

### Restart server with verbose logging:
```bash
# Kill current server
lsof -ti:5002 | xargs kill -9

# Start with debug output
python3 voice_agent.py 2>&1 | tee /tmp/voice_agent_debug.log
```

## 6. Test TTS Directly

### Test if DashScope TTS streaming works:
```bash
python3 -c "
from dashscope_client import DashScopeClient
client = DashScopeClient()

print('Testing TTS streaming...')
for chunk in client.synthesize('你好，测试', voice='Cherry', stream=True):
    print(f'Chunk: {chunk}')
"
```

## 7. Check Network

### Check if DashScope API is reachable:
```bash
curl -I https://dashscope.aliyuncs.com
```

## 8. Rollback to Non-Streaming TTS

If streaming TTS is broken, temporarily disable it:

**Edit voice_agent.py line ~730:**
```python
# Change from:
for audio_chunk in dashscope_client.synthesize(
    sentence_buffer.strip(),
    voice=voice,
    language_type='Auto',
    stream=True  # ← Change this to False
):

# To:
audio_url = dashscope_client.synthesize(
    sentence_buffer.strip(),
    voice=voice,
    language_type='Auto',
    stream=False  # ← Non-streaming mode
)

# Then emit the URL:
emit('synthesis_complete', {
    'session_id': session_id,
    'audio_url': audio_url
})
```

## 9. Quick Diagnostic Commands

```bash
# Check if server is running
ps aux | grep voice_agent

# Check server port
lsof -i :5002

# Check recent errors
tail -100 /tmp/voice_agent.log | grep -i error

# Check TTS activity
tail -100 /tmp/voice_agent.log | grep TTS

# Check full conversation flow
tail -200 /tmp/voice_agent.log | grep -E "\[ASR\]|\[LLM\]|\[TTS\]"
```

## 10. What to Look For

### Good signs ✅:
- `[LLM→TTS] Sentence complete, streaming to TTS: ...`
- `[TTS] Sent chunk X (url) to client`
- No error messages

### Bad signs ❌:
- `[TTS] Streaming error: ...`
- `TTS returned no audio URL`
- `Synthesis error: ...`
- Python exceptions/tracebacks

---

**Next**: Run the diagnostic commands above and share what you see!
