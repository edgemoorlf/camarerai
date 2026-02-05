# CamareraI - AI Voice Agent for Restaurants

**Status:** POC - Always-Listening Voice Agent
**Last Updated:** 2026-02-04

---

## 🎯 Current Implementation

**Active File:** `voice_agent.py`
**Status:** ✅ Ready to test
**Architecture:** WebSocket-based streaming ASR with always-listening mode

### What Works ✅
- ✅ **Touch to Order button** - Large button to start ordering (browser security compliant)
- ✅ **Always-listening mode** - Microphone streams continuously after button tap
- ✅ **Natural conversation** - Speak naturally, AI responds when you finish
- ✅ **Language matching** - AI responds in your language (Chinese/English)
- ✅ **Barge-in support** - Interrupt AI by speaking or pressing SPACE
- ✅ **Minimal UI** - Clean status indicator + order summary only
- ✅ **Real-time voice transcription** (streaming)
- ✅ **LLM conversation** (English, Mandarin, Cantonese)
- ✅ **Text-to-speech responses**
- ✅ **Session management**
- ✅ **Closing remark detection** - Detects "thank you", "谢谢", "唔該" and resets
- ✅ **Session boundaries** - Clean reset between customers
- ✅ **Order parsing** - Extracts items from conversation in any language
- ✅ **Order display** - Shows items with quantities and prices
- ✅ **Order calculations** - Automatic subtotal, tax (9%), and total
- ✅ **Order modifications** - Add, remove, or change quantities
- ✅ **Real-time updates** - Order panel updates as items are added

### What's Not Implemented Yet ⬜
- ❌ Context management (full conversation history)
- ❌ Error handling for invalid menu items
- ❌ Order confirmation before sending to kitchen
- ❌ Fuzzy item matching (e.g., "chicken" → "Kung Pao Chicken")
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

Server also available on network:
- Local: http://127.0.0.1:5002
- Network: http://192.168.1.139:5002

### 5. Test Touch to Order Flow

1. **Page loads** - "Touch to Order" button appears
2. **Tap button** - Browser requests microphone permission
3. **Grant permission** - Button disappears, status shows "Listening"
4. **Order items**: "I'd like the Kung Pao Chicken"
5. **Watch order panel** - Item appears with price
6. **Modify order**: "Actually, make that two"
7. **Watch update** - Quantity changes to x2, total updates
8. **Continue ordering**: "And the Dan Dan Noodles"
9. **Watch panel** - New item added, totals recalculate
10. **End session**: Say "Thank you" or "谢谢" or "唔該"
11. **AI confirms** - Responds with confirmation
12. **Session resets** - Order clears, button reappears for next customer

**Interrupt anytime:** Press SPACE or start speaking to interrupt AI

**Debug Panel:** Click 🐛 button (bottom right) to see transcription and responses

---

## 📁 Project Structure

### Core Files (Active)

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
├── app.js                   # Always-listening WebSocket client
└── style.css                # Minimal UI styling

templates/
└── index.html               # Minimal UI (status + order summary)
```

### Documentation

```
README.md                    # This file - single source of truth
CLAUDE.md                    # AI assistant guidelines
docs/
├── PLAN.md                  # Overall project plan and vision
├── eng/
│   ├── IMPLEMENTATION_PLAN.md     # Technical implementation plan
│   └── IMPLEMENTATION_STATUS.md   # Current implementation status
└── prd/
    └── PRODUCT_DESIGN.md    # Product design decisions
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

### Issue 4: Import Errors

**Symptom:**
```
ModuleNotFoundError: No module named 'flask_socketio'
```

**Fix:**
```bash
pip install flask-socketio python-socketio eventlet dashscope flask python-dotenv
```

---

## 🎤 How It Works

### Architecture

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
    ↓ Generate response
DashScope TTS (Sambert)
    ↓ Synthesize speech
Browser (auto-play audio)
```

### Flow

1. **Page loads**
   - "Touch to Order" button appears
   - Microphone is NOT active (browser security compliant)
   - Status area is hidden

2. **User taps button**
   - Browser requests microphone permission (user gesture present)
   - Button disappears
   - Status indicator appears showing "Listening"
   - Continuous audio streaming begins

3. **User speaks**
   - Audio streams to server in real-time
   - Partial transcription updates (visible in debug panel)
   - Sentence-end detection triggers auto-response

4. **AI responds**
   - Status changes to "Thinking"
   - LLM generates response in same language
   - TTS synthesizes audio
   - Status changes to "Speaking"
   - Audio plays automatically

5. **Barge-in support**
   - User can interrupt by speaking
   - Or press SPACE key
   - Audio stops immediately
   - Returns to listening mode

6. **Session ends**
   - User says closing remark ("thank you", "谢谢", "唔該")
   - AI responds with confirmation
   - After AI finishes speaking:
     - Microphone stops
     - Status area hides
     - "Touch to Order" button reappears
   - Ready for next customer

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
[Tap "Touch to Order" button]
You: "Hi! What do you recommend for 2 people?"
AI: [Suggests Kung Pao Chicken and Dan Dan Noodles in English]
You: "Thank you"
AI: [Confirms order]
[Button reappears for next customer]
```

**Mandarin:**
```
[点击"Touch to Order"按钮]
You: "你好！有什么推荐的吗？"
AI: [中文回复推荐菜品]
You: "谢谢"
AI: [确认订单]
[按钮重新出现，准备下一位顾客]
```

**Cantonese:**
```
[撳"Touch to Order"掣]
You: "你好！有咩推薦？"
AI: [粵語回覆推薦菜式]
You: "唔該"
AI: [確認訂單]
[掣重新出現，準備下一位客人]
```

### Test 4: Barge-in

1. While AI is speaking, start talking
2. AI should stop immediately
3. Or press SPACE to interrupt
4. Status should return to "Listening"

### Test 5: Closing Remarks & Session Reset

**English closing remarks:**
- "Thank you", "Thanks", "That's all", "Go ahead", "Send the order"

**Mandarin closing remarks:**
- "谢谢", "好的", "可以了", "就这些", "下单吧"

**Cantonese closing remarks:**
- "唔該", "多謝", "得啦", "可以啦", "落單啦"

**Expected behavior:**
1. Say any closing remark
2. AI responds with confirmation
3. After AI finishes speaking:
   - Microphone stops
   - Status indicator disappears
   - "Touch to Order" button reappears
4. Ready for next customer session

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
   - **Fix:** Allow microphone in browser settings

3. **Order Parsing** - Not yet implemented
   - **Status:** Items not extracted from conversation yet

4. **Order Display** - Order summary panel not populated
   - **Status:** UI ready but backend not sending order updates

5. **Voice Cloning** - Not available in basic DashScope SDK
   - **Status:** Planned for future implementation

---

## 📈 Roadmap

### Phase 1: Core Infrastructure ✅ COMPLETE
- [x] DashScope API client wrapper
- [x] Flask server with WebSocket support
- [x] Streaming ASR with sentence accumulation
- [x] Session management with conversation history
- [x] TTS synthesis and playback

### Phase 2-4: UI Redesign + Always-Listening + Barge-in ✅ COMPLETE
- [x] Remove chat interface
- [x] Minimal status indicator
- [x] Elegant order summary panel
- [x] High-end tablet aesthetic
- [x] Touch to Order button (browser security compliant)
- [x] Continuous audio streaming
- [x] Auto-respond on sentence end
- [x] Barge-in (interrupt TTS)
- [x] Language matching
- [x] Closing remark detection (English, Mandarin, Cantonese)
- [x] Session reset between customers

### Phase 5: Context & Order Management 🔄 IN PROGRESS
- [x] Parse menu items from customer speech
- [x] Update order state in real-time
- [x] Display order updates on screen
- [x] Add/Remove/Modify order actions
- [x] Calculate subtotal, tax, and total
- [x] Show quantities and prices
- [x] Clear order on session reset
- [ ] Maintain full conversation context
- [ ] Handle order modifications ("change that to two", "remove the soup")
- [ ] Error handling for invalid items
- [ ] Fuzzy item matching

### Phase 6: Polish & Demo 📋 PLANNED
- [ ] Fine-tune response latency
- [ ] Improve sentence-end detection
- [ ] Test various conversation scenarios
- [ ] Handle edge cases gracefully
- [ ] Create demo script

### Phase 7: Advanced Features 📋 PLANNED
- [ ] Voice cloning for staff
- [ ] Speaker identification
- [ ] Multi-speaker support
- [ ] Payment integration

### Phase 8: Production Ready 📋 PLANNED
- [ ] Deploy to cloud
- [ ] Performance optimization
- [ ] Error handling
- [ ] Analytics dashboard
- [ ] Multi-restaurant support

---

## 🤝 Contributing

This is a POC project. Current focus:
1. Implement order parsing from conversation
2. Populate order summary panel with real-time updates
3. Improve context management
4. Test conversation quality in all 3 languages
5. Improve user experience

---

## 📝 Development Notes

### Why Touch to Order Button?

**Browser Security Requirement:**
- Browsers require explicit user interaction before accessing microphone
- Auto-start microphone violates security policies
- User gesture (tap/click) required for permission request

**Solution:**
- Large, prominent "Touch to Order" button
- Appears on page load
- Requests microphone permission on tap
- Disappears after activation
- Reappears after session ends

### Why Closing Remark Detection?

**Clear Session Boundaries:**
- Explicit start with button tap
- Automatic end on closing remarks
- Clean reset between customers
- No manual "stop" button needed

**Multilingual Support:**
- Detects closing remarks in English, Mandarin, Cantonese
- Natural conversation flow in all languages
- Automatic session management

### Why Always-Listening?

**Old approach (push-to-talk):**
- Click button → Record → Release → Process
- Awkward interaction
- Not natural conversation flow

**New approach (always-listening after button tap):**
- Continuous listening during session
- Natural conversation
- Auto-respond on sentence end
- Barge-in support
- Better UX

### Why Streaming ASR?

**Batch approach:**
- Record → Upload → Transcribe → Display
- 3-5 second latency
- Required public URL (doesn't work on localhost)

**Streaming approach:**
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
   - `docs/eng/IMPLEMENTATION_STATUS.md` (current status)
   - `docs/prd/PRODUCT_DESIGN.md` (design decisions)

3. **Common issues:**
   - DNS resolution → Change DNS to 8.8.8.8
   - Missing packages → `pip install flask-socketio python-socketio eventlet dashscope flask python-dotenv`
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
pip install flask-socketio python-socketio eventlet dashscope flask python-dotenv
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
```

### Touch to Order
```
Tap the large blue button to start ordering
- Requests microphone permission
- Starts voice recognition
- Enables natural conversation
```

### Interrupt AI
```
Press SPACE or start speaking while AI is talking
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

**Last Updated:** 2026-02-04
**Version:** POC v0.5 (Order Management)
**Status:** Ready for testing - Phase 5 mostly complete, order parsing and display working
