# CamareraI - AI Voice Agent for Restaurants

**Status:** POC - Streaming Voice Recognition Implementation
**Last Updated:** 2026-01-31

---

## 🎯 Current Implementation

**Active File:** `voice_agent.py`
**Status:** ✅ Ready to test
**Architecture:** WebSocket-based streaming ASR

### What Works
- ✅ Real-time voice transcription (streaming)
- ✅ LLM conversation (English, Mandarin, Cantonese)
- ✅ Text-to-speech responses
- ✅ Session management
- ✅ Text input fallback (double-click conversation area)

### What's Not Implemented Yet
- ❌ Order parsing from conversation
- ❌ Voice cloning
- ❌ Speaker identification
- ❌ Kitchen integration

---

## 🚀 Quick Start

### 1. Check System Requirements

```bash
python3 test_all.py
```

This verifies:
- All files present
- Dependencies installed
- Network connectivity to DashScope
- API key configured

### 2. Install Dependencies (if needed)

```bash
pip install flask-socketio python-socketio eventlet dashscope flask python-dotenv
```

### 3. Start the Server

```bash
python3 voice_agent.py
```

### 4. Open Browser

```
http://localhost:5002
```

### 5. Test Voice Recognition

1. Click "Tap to Talk"
2. Speak: "Hello, what do you recommend for 2 people?"
3. Watch transcription appear in real-time
4. Stop recording
5. AI responds with menu recommendations

**Fallback:** Double-click conversation area to type instead of speaking.

---

## 📁 Project Structure

### Core Files (Use These)

```
voice_agent.py               # Main server (WebSocket + streaming ASR)
dashscope_client.py          # DashScope API wrapper
test_all.py                  # Complete system check
test_network.py              # Network diagnostics

data/
├── menu.json                # Restaurant menu (multilingual)
├── knowledge.json           # Beyond-menu knowledge
├── table_names.json         # Table name assignments
└── voices.json              # Voice configuration

static/
├── app_streaming.js         # WebSocket client
└── style.css                # UI styling

templates/
└── index_streaming.html     # Main UI
```

### Deprecated Files (Don't Use)

```
poc_voice_agent.py           # Old batch ASR (doesn't work)
static/app.js                # Old client (doesn't work)
templates/index.html         # Old UI (doesn't work)
test_dashscope.py            # Old test (use test_all.py instead)
quick_test.py                # Old test (use test_all.py instead)
```

### Documentation

```
README.md                    # This file - single source of truth
STREAMING_COMPLETE.md        # Implementation details
requirements_streaming.txt   # Dependencies list
```

---

## 🔧 Troubleshooting

### Issue 1: DNS Resolution Error

**Symptom:**
```
Failed to resolve 'dashscope.aliyuncs.com'
```

**Fix:**
```bash
# Change DNS to Google DNS
sudo networksetup -setdnsservers Wi-Fi 8.8.8.8 8.8.4.4

# Test again
python3 test_network.py
```

### Issue 2: WebSocket Connection Failed

**Symptom:**
```
WebSocket connection error
```

**Fix:**
```bash
# Install dependencies
pip install flask-socketio python-socketio eventlet

# Restart server
python3 voice_agent.py
```

### Issue 3: No Transcription Appearing

**Checklist:**
- [ ] Microphone permission granted in browser
- [ ] Browser console shows "WebSocket connected"
- [ ] Flask terminal shows no errors
- [ ] Network test passes (`python3 test_network.py`)

**Fallback:**
- Double-click conversation area
- Type your message instead

### Issue 4: Import Errors

**Symptom:**
```
ModuleNotFoundError: No module named 'flask_socketio'
```

**Fix:**
```bash
pip install -r requirements_streaming.txt
```

---

## 🎤 How It Works

### Architecture

```
Browser Microphone (16kHz PCM)
    ↓ WebSocket
Flask-SocketIO Server
    ↓ WebSocket
DashScope Streaming ASR (Paraformer)
    ↓ Real-time transcription
Flask-SocketIO Server
    ↓ WebSocket
Browser UI (live updates)
```

### Flow

1. **User clicks "Tap to Talk"**
   - Browser captures audio at 16kHz
   - Converts to PCM format
   - Streams via WebSocket

2. **Server receives audio**
   - Forwards to DashScope streaming ASR
   - Receives partial transcription results
   - Sends back to browser in real-time

3. **User stops recording**
   - Final transcription sent to LLM
   - AI generates response
   - TTS synthesizes audio
   - Audio plays back to user

**Latency:** 0.5-1 second (real-time streaming)

---

## 🧪 Testing

### Test 1: System Check

```bash
python3 test_all.py
```

Expected output:
```
✓ Files: PASS
✓ Packages: PASS
✓ DNS: PASS
✓ API Key: PASS
✓ DashScope API: PASS

🎉 Your system is ready!
```

### Test 2: Network Connectivity

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

### Test 3: Conversation Flow

**English:**
```
You: "Hi! What do you recommend for 2 people?"
AI: [Suggests Kung Pao Chicken and Dan Dan Noodles]
```

**Mandarin:**
```
You: "你好！有什么推荐的吗？"
AI: [中文回复推荐菜品]
```

**Cantonese:**
```
You: "你好！有咩推薦？"
AI: [粵語回覆推薦菜式]
```

---

## 📊 Configuration

### Environment Variables

Create `.env` file:
```bash
DASHSCOPE_API_KEY=sk-your-key-here
```

### Menu Data

Edit `data/menu.json` to customize:
- Restaurant name
- Menu items (multilingual)
- Prices
- Dietary information
- Staff recommendations

### Voice Settings

Edit `data/voices.json` to configure:
- Default voice
- Voice per table
- Voice cloning settings (future)

---

## 🐛 Known Issues

1. **DNS Resolution** - Some networks cannot resolve dashscope.aliyuncs.com
   - **Fix:** Change DNS to 8.8.8.8 or 1.1.1.1

2. **Microphone Permission** - Browser may block microphone access
   - **Fix:** Allow microphone in browser settings, or use text input

3. **Order Parsing** - Not yet implemented
   - **Workaround:** Orders must be manually tracked for now

4. **Voice Cloning** - Not available in basic DashScope SDK
   - **Status:** Planned for future implementation

---

## 📈 Roadmap

### Phase 1: Core Voice Recognition ✅ DONE
- [x] Streaming ASR implementation
- [x] WebSocket architecture
- [x] Real-time transcription
- [x] LLM integration
- [x] TTS integration
- [x] Multilingual support

### Phase 2: Order Management 🔄 IN PROGRESS
- [ ] Parse menu items from conversation
- [ ] Build order in real-time
- [ ] Order confirmation workflow
- [ ] Send to kitchen system

### Phase 3: Advanced Features 📋 PLANNED
- [ ] Voice cloning for staff
- [ ] Speaker identification
- [ ] Multi-speaker support
- [ ] Order modification
- [ ] Payment integration

### Phase 4: Production Ready 📋 PLANNED
- [ ] Deploy to cloud
- [ ] Performance optimization
- [ ] Error handling
- [ ] Analytics dashboard
- [ ] Multi-restaurant support

---

## 🤝 Contributing

This is a POC project. Current focus:
1. Get streaming voice recognition working reliably
2. Test conversation quality in all 3 languages
3. Implement order parsing
4. Improve user experience

---

## 📝 Development Notes

### Why Streaming ASR?

**Old approach (batch):**
- Record → Upload → Transcribe → Display
- 3-5 second latency
- Required public URL (doesn't work on localhost)

**New approach (streaming):**
- Real-time audio streaming
- 0.5-1 second latency
- Direct WebSocket connection
- Better UX

### Tech Stack

- **Backend:** Python + Flask + Flask-SocketIO
- **Frontend:** Vanilla JavaScript + WebSocket
- **AI Services:** Alibaba DashScope (ASR, LLM, TTS)
- **Data:** JSON files (menu, knowledge, config)

### Why DashScope?

- Single API provider (ASR + LLM + TTS)
- Cost-effective (~$60/month for POC)
- Chinese-optimized (native Mandarin/Cantonese)
- Streaming ASR support
- Good documentation

---

## 📞 Support

### Getting Help

1. **Run diagnostics:**
   ```bash
   python3 test_all.py
   ```

2. **Check documentation:**
   - This README (single source of truth)
   - STREAMING_COMPLETE.md (implementation details)

3. **Common issues:**
   - DNS resolution → Change DNS to 8.8.8.8
   - Missing packages → `pip install -r requirements_streaming.txt`
   - WebSocket errors → Restart server
   - No transcription → Check microphone permission

### Reporting Issues

When reporting issues, include:
1. Output of `python3 test_all.py`
2. Error messages from Flask terminal
3. Error messages from browser console (F12)
4. What you were trying to do
5. What actually happened

---

## 📄 License

MIT License - See LICENSE file for details

---

## 🎯 Quick Reference

### Start Server
```bash
python3 voice_agent.py
```

### Run Tests
```bash
python3 test_all.py          # Complete system check
python3 test_network.py      # Network diagnostics only
```

### Install Dependencies
```bash
pip install -r requirements_streaming.txt
```

### Access Application
```
http://localhost:5002
```

### Text Input Fallback
```
Double-click conversation area → Type message
```

---

**Last Updated:** 2026-01-31
**Version:** POC v0.2 (Streaming)
**Status:** Ready for testing
