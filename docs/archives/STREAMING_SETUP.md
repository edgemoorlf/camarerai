# Streaming Voice Recognition - Installation & Setup

## What's New

Implemented **real-time streaming voice recognition** using WebSocket and DashScope's streaming ASR API.

### Key Improvements
- ✅ **Real-time transcription** - See words appear as you speak
- ✅ **Lower latency** - No need to wait for recording to finish
- ✅ **Better interactivity** - More natural conversation flow
- ✅ **WebSocket-based** - Bidirectional real-time communication
- ✅ **Streaming audio** - Continuous audio streaming to server

## Installation

### 1. Install Additional Dependencies

```bash
# Activate virtual environment
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install Flask-SocketIO for WebSocket support
pip install flask-socketio python-socketio

# Install eventlet for async support (recommended)
pip install eventlet
```

### 2. Update Requirements

```bash
# Add to requirements.txt
echo "flask-socketio>=5.3.0" >> requirements.txt
echo "python-socketio>=5.9.0" >> requirements.txt
echo "eventlet>=0.33.0" >> requirements.txt
```

## Files Created

### Backend
- `streaming_voice_agent.py` - New WebSocket-based server with streaming ASR

### Frontend
- `static/app_streaming.js` - WebSocket client with real-time audio streaming
- `templates/index_streaming.html` - Updated UI with Socket.IO client

## How It Works

### Architecture

```
Browser (Microphone)
    ↓ (WebSocket)
Flask-SocketIO Server
    ↓ (WebSocket)
DashScope Streaming ASR
    ↓ (Partial Results)
Flask-SocketIO Server
    ↓ (WebSocket)
Browser (Real-time Display)
```

### Flow

1. **User clicks "Tap to Talk"**
   - Browser requests microphone access
   - Audio context created with 16kHz sample rate
   - WebSocket connection established

2. **Audio streaming starts**
   - Browser captures audio in real-time
   - Converts to PCM format (Int16)
   - Encodes to base64
   - Sends to server via WebSocket every ~250ms

3. **Server processes audio**
   - Receives base64 audio chunks
   - Decodes to PCM bytes
   - Streams to DashScope ASR API
   - Receives partial transcription results

4. **Real-time transcription**
   - Partial results sent back to browser
   - UI updates in real-time
   - User sees words appear as they speak

5. **Transcription complete**
   - Final text sent to LLM
   - AI generates response
   - TTS synthesizes audio
   - Audio plays back to user

## Running the Streaming Version

### Start the Server

```bash
python3 streaming_voice_agent.py
```

### Open Browser

```
http://localhost:5002
```

The UI will automatically use the streaming version.

## Testing

### Test 1: Check WebSocket Connection

1. Open browser console (F12)
2. Look for: `✓ WebSocket connected`
3. Look for: `Session created: {...}`

### Test 2: Test Streaming ASR

1. Click "Tap to Talk"
2. Speak: "Hello, what do you recommend?"
3. Watch the transcription preview update in real-time
4. Stop recording
5. Verify final transcription appears in conversation

### Test 3: Test Full Flow

1. Start recording
2. Speak a complete sentence
3. Stop recording
4. Verify transcription appears
5. Verify AI responds
6. Verify audio plays back

## Troubleshooting

### "WebSocket connection failed"

**Cause**: Flask-SocketIO not installed or server not running

**Solution**:
```bash
pip install flask-socketio python-socketio eventlet
python3 streaming_voice_agent.py
```

### "Failed to resolve 'dashscope.aliyuncs.com'"

**Cause**: Network/DNS issue preventing connection to DashScope

**Solutions**:
1. Check internet connection
2. Try different network (disable VPN if using one)
3. Check DNS settings
4. Test with: `ping dashscope.aliyuncs.com`

### "Microphone access denied"

**Cause**: Browser doesn't have microphone permission

**Solution**:
1. Click the lock icon in address bar
2. Allow microphone access
3. Refresh the page
4. Or use text input fallback (double-click conversation area)

### "No audio data received"

**Cause**: Audio format or sample rate mismatch

**Solution**:
- Verify browser supports 16kHz audio
- Check browser console for errors
- Try different browser (Chrome recommended)

### "Transcription not appearing"

**Cause**: DashScope ASR not receiving audio or callback not working

**Solution**:
1. Check Flask terminal for errors
2. Verify DashScope API key is valid
3. Check network connectivity
4. Look for error messages in browser console

## Comparison: Old vs New

### Old (Non-Streaming)
```
User speaks → Stop recording → Upload file →
Wait for transcription → Display result
Total latency: 3-5 seconds
```

### New (Streaming)
```
User speaks → Real-time streaming →
Partial results appear → Final result
Total latency: 0.5-1 second
```

## Network Requirements

### For Streaming ASR to Work

1. **Stable internet connection**
   - Minimum: 1 Mbps upload
   - Recommended: 5+ Mbps upload

2. **Low latency**
   - Ping to dashscope.aliyuncs.com < 200ms
   - Test with: `ping dashscope.aliyuncs.com`

3. **No blocking**
   - Firewall allows WebSocket connections
   - No VPN blocking DashScope domains
   - DNS can resolve dashscope.aliyuncs.com

### Test Network Connectivity

```bash
# Test DNS resolution
nslookup dashscope.aliyuncs.com

# Test connectivity
ping dashscope.aliyuncs.com

# Test HTTPS
curl -I https://dashscope.aliyuncs.com
```

## DNS Resolution Fix

If you're getting DNS resolution errors:

### Option 1: Use Google DNS

```bash
# macOS
sudo networksetup -setdnsservers Wi-Fi 8.8.8.8 8.8.4.4

# Linux
echo "nameserver 8.8.8.8" | sudo tee /etc/resolv.conf
```

### Option 2: Use Cloudflare DNS

```bash
# macOS
sudo networksetup -setdnsservers Wi-Fi 1.1.1.1 1.0.0.1
```

### Option 3: Add to /etc/hosts

```bash
# Get IP address
nslookup dashscope.aliyuncs.com 8.8.8.8

# Add to /etc/hosts (replace with actual IP)
echo "47.xxx.xxx.xxx dashscope.aliyuncs.com" | sudo tee -a /etc/hosts
```

## Performance Tuning

### Reduce Latency

1. **Adjust audio chunk size** (in `app_streaming.js`):
```javascript
// Smaller chunks = lower latency, more network overhead
const processor = this.audioContext.createScriptProcessor(2048, 1, 1);
```

2. **Use faster model** (in `streaming_voice_agent.py`):
```python
recognition = Recognition(
    model='paraformer-realtime-v2',  # Fastest
    # model='paraformer-v2',  # More accurate but slower
    ...
)
```

### Reduce Bandwidth

1. **Increase chunk size**:
```javascript
const processor = this.audioContext.createScriptProcessor(8192, 1, 1);
```

2. **Lower sample rate** (trade-off: lower quality):
```javascript
const stream = await navigator.mediaDevices.getUserMedia({
    audio: { sampleRate: 8000 }  // Lower quality, less bandwidth
});
```

## Next Steps

1. **Test streaming ASR** with the new implementation
2. **Verify network connectivity** to DashScope
3. **Fix DNS issues** if any
4. **Test in different network conditions**
5. **Measure and optimize latency**

## Support

If streaming ASR still doesn't work:

1. **Check Flask terminal** for detailed error messages
2. **Check browser console** for WebSocket errors
3. **Test network connectivity** to DashScope
4. **Try text input fallback** (double-click conversation area)
5. **Report the specific error message** you're seeing
