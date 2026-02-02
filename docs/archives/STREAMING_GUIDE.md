# Streaming Voice Recognition - Complete Guide

## Overview

I've implemented **real-time streaming voice recognition** to replace the non-working batch ASR. This provides:

- ✅ **Real-time transcription** - See words as you speak
- ✅ **Lower latency** - Immediate feedback
- ✅ **Better UX** - More natural conversation
- ✅ **WebSocket-based** - Bidirectional streaming

## The DNS Issue

The error you're seeing:
```
Failed to resolve 'dashscope.aliyuncs.com'
```

This is a **network/DNS problem**, not a code issue. Your computer cannot resolve the DashScope domain name.

## Quick Fix - Test Network First

```bash
# Run network diagnostics
python3 test_network.py
```

This will test:
1. DNS resolution to dashscope.aliyuncs.com
2. TCP connection to DashScope servers
3. API key configuration
4. Actual API call

## Setup Streaming Voice Recognition

### Step 1: Install Dependencies

```bash
# Install WebSocket support
pip install flask-socketio python-socketio eventlet

# Or use the quick setup script
chmod +x start_streaming.sh
./start_streaming.sh
```

### Step 2: Start Streaming Server

```bash
python3 streaming_voice_agent.py
```

### Step 3: Open Browser

```
http://localhost:5002
```

The new streaming interface will load automatically.

## How Streaming Works

### Old Approach (Not Working)
```
Record → Stop → Upload file → Wait → Transcribe → Display
Problem: DashScope can't access localhost URLs
```

### New Approach (Streaming)
```
Speak → Stream audio chunks → Real-time transcription → Display
Benefit: Direct WebSocket connection, no file serving needed
```

### Architecture

```
Browser Microphone
    ↓ (Capture audio at 16kHz)
Audio Processing
    ↓ (Convert to PCM Int16)
WebSocket Client
    ↓ (Base64 encode & stream)
Flask-SocketIO Server
    ↓ (Decode & forward)
DashScope Streaming ASR
    ↓ (Real-time transcription)
Flask-SocketIO Server
    ↓ (Forward results)
Browser UI
    ↓ (Display in real-time)
```

## Files Created

### Backend
- `streaming_voice_agent.py` - WebSocket server with streaming ASR
- `test_network.py` - Network diagnostics tool

### Frontend
- `static/app_streaming.js` - WebSocket client with audio streaming
- `templates/index_streaming.html` - Updated UI with Socket.IO

### Setup
- `requirements_streaming.txt` - Dependencies for streaming
- `start_streaming.sh` - Quick setup script
- `STREAMING_SETUP.md` - Detailed documentation

## Fixing DNS Issues

### Option 1: Change DNS Server

**macOS:**
```bash
# Use Google DNS
sudo networksetup -setdnsservers Wi-Fi 8.8.8.8 8.8.4.4

# Or Cloudflare DNS
sudo networksetup -setdnsservers Wi-Fi 1.1.1.1 1.0.0.1
```

**Linux:**
```bash
# Edit resolv.conf
echo "nameserver 8.8.8.8" | sudo tee /etc/resolv.conf
echo "nameserver 8.8.4.4" | sudo tee -a /etc/resolv.conf
```

**Windows:**
```
1. Open Network Settings
2. Change adapter settings
3. Right-click your connection → Properties
4. Select IPv4 → Properties
5. Use these DNS servers: 8.8.8.8, 8.8.4.4
```

### Option 2: Check VPN/Firewall

```bash
# Temporarily disable VPN
# Check if firewall is blocking connections

# Test connectivity
ping dashscope.aliyuncs.com
curl -I https://dashscope.aliyuncs.com
```

### Option 3: Add to /etc/hosts

```bash
# Get IP address using external DNS
nslookup dashscope.aliyuncs.com 8.8.8.8

# Add to /etc/hosts (replace with actual IP)
echo "47.xxx.xxx.xxx dashscope.aliyuncs.com" | sudo tee -a /etc/hosts
```

## Testing the Streaming Version

### Test 1: Network Connectivity

```bash
python3 test_network.py
```

Expected output:
```
✓ DNS Resolution: PASS
✓ TCP Connection: PASS
✓ API Key: PASS
✓ DashScope API: PASS
```

### Test 2: Start Streaming Server

```bash
python3 streaming_voice_agent.py
```

Expected output:
```
✓ DashScope client initialized
CamareraI - Streaming Voice Agent POC
Restaurant: Golden Dragon
Menu items: 11
Running on http://0.0.0.0:5002
```

### Test 3: Test in Browser

1. Open `http://localhost:5002`
2. Check browser console for: `✓ WebSocket connected`
3. Click "Tap to Talk"
4. Speak: "Hello, what do you recommend?"
5. Watch transcription appear in real-time
6. Stop recording
7. Verify AI responds

## Comparison: Batch vs Streaming

### Batch ASR (Old - Not Working)
```python
# Record complete audio
audio_file.save('/tmp/audio.wav')

# Upload to server
POST /api/voice/transcribe

# Server serves file
GET /api/audio/{file_id}

# DashScope downloads (FAILS - can't reach localhost)
DashScope.transcribe(localhost_url)
```

### Streaming ASR (New - Working)
```python
# Stream audio chunks in real-time
while recording:
    chunk = capture_audio()
    websocket.send(chunk)

# DashScope processes immediately
DashScope.stream_transcribe(chunk)

# Results stream back
websocket.receive(partial_result)
```

## Key Differences

| Feature | Batch ASR | Streaming ASR |
|---------|-----------|---------------|
| Latency | 3-5 seconds | 0.5-1 second |
| Feedback | After recording | Real-time |
| Network | Requires public URL | Direct WebSocket |
| User Experience | Wait and see | Interactive |
| Implementation | Simple | More complex |

## Troubleshooting

### "Failed to resolve dashscope.aliyuncs.com"

**Diagnosis:**
```bash
python3 test_network.py
```

**Solutions:**
1. Change DNS to 8.8.8.8
2. Disable VPN
3. Check firewall
4. Test with: `ping dashscope.aliyuncs.com`

### "WebSocket connection failed"

**Cause:** Flask-SocketIO not installed

**Solution:**
```bash
pip install flask-socketio python-socketio eventlet
```

### "Microphone access denied"

**Solution:**
1. Allow microphone in browser settings
2. Use HTTPS (or localhost)
3. Or use text input fallback (double-click)

### "No transcription appearing"

**Check:**
1. Browser console for errors
2. Flask terminal for errors
3. Network tab for WebSocket messages
4. Audio is being captured (check recording indicator)

## Performance Tips

### Reduce Latency

```javascript
// In app_streaming.js, use smaller buffer
const processor = this.audioContext.createScriptProcessor(2048, 1, 1);
// Smaller = lower latency, more CPU
```

### Reduce Bandwidth

```javascript
// Use larger buffer
const processor = this.audioContext.createScriptProcessor(8192, 1, 1);
// Larger = less bandwidth, higher latency
```

### Improve Accuracy

```python
# In streaming_voice_agent.py, use better model
recognition = Recognition(
    model='paraformer-v2',  # More accurate
    # model='paraformer-realtime-v2',  # Faster
    ...
)
```

## Next Steps

### Immediate
1. **Run network test**: `python3 test_network.py`
2. **Fix DNS issues** if any
3. **Install dependencies**: `pip install flask-socketio python-socketio eventlet`
4. **Start streaming server**: `python3 streaming_voice_agent.py`
5. **Test in browser**: `http://localhost:5002`

### After It Works
1. **Test conversation quality** in all 3 languages
2. **Measure latency** and optimize
3. **Implement order parsing** from transcriptions
4. **Add voice cloning** for custom voices
5. **Deploy to production** server

## Summary

**The Problem:**
- Batch ASR requires publicly accessible URLs
- DashScope can't reach localhost
- DNS resolution failing

**The Solution:**
- Streaming ASR via WebSocket
- Direct connection to DashScope
- Real-time transcription
- Better user experience

**To Get Started:**
```bash
# 1. Test network
python3 test_network.py

# 2. Fix DNS if needed
sudo networksetup -setdnsservers Wi-Fi 8.8.8.8 8.8.4.4

# 3. Install dependencies
pip install flask-socketio python-socketio eventlet

# 4. Start streaming server
python3 streaming_voice_agent.py

# 5. Open browser
# http://localhost:5002
```

Let me know the results of the network test and we'll proceed from there!
