# CamareraI - Voice Ordering System

**Status:** POC - Multi-Provider Architecture
**Last Updated:** 2026-03-10
**Branch:** `feature/gemini-live-api`

> **Note:** The codebase now supports multiple AI providers: DashScope, Gemini Standard API, and Gemini Live API. Use `PROVIDER` env var to switch between them.

---

## 🎯 Current Implementation

**Entry Point:** `main.py`
**Provider:** Configurable (`dashscope`, `gemini`, `gemini_live`)
**Status:** ✅ Ready to test
**Architecture:** Modular provider-specific voice agents with shared components

### 🎯 Current Focus: Performance Optimization

**Problem:** First audio latency (~400-600ms) is too slow for snappy demos.
**Target:** Reduce to <300ms for natural conversation feel.

**Current Metrics:**
- LLM first token: ~200-300ms
- First audio: ~400-600ms
- Total response: ~1600ms

See [docs/eng/CURRENT_STATUS.md](docs/eng/CURRENT_STATUS.md) for detailed optimization plan.

### What Works ✅
- ✅ **Touch to Order button** - Large button to start ordering (browser security compliant)
- ✅ **Always-listening mode** - Microphone streams continuously after button tap
- ✅ **Natural conversation** - Speak naturally, AI responds when you finish
- ✅ **Language matching** - AI responds in your language (Chinese/English)
- ✅ **Minimal UI** - Clean status indicator + order summary only
- ✅ **Real-time voice transcription** (streaming)
- ✅ **LLM conversation** (English, Mandarin, Cantonese)
- ✅ **Text-to-speech responses** (streaming)
- ✅ **Session management** - Full lifecycle with persistence, "Tap for Anything"
- ✅ **Closing remark detection** - Detects "thank you", "谢谢", "唔該" and resets
- ✅ **Session boundaries** - Clean reset between customers
- ✅ **Order parsing** - Extracts items from conversation in any language
- ✅ **Order display** - Shows items with quantities and prices
- ✅ **Order calculations** - Automatic subtotal, tax (9%), and total
- ✅ **Order modifications** - Add, remove, or change quantities
- ✅ **Real-time updates** - Order panel updates as items are added
- ✅ **Performance monitoring** - Real-time metrics in UI
- ✅ **Barge-in** - SPACE key to interrupt AI (voice filtering on separate branch)

### What's Not Implemented Yet ⬜
- ❌ Context management (full conversation history)
- ❌ Error handling for invalid menu items
- ❌ Order confirmation before sending to kitchen
- ❌ Fuzzy item matching (e.g., "chicken" → "Kung Pao Chicken")
- ❌ Voice cloning
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
pip install -r requirements.txt
```

### 3. Start the Server

**DashScope (default - full streaming):**
```bash
python3 main.py
# or explicitly:
PROVIDER=dashscope python3 main.py
```

**Gemini Standard API (batch ASR+LLM, DashScope TTS):**
```bash
PROVIDER=gemini python3 main.py
```

**Gemini Live API (native bidirectional audio streaming):**
```bash
PROVIDER=gemini_live python3 main.py
```

### 4. Open Browser

```
http://localhost:5002
```

Server also available on network:
- Local: http://127.0.0.1:5002
- Network: http://192.168.1.139:5002

### 5. Test Complete Flow

1. **Page loads** - "Touch to Order" button appears
2. **Tap button** - Browser requests microphone permission
3. **Grant permission** - Enrollment prompt appears
4. **Enrollment**: Say "Hello, I'd like to order" (2.5 seconds)
5. **Enrollment completes** - Status shows "Listening"
6. **Order items**: "I'd like the Kung Pao Chicken"
7. **Watch order panel** - Item appears with price
8. **Modify order**: "Actually, make that two"
9. **Watch update** - Quantity changes to x2, total updates
10. **Test barge-in**: While AI speaks, interrupt (should work)
11. **Test filtering**: Have another person speak (should NOT trigger)
12. **End session**: Say "Thank you" or "谢谢" or "唔該"
13. **AI confirms** - Responds with confirmation
14. **Session resets** - Order clears, button reappears for next customer

**Interrupt anytime:** Press SPACE or start speaking to interrupt AI (only enrolled customer)

**Debug Panel:** Click 🐛 button (bottom right) to see transcription and responses

---

## 🎤 Speaker Verification (Deferred)

Speaker verification with client-side voice fingerprinting is implemented on the `experiment/speaker-id-fingerprint` branch but **deferred** for now.

**Why deferred?**
- Performance (first audio latency) is the current blocker for demos
- Speaker verification is a nice-to-have differentiator, not essential
- Can be merged after performance is optimized

**Quick info:**
- **Latency:** 5ms (client-side) vs 116-416ms (backend)
- **Accuracy:** 70-75% expected
- See [docs/eng/FINAL_RECOMMENDATION.md](docs/eng/FINAL_RECOMMENDATION.md) on that branch for full comparison

**Current barge-in:** SPACE key only (no voice filtering)

---

## 📁 Project Structure

### Core Files (Active)

```
main.py                          # Entry point - launches appropriate provider
config.py                        # Centralized configuration

# Provider-specific voice agents (choose one via PROVIDER env var)
voice_agent_dashscope.py         # DashScope ASR+LLM+TTS (streaming)
voice_agent_gemini_standard.py   # Gemini ASR+LLM + DashScope TTS
voice_agent_gemini_live.py       # Gemini Live API (native audio streaming)

# Shared components
models/
└── conversation_session.py      # Session management (provider-agnostic)
routes/
└── api.py                       # HTTP API routes (shared)
services/
├── order_service.py             # Order processing logic
├── llm_service.py               # LLM streaming with function calling
├── dashscope_service.py         # DashScope API wrapper
├── gemini_standard_service.py   # Gemini Standard API (ASR+LLM)
├── gemini_live_service.py       # Gemini Live API service
└── provider_factory.py          # Service factory

performance_monitor.py           # Real-time performance metrics
test_all.py                      # Complete system check

data/
├── menu.json                # Restaurant menu (multilingual)
├── knowledge.json           # Beyond-menu knowledge
├── table_names.json         # Table name assignments
└── voices.json              # Voice configuration

static/
├── app.js                   # Always-listening WebSocket client
├── audio_stream_player.js   # Streaming audio playback
├── performance_monitor.js   # Performance metrics UI
└── style.css                # Minimal UI styling

templates/
└── index.html               # Minimal UI (status + order summary)

# Note: speaker_fingerprint.js is on experiment/speaker-id-fingerprint branch
Note: voice_agent.py is the legacy file (kept for reference, use main.py instead)
```

### Documentation

```
README.md                    # This file - single source of truth
CLAUDE.md                    # AI assistant guidelines
docs/eng/CURRENT_STATUS.md   # Latest status & performance optimization plan
docs/
├── PLAN.md                  # Overall project plan and vision
├── eng/
│   ├── CURRENT_STATUS.md    # Current status & next steps ⭐
│   ├── IMPLEMENTATION_PLAN.md     # Technical implementation plan
│   ├── IMPLEMENTATION_STATUS.md   # Implementation status (older)
│   └── TEST_PLAN.md               # Comprehensive test plan
└── prd/
    └── PRODUCT_DESIGN.md    # Product design decisions

# Speaker verification docs (on separate branch):
# CLIENT_SIDE_FINGERPRINT.md, FINAL_RECOMMENDATION.md
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
pip install -r requirements.txt

# Restart server
python3 main.py
```

### Issue 3: Microphone Not Starting

**Checklist:**
- [ ] Tapped "Touch to Order" button
- [ ] Granted microphone permission in browser
- [ ] Browser console shows "WebSocket connected"
- [ ] Flask terminal shows "Always-listening mode active"
- [ ] Network test passes (`python3 test_network.py`)

**Debug:**
- Open debug panel (🐛 button)
- Check if session is created
- Check browser console for errors (F12)
- Try refreshing page and tapping button again


## 🎤 How It Works

### Architecture (DashScope Mode)

```
Browser Microphone (16kHz PCM)
    ↓ WebSocket (continuous streaming)
Flask-SocketIO Server
    ↓ WebSocket
DashScope Streaming ASR (Paraformer)
    ↓ Real-time transcription + sentence detection
Flask-SocketIO Server
    ↓ Auto-send to LLM on sentence end
DashScope LLM (Qwen)
    ↓ Stream response (sentence-by-sentence)
DashScope TTS (Sambert)
    ↓ Stream audio chunks
Browser (streaming audio playback)
```

**End-to-End Streaming:** ASR → LLM → TTS streams continuously for low latency.

### Architecture (Gemini Live Mode)

```
Browser Microphone (16kHz PCM)
    ↓ WebSocket
Flask-SocketIO Server
    ↓ WebSocket (PCM streaming)
Gemini Live API
    ↓ Unified bidirectional streaming
    ↓ Native ASR + LLM + TTS
Browser (streaming audio playback)
```

**Unified Streaming:** Single WebSocket connection handles both input and output audio.

### Provider Architectures

| Provider | ASR | LLM | TTS | Audio Format | Best For |
|----------|-----|-----|-----|--------------|----------|
| **DashScope** | Streaming Paraformer | Qwen (streaming) | Sambert (streaming) | PCM 16kHz | Production use, full control |
| **Gemini Standard** | Batch (Gemini 1.5 Flash) | Gemini 1.5 Flash | DashScope Sambert | WebM → PCM | Quick testing, lower latency |
| **Gemini Live** | Native (Live API) | Native (Live API) | Native (Live API) | PCM 16kHz | Lowest latency, unified API |

### Flow (DashScope Mode - Default)

1. **Page loads**
   - "Touch to Order" button appears
   - Microphone is NOT active (browser security compliant)
   - Status area is hidden

2. **User taps button**
   - Browser requests microphone permission (user gesture present)
   - Button disappears
   - Status indicator appears showing "Listening"

3. **User speaks**
   - Audio streams to server in real-time
   - Partial transcription updates (visible in debug panel)
   - Sentence-end detection triggers auto-response

4. **AI responds (Streaming)**
   - Status changes to "Thinking"
   - LLM generates response in same language (streaming)
   - TTS synthesizes audio (sentence-by-sentence streaming)
   - Status changes to "Speaking"
   - Audio plays automatically as chunks arrive

5. **Barge-in**
   - Press SPACE to interrupt AI
   - (Voice-based barge-in with speaker filtering on separate branch)

6. **Session ends**
   - User says closing remark ("thank you", "谢谢", "唔該")
   - AI responds with confirmation
   - Order persists on screen
   - "Tap for Anything" button appears
   - Tap button to add more items, or manually reset for next customer

**Latency:**
- ASR: 0.5-1 second (real-time streaming)
- First audio: ~400-600ms (target: <300ms)
- Gemini Live API typically has the lowest latency due to unified streaming

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

### Test 2: Conversation Flow

**English:**
```
[Tap "Touch to Order" button]
[Complete enrollment]
You: "Hi! What do you recommend for 2 people?"
AI: [Suggests Kung Pao Chicken and Dan Dan Noodles in English]
You: "Thank you"
AI: [Confirms order]
[Button reappears for next customer]
```

**Mandarin:**
```
[点击"Touch to Order"按钮]
[完成注册]
You: "你好！有什么推荐的吗？"
AI: [中文回复推荐菜品]
You: "谢谢"
AI: [确认订单]
[按钮重新出现，准备下一位顾客]
```

---

## 📊 Configuration

### Environment Variables

Create `.env` file:
```bash
DASHSCOPE_API_KEY=sk-your-key-here
GEMINI_API_KEY=your-gemini-key-here  # Required for gemini or gemini_live providers
PROVIDER=dashscope  # Options: dashscope, gemini, gemini_live
```

### Provider Selection

| Variable | Options | Default | Description |
|----------|---------|---------|-------------|
| `PROVIDER` | `dashscope`, `gemini`, `gemini_live` | `dashscope` | Selects which voice agent to run |

**Examples:**
```bash
# DashScope (full streaming, production-ready)
PROVIDER=dashscope python3 main.py

# Gemini Standard (batch ASR+LLM, separate TTS)
PROVIDER=gemini python3 main.py

# Gemini Live (native bidirectional audio, lowest latency)
PROVIDER=gemini_live python3 main.py
```

### Speaker Verification Threshold

Edit `static/app.js` (line ~16):
```javascript
this.speakerVerifier = new ClientSpeakerVerifier(0.75); // Default

// Lower (0.6-0.7) = more lenient, fewer false negatives
// Higher (0.8-0.9) = stricter, fewer false positives
```

### Enrollment Duration

Edit `static/app.js` (line ~18):
```javascript
this.enrollmentDuration = 2.5; // seconds

// Longer = better accuracy, worse UX
// Shorter = worse accuracy, better UX
```

### Menu Data

Edit `data/menu.json` to customize:
- Restaurant name
- Menu items (multilingual)
- Prices
- Dietary information
- Staff recommendations

---

## 🐛 Known Issues

1. **Performance - First Audio Latency** - ~400-600ms current, target <300ms
   - Connection establishment adds latency
   - See [docs/eng/CURRENT_STATUS.md](docs/eng/CURRENT_STATUS.md) for optimization plan
   - Priority fix for demo readiness

2. **No Speaker Verification** - On separate branch (`experiment/speaker-id-fingerprint`)
   - Barge-in currently SPACE key only
   - Voice-based filtering deferred until performance is optimized
   - See [docs/eng/FINAL_RECOMMENDATION.md](docs/eng/FINAL_RECOMMENDATION.md) for comparison

3. **Context Management** - Full conversation history not maintained
   - Can be improved for better multi-turn conversations

4. **No Fuzzy Item Matching** - "Chicken" doesn't match "Kung Pao Chicken"
   - Exact menu item names work best

---

## 📈 Roadmap

### Phase 5: Context & Order Management ✅ COMPLETE
- [x] Parse menu items from customer speech
- [x] Update order state in real-time
- [x] Display order updates on screen
- [x] Add/Remove/Modify order actions
- [x] Calculate subtotal, tax, and total
- [x] Show quantities and prices
- [x] Clear order on session reset
- [x] Session management with persistence ("Tap for Anything")

### Phase 6: Performance Optimization 🔄 CURRENT (Priority)
- [ ] Profile streaming pipeline (ASR → LLM → TTS)
- [ ] Implement connection pre-warming
- [ ] Reduce first audio latency to <300ms
- [ ] Test various conversation scenarios
- [ ] Handle edge cases gracefully
- [ ] Create demo script

### Phase 7: Speaker Verification 📋 DEFERRED
- [ ] Merge from `experiment/speaker-id-fingerprint` branch
- [ ] Test accuracy and tune threshold
- [ ] Optional: Add MFCC/formant features for better accuracy
- [ ] Optional: Enrollment persistence with localStorage

### Phase 8: Advanced Features 📋 PLANNED
- [ ] Multi-speaker support
- [ ] Payment integration
- [ ] Kitchen integration

### Phase 9: Production Ready 📋 PLANNED
- [ ] Deploy to cloud
- [ ] Error handling improvements
- [ ] Analytics dashboard
- [ ] Multi-restaurant support

---

## 🤝 Contributing

This is a POC project. Current focus:
1. **Performance optimization** - Reduce first audio latency to <300ms
2. Profile streaming pipeline and identify bottlenecks
3. Test conversation quality in all 3 languages
4. Test edge cases that might cause delays
5. Create demo script with fast response scenarios

See [docs/eng/CURRENT_STATUS.md](docs/eng/CURRENT_STATUS.md) for detailed optimization options.

---

## 📝 Development Notes

### Current Architecture

**Refactored Structure (2026-03-10):**
```
main.py                          # Entry point - imports provider-specific agent
config.py                        # All configuration

# Provider-specific implementations (no mixed logic)
voice_agent_dashscope.py         # Complete DashScope implementation
voice_agent_gemini_standard.py   # Gemini Standard + DashScope TTS
voice_agent_gemini_live.py       # Gemini Live API (native audio)

# Shared components (provider-agnostic)
models/
  conversation_session.py        # Session state management
routes/
  api.py                         # HTTP routes
services/
  order_service.py               # Order processing
  llm_service.py                 # LLM streaming (DashScope)
  dashscope_service.py           # DashScope TTS
  gemini_standard_service.py     # Gemini Standard API
  gemini_live_service.py         # Gemini Live API
```

**Benefits:**
- Clean separation: Each provider is isolated, no conditional branching throughout code
- Independent evolution: Modify one provider without affecting others
- Easier testing: Test each provider independently
- Clear ownership: Each file has one responsibility

**Performance Monitoring:**
- Real-time metrics tracked: LLM first token, TTS latency, total response time
- Visual performance monitor in UI
- Target: First audio <300ms

### Tech Stack

- **Backend:** Python + Flask + Flask-SocketIO
- **Frontend:** Vanilla JavaScript + WebSocket + Web Audio API
- **AI Services:**
  - Alibaba DashScope (ASR, LLM, TTS)
  - Google Gemini (Standard API for ASR+LLM, Live API for native audio)
- **Speaker Verification:** Client-side voice fingerprinting (JavaScript) - deferred
- **Data:** JSON files (menu, knowledge, config)

---

## 📞 Support

### Getting Help

1. **Run diagnostics:**
   ```bash
   python3 test_all.py
   ```

2. **Check documentation:**
   - This README (single source of truth)
   - `docs/eng/CURRENT_STATUS.md` (latest status & optimization plan) ⭐
   - `docs/eng/TEST_PLAN.md` (comprehensive test plan)
   - `CLIENT_SIDE_FINGERPRINT.md` (speaker verification - on other branch)
   - `FINAL_RECOMMENDATION.md` (speaker verification comparison - on other branch)

3. **Common issues:**
   - DNS resolution → Change DNS to 8.8.8.8
   - Missing packages → `pip install -r requirements.txt`
   - WebSocket errors → Restart server
   - No transcription → Check microphone permission
   - Slow responses → See performance optimization plan in CURRENT_STATUS.md

---

## 📄 License

MIT License - See LICENSE file for details

---

## 🎯 Quick Reference

### Start Server

**DashScope (default - recommended for production):**
```bash
python3 main.py
# or: PROVIDER=dashscope python3 main.py
```

**Gemini Standard API:**
```bash
PROVIDER=gemini python3 main.py
```

**Gemini Live API:**
```bash
PROVIDER=gemini_live python3 main.py
```

### Run Tests
```bash
python3 test_all.py          # Complete system check
python3 test_network.py      # Network diagnostics only
```

### Install Dependencies
```bash
pip install -r requirements.txt
```

### Access Application
```
http://localhost:5002
```

### Debug Panel
```
Click 🐛 button (bottom right) to see:
- Session ID
- Table name
- Transcription
- AI response
- Performance metrics (LLM first token, TTS latency)
```

### Touch to Order
```
Tap the large blue button to start ordering
- Requests microphone permission
- Starts listening immediately
- Enables natural conversation
```

### Interrupt AI
```
Press SPACE while AI is talking to interrupt
- (Voice-based filtering with speaker verification on separate branch)
```

### End Session
```
Say closing remarks to end session:
- English: "thank you", "thanks", "that's all"
- Mandarin: "谢谢", "好的", "就这些"
- Cantonese: "唔該", "多謝", "得啦"

Button will reappear for next customer
```

---

**Last Updated:** 2026-03-10
**Version:** POC v0.8 (Multi-Provider Architecture)
**Status:** Provider separation complete - DashScope, Gemini Standard, and Gemini Live API supported
**Branch:** `feature/gemini-live-api`
**Next:** Testing and validation of all provider modes
